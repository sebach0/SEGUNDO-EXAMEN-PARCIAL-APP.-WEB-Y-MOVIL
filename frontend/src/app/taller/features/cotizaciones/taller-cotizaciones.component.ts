import {
  Component,
  inject,
  OnInit,
  OnDestroy,
  signal,
  ChangeDetectionStrategy,
  ChangeDetectorRef,
} from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule, ReactiveFormsModule, FormBuilder, FormArray, Validators } from '@angular/forms';
import { ActivatedRoute, RouterLink } from '@angular/router';
import { Subscription } from 'rxjs';
import { CotizacionService } from '../../../core/services/cotizacion.service';
import type { Cotizacion, CotizacionContexto, CotizacionCreateIn, CotizacionItemIn } from '../../../core/models/cotizacion.models';
import { OsmMapPickerComponent } from '../../../shared/components/osm-map-picker/osm-map-picker.component';
import {
  ETA_LLEGADA_MAX_MIN,
  ETA_REPARACION_MAX_MIN,
  formatEtaMinutos,
  minutosFromHorasMin,
  minutosToHorasMin,
} from '../../../core/utils/eta-format.util';

@Component({
  selector: 'app-taller-cotizaciones',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [CommonModule, FormsModule, ReactiveFormsModule, RouterLink, OsmMapPickerComponent],
  templateUrl: './taller-cotizaciones.component.html',
  styleUrl: './taller-cotizaciones.component.scss',
})
export class TallerCotizacionesComponent implements OnInit, OnDestroy {
  private readonly cotSvc = inject(CotizacionService);
  private readonly route  = inject(ActivatedRoute);
  private readonly fb     = inject(FormBuilder);
  private readonly cdr    = inject(ChangeDetectorRef);
  private formSub?: Subscription;

  solicitudId = signal(0);
  cotizaciones = signal<Cotizacion[]>([]);
  contexto = signal<CotizacionContexto | null>(null);
  loading  = signal(true);
  saving   = signal(false);
  msg      = signal<{ tipo: 'ok' | 'error'; texto: string } | null>(null);
  mostrarFormulario = signal(false);

  form = this.fb.group({
    descripcion_danio:  ['', [Validators.required, Validators.minLength(5)]],
    detalle_servicio:   ['', [Validators.required, Validators.minLength(5)]],
    monto_total:        [null as number | null, [Validators.required, Validators.min(1)]],
    llegada_horas:      [0, [Validators.min(0)]],
    llegada_minutos:    [0, [Validators.min(0), Validators.max(59)]],
    reparacion_horas:   [0, [Validators.min(0)]],
    reparacion_minutos: [0, [Validators.min(0), Validators.max(59)]],
    incluye_grua:       [false],
    comentarios:        [null as string | null],
    items: this.fb.array([]),
  });

  get items(): FormArray {
    return this.form.get('items') as FormArray;
  }

  ngOnInit(): void {
    const id = Number(this.route.snapshot.paramMap.get('solicitudId') ?? 0);
    this.solicitudId.set(id);
    this.formSub = this.form.statusChanges.subscribe(() => this.cdr.markForCheck());
    this.cargar();
  }

  ngOnDestroy(): void {
    this.formSub?.unsubscribe();
  }

  private patchDuracion(prefix: 'llegada' | 'reparacion', totalMin: number): void {
    const { horas, minutos } = minutosToHorasMin(totalMin);
    this.form.patchValue({
      [`${prefix}_horas`]: horas,
      [`${prefix}_minutos`]: minutos,
    });
  }

  private duracionTotalMinutos(prefix: 'llegada' | 'reparacion'): number {
    const h = Number(this.form.value[`${prefix}_horas`] ?? 0);
    const m = Number(this.form.value[`${prefix}_minutos`] ?? 0);
    return minutosFromHorasMin(h, m);
  }

