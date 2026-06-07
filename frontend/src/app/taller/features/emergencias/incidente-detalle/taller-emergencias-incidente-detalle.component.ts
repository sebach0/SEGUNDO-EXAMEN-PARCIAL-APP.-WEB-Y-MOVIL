import { Component, inject, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ActivatedRoute, Router, RouterLink } from '@angular/router';
import { forkJoin } from 'rxjs';
import { TallerEmergenciasApiService } from '../../../../core/services/taller-emergencias-api.service';
import { TallerApiService } from '../../../../core/services/taller-api.service';
import { TallerAuthService } from '../../../../core/services/taller-auth.service';
import type {
  AsignacionTecnicoDto,
  SolicitudBandejaDetalleDto,
  SolicitudEvidenciaTallerDto,
} from '../../../../core/models/taller-emergencias.models';
import type { TecnicoPortalDto } from '../../../../core/models/taller-api.models';

@Component({
  selector: 'app-taller-emergencias-incidente-detalle',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterLink],
  templateUrl: './taller-emergencias-incidente-detalle.component.html',
  styleUrl: './taller-emergencias-incidente-detalle.component.scss',
})
export class TallerEmergenciasIncidenteDetalleComponent implements OnInit {
  private readonly api = inject(TallerEmergenciasApiService);
  private readonly tallerApi = inject(TallerApiService);
  private readonly auth = inject(TallerAuthService);
  private readonly route = inject(ActivatedRoute);
  private readonly router = inject(Router);

  bandejaId: number | null = null;
  detalle: SolicitudBandejaDetalleDto | null = null;
  loading = true;
  error: string | null = null;
  busy = false;

  successMsg: string | null = null;

  tecnicos: TecnicoPortalDto[] = [];
  asignaciones: AsignacionTecnicoDto[] = [];
  loadingAsignData = false;
  selectedTecnicoId: number | null = null;
  observacionAsignacion = '';
  /** ETA en minutos (opcional) al asignar técnico. */
  tiempoEstimadoMin: number | null = null;

  modalRechazar = false;
  motivoRechazo = '';

  ngOnInit(): void {
    this.route.paramMap.subscribe((p) => {
      const id = Number(p.get('bandejaId'));
      this.bandejaId = Number.isFinite(id) && id > 0 ? id : null;
      if (this.bandejaId) this.load();
      else {
        this.loading = false;
        this.error = 'Identificador de bandeja inválido.';
      }
    });
  }

  load(): void {
    if (!this.bandejaId) return;
    this.loading = true;
    this.error = null;
    this.successMsg = null;
    this.tecnicos = [];
    this.asignaciones = [];
    this.selectedTecnicoId = null;
    this.observacionAsignacion = '';
    this.tiempoEstimadoMin = null;
    this.api.getBandejaDetalle(this.bandejaId).subscribe({
      next: (d) => {
        this.detalle = d;
        this.loading = false;
        this.cargarDatosAsignacion(d);
      },
      error: (err) => {
        this.loading = false;
        this.detalle = null;
        this.error = this.msg(err, 'No se pudo cargar el detalle del incidente.');
      },
    });
  }

