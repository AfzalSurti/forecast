import { useMemo } from 'react';
import {
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';
import { api, type Window } from '../api/client';
import { KpiCard, Panel } from '../components/Panel';
import {
  axisProps,
  COLORS,
  gridProps,
  legendProps,
  mwTick,
  tooltipProps,
} from '../components/chartTheme';
import { useApi } from '../hooks/useApi';
import { fmtDateTime, fmtDay, fmtMW, fmtPct } from '../lib/format';

interface Props {
  window: Window;
  horizon: number;
}

interface Row {
  t: number;
  actual?: number;
  /** Published forecast value (hourly slots only). */
  forecast?: number;
  /** Plotted value: `forecast`, or a bridge between two hourly forecasts. */
  forecastLine?: number;
}

const HALF_HOUR_MS = 1_800_000;

interface TooltipProps {
  active?: boolean;
  payload?: { payload: Row }[];
  horizon: number;
}

function ChartTooltip({ active, payload, horizon }: TooltipProps) {
  const row = payload?.[0]?.payload;
  if (!active || !row) return null;
  const error = row.forecast != null && row.actual != null ? row.forecast - row.actual : null;
  return (
    <div className="chart-tooltip">
      <div className="chart-tooltip-label">{fmtDateTime(row.t)}</div>
      <div>
        <span className="swatch" style={{ background: COLORS.actual }} />
        Actual <strong>{fmtMW(row.actual)}</strong>
      </div>
      <div>
        <span className="swatch" style={{ background: COLORS.forecast }} />
        Forecast ({horizon}h) <strong>{fmtMW(row.forecast)}</strong>
      </div>
      {error != null && <div className="chart-tooltip-muted">Error {fmtMW(error, true)}</div>}
    </div>
  );
}

export function ForecastVsActual({ window, horizon }: Props) {
  const actuals = useApi(() => api.actuals(window), [window.start, window.end]);
  const forecasts = useApi(
    () => api.forecasts(window, horizon),
    [window.start, window.end, horizon],
  );
  const metrics = useApi(() => api.metrics(window, horizon), [window.start, window.end, horizon]);

  const rows = useMemo<Row[]>(() => {
    const byTime = new Map<number, Row>();
    const row = (iso: string) => {
      const t = Date.parse(iso);
      let r = byTime.get(t);
      if (!r) {
        r = { t };
        byTime.set(t, r);
      }
      return r;
    };
    actuals.data?.forEach((p) => (row(p.start_time).actual = p.generation_mw));
    forecasts.data?.forEach((p) => {
      if (p.generation_mw != null) row(p.start_time).forecast = p.generation_mw;
    });
    const sorted = [...byTime.values()].sort((a, b) => a.t - b.t);
    // Forecasts are hourly: bridge half-hour rows only between two real forecasts,
    // so genuine gaps (no qualifying forecast) still break the line.
    sorted.forEach((r, i) => {
      if (r.forecast != null) {
        r.forecastLine = r.forecast;
        return;
      }
      const prev = sorted[i - 1];
      const next = sorted[i + 1];
      if (
        prev?.forecast != null &&
        next?.forecast != null &&
        next.t - prev.t === 2 * HALF_HOUR_MS
      ) {
        r.forecastLine = (prev.forecast + next.forecast) / 2;
      }
    });
    return sorted;
  }, [actuals.data, forecasts.data]);

  const m = metrics.data;
  const spanDays = (Date.parse(window.end) - Date.parse(window.start)) / 86_400_000;
  const error = actuals.error ?? forecasts.error;

  return (
    <div className="view">
      <div className="kpi-row">
        <KpiCard label="MAE" value={fmtMW(m?.mae)} hint="Mean absolute error" />
        <KpiCard label="RMSE" value={fmtMW(m?.rmse)} hint="Penalises large misses" />
        <KpiCard
          label="Bias"
          value={fmtMW(m?.bias, true)}
          hint={
            m?.bias == null
              ? 'Mean forecast − actual'
              : m.bias > 0
                ? 'Forecast runs high on average'
                : 'Forecast runs low on average'
          }
        />
        <KpiCard
          label="P90 abs error"
          value={fmtMW(m?.abs_error_percentiles.p90)}
          hint={`90% of misses are smaller · coverage ${fmtPct(m?.coverage_pct, 0)}`}
        />
      </div>
      {metrics.error && (
        <div className="state state-error inline" role="alert">
          Metrics unavailable: {metrics.error}
        </div>
      )}

      <Panel
        title="Wind generation: actual vs forecast"
        subtitle={
          <>
            Actual outturn (FUELHH, half-hourly) against the latest WINDFOR forecast published at
            least <strong>{horizon}h</strong> before each hour. Gaps mean no forecast qualified.
          </>
        }
        loading={actuals.loading || forecasts.loading}
        error={error}
        empty={rows.length === 0}
      >
        <div className="chart chart-tall">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={rows} margin={{ top: 8, right: 16, bottom: 0, left: 0 }}>
              <CartesianGrid {...gridProps} />
              <XAxis
                dataKey="t"
                type="number"
                scale="time"
                domain={['dataMin', 'dataMax']}
                tickFormatter={(t: number) => (spanDays > 2 ? fmtDay(t) : fmtDateTime(t))}
                minTickGap={40}
                {...axisProps}
              />
              <YAxis tickFormatter={mwTick} width={64} {...axisProps} />
              <Tooltip cursor={tooltipProps.cursor} content={<ChartTooltip horizon={horizon} />} />
              <Legend {...legendProps} />
              <Line
                name="Actual"
                dataKey="actual"
                stroke={COLORS.actual}
                strokeWidth={2}
                dot={false}
                activeDot={{ r: 4, strokeWidth: 2, stroke: '#1a1a19' }}
                connectNulls
                isAnimationActive={false}
              />
              <Line
                name={`Forecast (${horizon}h ahead)`}
                dataKey="forecastLine"
                stroke={COLORS.forecast}
                strokeWidth={2}
                dot={false}
                activeDot={{ r: 4, strokeWidth: 2, stroke: '#1a1a19' }}
                connectNulls={false}
                isAnimationActive={false}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </Panel>
    </div>
  );
}