  private cargar(): void {
    const id = this.solicitudId();
    if (!id) { this.loading.set(false); return; }

    this.cotSvc.contextoOferta(id).subscribe({
      next: (ctx) => {
        this.contexto.set(ctx);
        if (ctx.servicios_disponibles.length && !this.form.value.detalle_servicio) {
          const nombres = ctx.servicios_disponibles.map((s) => s.nombre).join(', ');
          this.form.patchValue({ detalle_servicio: `Servicios: ${nombres}.` });
        }
        if (ctx.tiene_grua) {
          this.form.patchValue({ incluye_grua: true });
        }
        if (
          ctx.eta_sugerida_min &&
          ctx.eta_sugerida_min <= ETA_LLEGADA_MAX_MIN &&
          this.duracionTotalMinutos('llegada') === 0
        ) {
          this.patchDuracion('llegada', ctx.eta_sugerida_min);
        }
        this.cdr.markForCheck();
      },
    });

    this.cotSvc.listar(id).subscribe({
      next: (list) => { this.cotizaciones.set(list); this.loading.set(false); this.cdr.markForCheck(); },
      error: () => { this.loading.set(false); this.cdr.markForCheck(); },
    });
  }

  toggleFormulario(): void {
    if (this.contexto()?.cotizacion_activa) return;
    this.mostrarFormulario.update((v) => !v);
    this.cdr.markForCheck();
  }

  usarEtaSugerida(): void {
    const eta = this.contexto()?.eta_sugerida_min;
    if (eta && eta <= ETA_LLEGADA_MAX_MIN) {
      this.patchDuracion('llegada', eta);
      this.cdr.markForCheck();
    }
  }

  addItem(): void {
    this.items.push(this.fb.group({
      descripcion:     [''],
      cantidad:        [1, [Validators.min(0.001)]],
      precio_unitario: [0, [Validators.min(0)]],
    }));
    this.cdr.markForCheck();
  }

  removeItem(i: number): void {
    this.items.removeAt(i);
    this.cdr.markForCheck();
  }

  subtotal(i: number): number {
    const g = this.items.at(i);
    return (g.value.cantidad ?? 0) * (g.value.precio_unitario ?? 0);
  }

  itemsTotal(): number {
    return this.items.controls.reduce((acc, _, i) => acc + this.subtotal(i), 0);
  }

  costoTraslado(): number {
    return this.contexto()?.costo_traslado_estimado ?? 0;
  }

  totalEstimado(): number {
    const servicio = Number(this.form.value.monto_total ?? 0);
    return servicio + this.costoTraslado();
  }

  tarifaTrasladoKm(): number {
    return this.contexto()?.tarifa_traslado_bs_km ?? 5;
  }

  hintFormulario(): string | null {
    if (this.form.valid) return null;
    const f = this.form.controls;
    if (f['descripcion_danio'].invalid) return 'Completá la descripción del daño (mín. 5 caracteres).';
    if (f['detalle_servicio'].invalid) return 'Completá el detalle del servicio (mín. 5 caracteres).';
    if (f['monto_total'].invalid) return 'Ingresá un monto total mayor a 0 BOB.';
    if (f['llegada_minutos'].invalid || f['reparacion_minutos'].invalid) {
      return 'Los minutos deben estar entre 0 y 59.';
    }
    return 'Revisá los campos marcados antes de enviar.';
  }

  private buildItemsPayload(): CotizacionItemIn[] | null {
    const raw = (this.form.value.items ?? []) as CotizacionItemIn[];
    const filled = raw.filter((i) => (i.descripcion ?? '').trim().length > 0);
    if (filled.length === 0) return [];

    for (const item of filled) {
      if (!item.descripcion?.trim() || (item.precio_unitario ?? 0) <= 0) {
        this.msg.set({
          tipo: 'error',
          texto: 'En cada ítem del desglose completá descripción y precio, o eliminalo.',
        });
        return null;
      }
    }
    return filled;
  }

