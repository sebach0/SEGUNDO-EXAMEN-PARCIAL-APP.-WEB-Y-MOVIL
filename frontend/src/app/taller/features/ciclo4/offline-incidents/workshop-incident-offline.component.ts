import { Component, inject, OnInit, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Subscription } from 'rxjs';
import { NetworkService } from '../../../../core/services/network.service';
import { OfflineQueueService } from '../../../../core/services/offline-queue.service';
import { SyncService } from '../../../../core/services/sync.service';
import type {
  WorkshopActionType,
  IncidentStatus,
  OfflineEvent,
} from '../../../../core/models/ciclo4.models';

/**
 * WorkshopIncidentOfflineComponent — Ciclo 4 (CU41) — Opción A (flujo real)
 *
 * Permite al taller registrar o actualizar el estado de una SOLICITUD DE
 * EMERGENCIA incluso cuando la web está offline.
 *
 * Flujo unificado:
 * 1. Si está ONLINE  → llama POST /api/app/taller/emergencias/sync-web.
 * 2. Si está OFFLINE → guarda en IndexedDB con estado 'pendiente'.
 * 3. Al recuperar conexión, SyncService sincroniza automáticamente con el
 *    endpoint real de solicitudes (no con el flujo ciclo4/incidentes).
 */
@Component({
  selector: 'app-workshop-incident-offline',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './workshop-incident-offline.component.html',
  styleUrl: './workshop-incident-offline.component.scss',
})
export class WorkshopIncidentOfflineComponent implements OnInit, OnDestroy {
  private readonly network = inject(NetworkService);
  private readonly queue = inject(OfflineQueueService);
  private readonly syncSvc = inject(SyncService);

  // ── Estado del formulario ─────────────────────────────────────────────────

  solicitudId: number | null = null;
  accion: WorkshopActionType = 'OBSERVACION';
  estadoNuevo: IncidentStatus | '' = '';
  comentario = '';
  fechaLocal = new Date().toISOString().slice(0, 16);

  // ── Estado UI ─────────────────────────────────────────────────────────────

  isOnline = true;
  busy = false;
  successMsg: string | null = null;
  error: string | null = null;

  readonly acciones: { value: WorkshopActionType; label: string }[] = [
    { value: 'CAMBIAR_ESTADO', label: 'Cambiar estado' },
    { value: 'OBSERVACION', label: 'Registrar observación' },
    { value: 'ACEPTAR', label: 'Registrar aceptación (offline)' },
    { value: 'RECHAZAR', label: 'Registrar rechazo (offline)' },
  ];

  readonly estados: { value: IncidentStatus; label: string }[] = [
    { value: 'BUSCANDO_TALLER', label: 'Buscando taller' },
    { value: 'TALLER_ASIGNADO', label: 'Taller asignado' },
    { value: 'EN_CAMINO', label: 'En camino' },
    { value: 'EN_ATENCION', label: 'En atención' },
    { value: 'FINALIZADO', label: 'Finalizado' },
    { value: 'CANCELADO', label: 'Cancelado' },
  ];

  private sub?: Subscription;

  ngOnInit(): void {
    this.isOnline = this.network.getCurrentStatus();
    this.sub = this.network.isOnline$().subscribe((status) => {
      this.isOnline = status;
    });
  }

  ngOnDestroy(): void {
    this.sub?.unsubscribe();
  }

  // ── Validaciones ──────────────────────────────────────────────────────────

  esFormularioValido(): boolean {
    if (!this.solicitudId || this.solicitudId < 1) return false;
    if (this.accion === 'CAMBIAR_ESTADO' && !this.estadoNuevo) return false;
    if (this.accion === 'RECHAZAR' && this.comentario.trim().length < 3) return false;
    return true;
  }

  requiereEstadoNuevo(): boolean {
    return this.accion === 'CAMBIAR_ESTADO';
  }

  requiereComentario(): boolean {
    return this.accion === 'RECHAZAR';
  }

