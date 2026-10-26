/** Typed client for the FastAPI backend. */

const API_BASE = (import.meta.env.VITE_API_BASE_URL ?? '').replace(/\/$/, '');

export interface ActualPoint {
  start_time: string;
  generation_mw: number;
}

export interface ForecastPoint {
  start_time: string;
  publish_time: string | null;
  lead_hours: number | null;
  generation_mw: number | null;
}

export interface ComparisonPoint {
  start_time: string;
  actual_mw: number | null;
  forecast_mw: number | null;
  publish_time: string | null;
  lead_hours: number | null;
  error_mw: number | null;
}

export interface Percentiles {
  p10: number | null;
  p50: number | null;
  p90: number | null;
  p95: number | null;
}

export interface Metrics {
  horizon_hours: number;
  start: string;
  end: string;
  n_slots: number;
  n_forecasts: number;
  coverage_pct: number;
  mae: number | null;
  rmse: number | null;
  bias: number | null;
  mape: number | null;
  nmae_pct: number | null;
  mean_actual: number | null;
  error_percentiles: Percentiles;
  abs_error_percentiles: Percentiles;
}

export interface HorizonMetrics {
  horizon_hours: number;
  n_forecasts: number;
  coverage_pct: number;
  mae: number | null;
  rmse: number | null;
  bias: number | null;
  p90_abs_error: number | null;
}

export interface HourMetrics {
  hour: number;
  n: number;
  mae: number | null;
  rmse: number | null;
  bias: number | null;
}

export interface Window {
  start: string;
  end: string;
}

async function get<T>(path: string, params: Record<string, string | number>): Promise<T> {
  const query = new URLSearchParams(
    Object.entries(params).map(([k, v]) => [k, String(v)]),
  ).toString();
  const response = await fetch(`${API_BASE}${path}?${query}`);
  if (!response.ok) {
    let detail = response.statusText;
    try {
      const body = await response.json();
      detail = typeof body.detail === 'string' ? body.detail : JSON.stringify(body.detail);
    } catch {
      // Non-JSON error body; keep the status text.
    }
    throw new Error(`API ${response.status}: ${detail}`);
  }
  return response.json() as Promise<T>;
}

export const api = {
  actuals: (w: Window) => get<ActualPoint[]>('/api/actuals', { ...w }),
  forecasts: (w: Window, horizon: number) =>
    get<ForecastPoint[]>('/api/forecasts', { ...w, horizon }),
  comparison: (w: Window, horizon: number) =>
    get<ComparisonPoint[]>('/api/comparison', { ...w, horizon }),
  metrics: (w: Window, horizon: number) => get<Metrics>('/api/metrics', { ...w, horizon }),
  metricsByHorizon: (w: Window) => get<HorizonMetrics[]>('/api/metrics/by-horizon', { ...w }),
  metricsByHour: (w: Window, horizon: number) =>
    get<HourMetrics[]>('/api/metrics/by-hour', { ...w, horizon }),
};