  private parseApiError(err: unknown): string {
    const detail = (err as { error?: { detail?: unknown } })?.error?.detail;
    if (typeof detail === 'string') return detail;
    if (Array.isArray(detail)) {
      return detail
        .map((e: { loc?: string[]; msg?: string }) => {
          const field = e.loc?.slice(-1)[0] ?? '';
          if (field === 'tiempo_estimado_llegada_min') {
            return 'El tiempo de llegada es demasiado alto (máximo 7 días). Revisá horas y minutos de llegada.';
          }
          if (field === 'tiempo_estimado_reparacion_min') {
            return 'El tiempo de reparación es demasiado alto. Revisá horas y minutos de reparación.';
          }
          return e.msg ?? 'Datos inválidos.';
        })
        .join(' ');
    }
    return 'Error al enviar la cotización.';
  }

  enviar(): void {
    if (this.saving()) return;

    this.form.markAllAsTouched();
    if (this.form.invalid) {
      this.msg.set({ tipo: 'error', texto: this.hintFormulario() ?? 'Completá el formulario.' });
      this.cdr.markForCheck();
      return;
    }

    const llegadaMin = this.duracionTotalMinutos('llegada');
    const reparacionMin = this.duracionTotalMinutos('reparacion');

    if (llegadaMin > ETA_LLEGADA_MAX_MIN) {
      this.msg.set({
        tipo: 'error',
        texto: `El ETA de llegada no puede superar 7 días (${ETA_LLEGADA_MAX_MIN} min). Tenés ${formatEtaMinutos(llegadaMin)}.`,
      });
      this.cdr.markForCheck();
      return;
    }

    if (reparacionMin > ETA_REPARACION_MAX_MIN) {
      this.msg.set({
        tipo: 'error',
        texto: 'El tiempo de reparación es demasiado alto. Revisá horas y minutos.',
      });
      this.cdr.markForCheck();
      return;
    }

    const items = this.buildItemsPayload();
    if (items === null) {
      this.cdr.markForCheck();
      return;
    }

    this.saving.set(true);
    this.msg.set(null);

    const v = this.form.value;
    const body: CotizacionCreateIn = {
      descripcion_danio:              v.descripcion_danio!,
      detalle_servicio:               v.detalle_servicio!,
      monto_total:                    v.monto_total!,
      tiempo_estimado_llegada_min:    llegadaMin > 0 ? llegadaMin : null,
      tiempo_estimado_reparacion_min: reparacionMin > 0 ? reparacionMin : null,
      incluye_grua:                   v.incluye_grua ?? false,
      comentarios:                    v.comentarios ?? null,
      items,
    };

    this.cotSvc.proponer(this.solicitudId(), body).subscribe({
      next: (cot) => {
        this.cotizaciones.set([...this.cotizaciones(), cot]);
        this.form.reset({
          incluye_grua: false,
          llegada_horas: 0,
          llegada_minutos: 0,
          reparacion_horas: 0,
          reparacion_minutos: 0,
        });
        this.items.clear();
        this.mostrarFormulario.set(false);
        this.saving.set(false);
        this.msg.set({ tipo: 'ok', texto: 'Cotización enviada. El cliente la verá junto con las demás ofertas.' });
        this.contexto.update((c) => (c ? { ...c, cotizacion_activa: true } : c));
        this.cdr.markForCheck();
      },
      error: (err) => {
        this.saving.set(false);
        this.msg.set({ tipo: 'error', texto: this.parseApiError(err) });
        this.cdr.markForCheck();
      },
    });
  }

  labelEstado(estado: string): string {
    const map: Record<string, string> = {
      ENVIADA: 'Enviada', ACEPTADA: 'Aceptada', RECHAZADA: 'Rechazada', EXPIRADA: 'Expirada',
    };
    return map[estado] ?? estado;
  }

  etaLabel(minutos: number | null | undefined, approximate = false): string {
    return formatEtaMinutos(minutos, { approximate });
  }
}