  // ── Envío ─────────────────────────────────────────────────────────────────

  async onSubmit(): Promise<void> {
    this.error = null;
    this.successMsg = null;

    if (!this.esFormularioValido()) {
      this.error = this._buildValidationError();
      return;
    }

    this.busy = true;

    const clientUuid = this.queue.generateClientUuid();
    const payload: Record<string, unknown> = {
      accion: this.accion,
      comentario: this.comentario.trim() || null,
    };
    if (this.estadoNuevo) payload['estado_nuevo'] = this.estadoNuevo;

    // El evento usa solicitud_id (flujo real, Opción A)
    const event: Omit<OfflineEvent, '_intentos' | '_ultimo_error'> = {
      client_uuid: clientUuid,
      incidente_id: 0,            // legacy — no usado en flujo real
      solicitud_id: this.solicitudId!,
      tipo_evento: this._tipoEvento(),
      payload,
      registrado_local_en: new Date(this.fechaLocal).toISOString(),
      _estado_local: 'pendiente',
      _entidad: 'solicitud_evento',
    };

    if (this.isOnline) {
      await this._enviarOnline(event, clientUuid);
    } else {
      await this._guardarOffline(event);
    }

    this.busy = false;
  }

  private async _enviarOnline(
    event: Omit<OfflineEvent, '_intentos' | '_ultimo_error'>,
    clientUuid: string,
  ): Promise<void> {
    await this.queue.addOfflineEvent(event);

    this.syncSvc
      .syncSolicitudWebEvents([{ ...event, _intentos: 0, _ultimo_error: null }])
      .subscribe({
        next: async (result) => {
          const item = result.detalle.find((d) => d.client_uuid === clientUuid);
          if (item?.sincronizado) {
            await this.queue.markAsSynced(clientUuid);
            this.successMsg = '✓ Evento sincronizado con el flujo real de solicitudes.';
            this._resetForm();
          } else {
            await this.queue.markAsError(clientUuid, item?.error ?? 'Error en backend');
            this.error = `El backend no pudo procesar el evento: ${item?.error ?? 'Error desconocido'}`;
          }
        },
        error: async (err) => {
          await this.queue.markAsError(clientUuid, err?.message ?? 'Error de red');
          this.error =
            'No se pudo enviar al backend. El evento fue guardado localmente y se sincronizará al recuperar conexión.';
        },
      });
  }

  private async _guardarOffline(
    event: Omit<OfflineEvent, '_intentos' | '_ultimo_error'>,
  ): Promise<void> {
    try {
      await this.queue.addOfflineEvent(event);
      this.successMsg =
        'Registro guardado localmente. Se sincronizará contra el flujo real al recuperar conexión.';
      this._resetForm();
    } catch {
      this.error = 'No se pudo guardar el evento localmente.';
    }
  }

  private _tipoEvento(): string {
    const map: Record<WorkshopActionType, string> = {
      ACEPTAR: 'TALLER_ACEPTO',
      RECHAZAR: 'TALLER_RECHAZO',
      CAMBIAR_ESTADO: 'ESTADO_CAMBIADO',
      OBSERVACION: 'OBSERVACION',
    };
    return map[this.accion];
  }

  private _buildValidationError(): string {
    if (!this.solicitudId || this.solicitudId < 1) return 'El ID de la solicitud es obligatorio.';
    if (this.accion === 'CAMBIAR_ESTADO' && !this.estadoNuevo)
      return 'Debes seleccionar el nuevo estado.';
    if (this.accion === 'RECHAZAR' && this.comentario.trim().length < 3)
      return 'El motivo de rechazo debe tener al menos 3 caracteres.';
    return 'Formulario inválido.';
  }

  private _resetForm(): void {
    this.solicitudId = null;
    this.accion = 'OBSERVACION';
    this.estadoNuevo = '';
    this.comentario = '';
    this.fechaLocal = new Date().toISOString().slice(0, 16);
  }
}