  private cargarDatosAsignacion(d: SolicitudBandejaDetalleDto): void {
    if (!this.debeMostrarBloqueAsignacion(d)) {
      this.loadingAsignData = false;
      return;
    }
    this.loadingAsignData = true;
    forkJoin({
      tecnicos: this.tallerApi.listTecnicos(),
      asignaciones: this.api.listarAsignacionesTecnico(d.solicitud_id),
    }).subscribe({
      next: ({ tecnicos, asignaciones }) => {
        this.tecnicos = tecnicos;
        this.asignaciones = [...asignaciones].sort(
          (a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime(),
        );
        const ultimo = this.asignaciones.find((r) => r.estado === 'ASIGNADO');
        this.selectedTecnicoId = ultimo?.tecnico_id ?? null;
        this.loadingAsignData = false;
        if (
          d.estado_solicitud === 'TALLER_ASIGNADO' &&
          !this.asignaciones.some((r) => r.estado === 'ASIGNADO') &&
          this.puedeAsignarTecnicoPermiso()
        ) {
          this.intentarAsignacionAutomatica(d.solicitud_id);
        }
      },
      error: (err) => {
        this.loadingAsignData = false;
        this.error = this.msg(err, 'No se pudieron cargar técnicos o el historial de asignaciones.');
      },
    });
  }

  /** Tras que el cliente elige la cotización del taller: asignar técnico. */
  debeMostrarBloqueAsignacion(d: SolicitudBandejaDetalleDto | null): boolean {
    if (!d || d.estado_bandeja !== 'ACEPTADA') return false;
    return d.estado_solicitud === 'TALLER_ASIGNADO' || d.estado_solicitud === 'TECNICO_ASIGNADO';
  }

  tecnicosActivos(): TecnicoPortalDto[] {
    return this.tecnicos.filter((t) => t.estado === 'ACTIVO');
  }

  tecnicosDisponibles(): TecnicoPortalDto[] {
    return this.tecnicosActivos().filter((t) => {
      const d = (t.disponibilidad ?? 'DISPONIBLE').trim().toLowerCase();
      return d !== 'ocupado' && d !== 'no_disponible' && d !== 'ausente' && d !== 'no';
    });
  }

  tecnicoDisponibilidadLabel(t: TecnicoPortalDto): string {
    const d = (t.disponibilidad ?? 'DISPONIBLE').trim().toUpperCase();
    return d === 'OCUPADO' ? 'Ocupado' : 'Disponible';
  }

  puedeAsignarTecnico(): boolean {
    if (!this.puedeAsignarTecnicoPermiso()) return false;
    const d = this.detalle;
    return !!d && this.debeMostrarBloqueAsignacion(d);
  }

  private puedeAsignarTecnicoPermiso(): boolean {
    const p = this.auth.getMe()?.permisos;
    if (!p?.length) return true;
    return p.includes('tecnicos:asignar');
  }

  externalMapLink(): string | null {
    const d = this.detalle;
    if (!d?.latitud || !d?.longitud) return null;
    return `https://www.openstreetmap.org/?mlat=${d.latitud}&mlon=${d.longitud}#map=16/${d.latitud}/${d.longitud}`;
  }

  /** `ai_payload` v1: hay algo útil para mostrar (resumen, clasificación, etc.). */
  aiTieneContenido(d: SolicitudBandejaDetalleDto | null): boolean {
    if (!d?.ai_payload || typeof d.ai_payload !== 'object') return false;
    const p = d.ai_payload as Record<string, unknown>;
    const rs = p['resumen_estructurado'];
    if (rs && typeof rs === 'object' && 'resumen' in (rs as object)) {
      const t = String((rs as { resumen?: unknown }).resumen ?? '').trim();
      if (t.length > 0) return true;
    }
    if (p['clasificacion'] || p['prioridad']) return true;
    if (Array.isArray(p['hallazgos_vision']) && (p['hallazgos_vision'] as unknown[]).length) return true;
    const tr = p['transcripcion_audio'];
    if (typeof tr === 'string' && tr.trim().length > 0) return true;
    return false;
  }

  aiResumenTexto(d: SolicitudBandejaDetalleDto | null): string {
    if (!d?.ai_payload) return '';
    const p = d.ai_payload as Record<string, unknown>;
    const rs = p['resumen_estructurado'];
    if (rs && typeof rs === 'object' && 'resumen' in (rs as object)) {
      return String((rs as { resumen?: unknown }).resumen ?? '');
    }
    return '';
  }

  aiCategoriaUi(d: SolicitudBandejaDetalleDto | null): string | null {
    const c = this.aiCategoriaRaw(d);
    if (!c) return null;
    const m: Record<string, string> = {
      BATERIA: 'Batería',
      LLANTA: 'Llanta / pinchazo',
      CHOQUE: 'Choque / colisión',
      MOTOR: 'Motor',
      OTROS: 'Otros',
    };
    return m[c] ?? c;
  }

  private aiCategoriaRaw(d: SolicitudBandejaDetalleDto | null): string | null {
    if (!d?.ai_payload || typeof d.ai_payload !== 'object') return null;
    const c = (d.ai_payload as Record<string, unknown>)['clasificacion'];
    if (!c || typeof c !== 'object') return null;
    const cat = (c as { categoria?: unknown }).categoria;
    return typeof cat === 'string' ? cat : null;
  }

  aiConfianzaClasificacion(d: SolicitudBandejaDetalleDto | null): number | null {
    if (!d?.ai_payload || typeof d.ai_payload !== 'object') return null;
    const c = (d.ai_payload as Record<string, unknown>)['clasificacion'];
    if (!c || typeof c !== 'object') return null;
    const n = (c as { confianza?: unknown }).confianza;
    return typeof n === 'number' && Number.isFinite(n) ? n : null;
  }

  aiPrioridadUi(d: SolicitudBandejaDetalleDto | null): string | null {
    if (!d?.ai_payload || typeof d.ai_payload !== 'object') return null;
    const pr = (d.ai_payload as Record<string, unknown>)['prioridad'];
    if (!pr || typeof pr !== 'object') return null;
    const n = (pr as { nivel_prioridad?: unknown }).nivel_prioridad;
    if (typeof n !== 'string') return null;
    const m: Record<string, string> = {
      ALTA: 'Alta',
      MEDIA: 'Media',
      BAJA: 'Baja',
      REVISION_MANUAL: 'Revisión manual',
    };
    return m[n] ?? n;
  }

  aiPrioridadMotivos(d: SolicitudBandejaDetalleDto | null): string[] {
    if (!d?.ai_payload || typeof d.ai_payload !== 'object') return [];
    const pr = (d.ai_payload as Record<string, unknown>)['prioridad'];
    if (!pr || typeof pr !== 'object') return [];
    const m = (pr as { motivo?: unknown }).motivo;
    if (!Array.isArray(m)) return [];
    return m.filter((x): x is string => typeof x === 'string');
  }

  aiHallazgosVision(d: SolicitudBandejaDetalleDto | null): string[] {
    if (!d?.ai_payload || typeof d.ai_payload !== 'object') return [];
    const h = (d.ai_payload as Record<string, unknown>)['hallazgos_vision'];
    if (!Array.isArray(h)) return [];
    return h.map((x) => String(x));
  }

  /** Lista segura (evita undefined si el backend aún no envía el campo). */
  evidenciasSafe(d: SolicitudBandejaDetalleDto | null): SolicitudEvidenciaTallerDto[] {
    if (!d?.evidencias?.length) return [];
    return d.evidencias;
  }

  /**
   * Las URLs se guardan con el host del backend; en el navegador se sirve por el mismo sitio bajo /api/...
   */
  evidenciaSrc(url: string): string {
    if (!url) return '';
    if (url.startsWith('/')) return url;
    try {
      const u = new URL(url);
      if (u.pathname.includes('/media/evidencias/')) {
        return u.pathname + (u.search || '');
      }
    } catch {
      /* no absoluta */
    }
    return url;
  }

  openRechazar(): void {
    this.motivoRechazo = '';
    this.modalRechazar = true;
  }

  closeModals(): void {
    this.modalRechazar = false;
  }

  irACotizar(): void {
    const sid = this.detalle?.solicitud_id;
    if (!sid) return;
    void this.router.navigate(['/taller/panel/cotizaciones/solicitud', sid]);
  }

  confirmRechazar(): void {
    const m = this.motivoRechazo.trim();
    if (m.length < 3) {
      this.error = 'El motivo de rechazo debe tener al menos 3 caracteres.';
      return;
    }
    if (!this.bandejaId) return;
    this.busy = true;
    this.api.rechazarBandeja(this.bandejaId, { motivo_rechazo: m }).subscribe({
      next: () => {
        this.busy = false;
        this.closeModals();
        void this.router.navigate(['/taller/panel/emergencias/solicitudes'], { queryParams: { ok: 'rechazada' } });
      },
      error: (err) => {
        this.busy = false;
        this.error = this.msg(err, 'No se pudo rechazar la solicitud.');
      },
    });
  }

  confirmarAsignarTecnico(): void {
    const d = this.detalle;
    if (!d || this.selectedTecnicoId == null || this.selectedTecnicoId < 1) {
      this.error = 'Seleccioná un técnico disponible.';
      return;
    }
    const obs = this.observacionAsignacion.trim();
    this.busy = true;
    this.error = null;
    this.api
      .asignarTecnico(d.solicitud_id, {
        tecnico_id: this.selectedTecnicoId,
        observacion: obs.length ? obs : null,
        tiempo_estimado_min: this.tiempoEstimadoMin != null && this.tiempoEstimadoMin > 0 ? this.tiempoEstimadoMin : null,
      })
      .subscribe({
        next: () => {
          this.busy = false;
          this.successMsg = 'Técnico asignado correctamente.';
          this.load();
        },
        error: (err) => {
          this.busy = false;
          this.error = this.msg(err, 'No se pudo asignar el técnico.');
        },
      });
  }

  nombreTecnico(id: number): string {
    const t = this.tecnicos.find((x) => x.id === id);
    return t ? `${t.nombres} ${t.apellidos}`.trim() : `ID ${id}`;
  }

  puedeOperarBandeja(): boolean {
    const d = this.detalle;
    return !!d && d.estado_bandeja === 'PENDIENTE';
  }

  puedeRechazar(): boolean {
    const p = this.auth.getMe()?.permisos;
    if (!p?.length) return true;
    return p.includes('solicitudes_taller:rechazar');
  }

  intentarAsignacionAutomatica(solicitudId: number): void {
    this.api.asignarTecnicoAutomatico(solicitudId).subscribe({
      next: () => {
        this.successMsg = 'Técnico asignado automáticamente (primer disponible del taller).';
        this.load();
      },
      error: () => {
        /* Sin técnicos libres: el responsable puede asignar manualmente. */
      },
    });
  }

  private msg(err: { error?: { detail?: unknown } }, fallback: string): string {
    const d = err?.error?.detail;
    if (typeof d === 'string') return d;
    if (Array.isArray(d) && d.length && typeof d[0] === 'object' && d[0] !== null && 'msg' in d[0]) {
      return String((d[0] as { msg: string }).msg);
    }
    return fallback;
  }
}
