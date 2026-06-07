/** Límite API backend para ETA de llegada (7 días). */
export const ETA_LLEGADA_MAX_MIN = 10080;

/** Límite API backend para tiempo de reparación. */
export const ETA_REPARACION_MAX_MIN = 100000;

/**
 * Formatea minutos de ETA para lectura humana.
 * - Menos de 60 min → "45 min"
 * - 60 min o más → "1 hora", "1 hora 15 min", "2 horas 5 min", etc.
 */
export function formatEtaMinutos(
  minutos: number | null | undefined,
  options?: { approximate?: boolean },
): string {
  if (minutos == null || minutos < 0) return '—';

  const prefix = options?.approximate ? '~' : '';

  if (minutos >= 60) {
    const horas = Math.floor(minutos / 60);
    const mins = minutos % 60;
    const horaLabel = horas === 1 ? '1 hora' : `${horas} horas`;
    if (mins === 0) return `${prefix}${horaLabel}`;
    return `${prefix}${horaLabel} ${mins} min`;
  }

  return `${prefix}${minutos} min`;
}

/** Convierte horas + minutos a total en minutos. */
export function minutosFromHorasMin(horas: number, minutos: number): number {
  return Math.max(0, horas) * 60 + Math.max(0, minutos);
}

/** Descompone minutos totales en horas y minutos restantes. */
export function minutosToHorasMin(total: number): { horas: number; minutos: number } {
  const safe = Math.max(0, Math.floor(total));
  return { horas: Math.floor(safe / 60), minutos: safe % 60 };
}
