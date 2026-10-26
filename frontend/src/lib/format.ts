/** Formatting helpers. All timestamps are displayed in UTC. */

export const DATA_START = '2026-01-01T00:00';
export const DATA_END = '2026-01-31T23:30';

const mwFormat = new Intl.NumberFormat('en-GB', { maximumFractionDigits: 0 });

export function fmtMW(value: number | null | undefined, signed = false): string {
  if (value == null || Number.isNaN(value)) return '—';
  const text = `${mwFormat.format(Math.abs(value))} MW`;
  if (!signed) return value < 0 ? `-${text}` : text;
  return `${value > 0 ? '+' : value < 0 ? '−' : ''}${text}`;
}

export function fmtPct(value: number | null | undefined, digits = 1): string {
  if (value == null || Number.isNaN(value)) return '—';
  return `${value.toFixed(digits)}%`;
}

/** `datetime-local` value (implicitly UTC) -> ISO string with Z. */
export function localInputToIso(value: string): string {
  return `${value}:00Z`;
}

const dateTimeFormat = new Intl.DateTimeFormat('en-GB', {
  day: '2-digit',
  month: 'short',
  hour: '2-digit',
  minute: '2-digit',
  timeZone: 'UTC',
});
const dayFormat = new Intl.DateTimeFormat('en-GB', {
  day: '2-digit',
  month: 'short',
  timeZone: 'UTC',
});

export function fmtDateTime(ms: number): string {
  return `${dateTimeFormat.format(ms)} UTC`;
}

export function fmtDay(ms: number): string {
  return dayFormat.format(ms);
}
