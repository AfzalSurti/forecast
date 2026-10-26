import { useMemo } from 'react';
import {
  Bar,
  BarChart,
  CartesianGrid,
  ComposedChart,
  Legend,
  Line,
  LineChart,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';
import {
  api,
  type ComparisonPoint,
  type HorizonMetrics,
  type HourMetrics,
  type Metrics,
  type Window,
} from '../api/client';
import { Panel } from '../components/Panel';
import {
  axisProps,
  COLORS,
  gridProps,
  legendProps,
  mwTick,
  tooltipProps,
} from '../components/chartTheme';
import { useApi } from '../hooks/useApi';
import { fmtMW, fmtPct } from '../lib/format';

interface Props {
  window: Window;
  horizon: number;
}

const BIN_MW = 500;
const mwFormatter = (v: number, name: string) => [fmtMW(v, name === 'Bias'), name];

interface Bin {
  from: number;
  label: string;
  count: number;
  share: number;
}

/** Bucket forecast errors into fixed-width MW bins. */
function histogram(rows: ComparisonPoint[]): Bin[] {
  const errors = rows.map((r) => r.error_mw).filter((e): e is number => e != null);
  if (errors.length === 0) return [];
  const lo = Math.floor(Math.min(...errors) / BIN_MW) * BIN_MW;
  const hi = Math.floor(Math.max(...errors) / BIN_MW) * BIN_MW;
  const bins: Bin[] = [];
  for (let from = lo; from <= hi; from += BIN_MW) {
    bins.push({ from, label: `${from / 1000}`, count: 0, share: 0 });
  }
  errors.forEach((e) => bins[Math.floor((e - lo) / BIN_MW)].count++);
  bins.forEach((b) => (b.share = (100 * b.count) / errors.length));
  return bins;
}

function Takeaway({
  metrics,
  byHorizon,
  byHour,
}: {
  metrics: Metrics;
  byHorizon: HorizonMetrics[] | null;
  byHour: HourMetrics[] | null;
}) {
  const h = metrics.horizon_hours;
  const p90 = metrics.abs_error_percentiles.p90;
  const p95 = metrics.abs_error_percentiles.p95;
  const shortfall90 = metrics.error_percentiles.p90;
  const bias = metrics.bias;
  if (p90 == null || bias == null) {
    return (
      <p>
        No forecasts qualify at a {h}h horizon in this window (coverage{' '}
        {fmtPct(metrics.coverage_pct, 0)}). WINDFOR runs out around 47h ahead, so try a shorter
        horizon.
      </p>
    );
  }
  const base = byHorizon?.find((r) => r.horizon_hours === 0)?.mae ?? null;
  const worstHour = byHour
    ?.filter((r) => r.mae != null)
    .reduce<HourMetrics | null>((w, r) => (!w || r.mae! > w.mae! ? r : w), null);

  return (
    <ul className="takeaways">
      <li>
        At a <strong>{h}h</strong> horizon, a buffer of <strong>{fmtMW(p90)}</strong> covers 90% of
        forecast misses in either direction ({fmtMW(p95)} for 95%).
      </li>
      <li>
        The forecast runs <strong>{bias > 0 ? 'high' : 'low'}</strong> by{' '}
        <strong>{fmtMW(Math.abs(bias))}</strong> on average: wind usually delivers{' '}
        {bias > 0 ? 'less' : 'more'} than forecast, so plan to buy {bias > 0 ? 'more' : 'less'} from
        the market than the raw forecast implies.
      </li>
      {shortfall90 != null && shortfall90 > 0 && Math.abs(shortfall90 - p90) > 50 && (
        <li>
          Wind fell short of forecast by more than <strong>{fmtMW(shortfall90)}</strong> in only 10%
          of hours, which sizes a one-sided buffer against shortfalls.
        </li>
      )}
      {base != null && metrics.mae != null && h > 0 && (
        <li>
          Committing {h}h ahead instead of at the last forecast costs{' '}
          <strong>{fmtMW(metrics.mae - base)}</strong> of extra MAE ({fmtMW(base)} →{' '}
          {fmtMW(metrics.mae)}).
        </li>
      )}
      {worstHour && (
        <li>
          Errors peak around <strong>{String(worstHour.hour).padStart(2, '0')}:00 UTC</strong> (MAE{' '}
          {fmtMW(worstHour.mae)}).
        </li>
      )}
    </ul>
  );
}

export function ForecastAccuracy({ window, horizon }: Props) {
  const byHorizon = useApi(() => api.metricsByHorizon(window), [window.start, window.end]);
  const comparison = useApi(
    () => api.comparison(window, horizon),
    [window.start, window.end, horizon],
  );
  const byHour = useApi(
    () => api.metricsByHour(window, horizon),
    [window.start, window.end, horizon],
  );
  const metrics = useApi(() => api.metrics(window, horizon), [window.start, window.end, horizon]);

  const bins = useMemo(() => histogram(comparison.data ?? []), [comparison.data]);
  const horizonRows = byHorizon.data?.filter((r) => r.mae != null) ?? [];

  return (
    <div className="view">
      <Panel
        title="Trader takeaway"
        className="panel-takeaway"
        loading={metrics.loading}
        error={metrics.error}
        empty={!metrics.data}
      >
        {metrics.data && (
          <Takeaway metrics={metrics.data} byHorizon={byHorizon.data} byHour={byHour.data} />
        )}
      </Panel>

      <div className="grid-2">
        <Panel
          title="Error vs forecast horizon"
          subtitle="How accuracy degrades the further ahead you commit. Horizons above ~44h lose coverage as WINDFOR extends only ~47h."
          loading={byHorizon.loading}
          error={byHorizon.error}
          empty={horizonRows.length === 0}
          className="span-2"
        >
          <div className="chart">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={horizonRows} margin={{ top: 8, right: 16, bottom: 0, left: 0 }}>
                <CartesianGrid {...gridProps} />
                <XAxis
                  dataKey="horizon_hours"
                  type="number"
                  domain={[0, 48]}
                  ticks={[0, 6, 12, 18, 24, 30, 36, 42, 48]}
                  tickFormatter={(v: number) => `${v}h`}
                  {...axisProps}
                />
                <YAxis tickFormatter={mwTick} width={64} {...axisProps} />
                <Tooltip
                  {...tooltipProps}
                  labelFormatter={(v: number) => `${v}h ahead`}
                  formatter={mwFormatter}
                />
                <Legend {...legendProps} />
                <ReferenceLine x={horizon} stroke={COLORS.muted} strokeDasharray="4 4" />
                <ReferenceLine y={0} stroke={COLORS.zero} />
                {(
                  [
                    ['mae', 'MAE', COLORS.actual],
                    ['rmse', 'RMSE', COLORS.forecast],
                    ['bias', 'Bias', COLORS.series3],
                    ['p90_abs_error', 'P90 abs error', COLORS.series4],
                  ] as const
                ).map(([key, name, color]) => (
                  <Line
                    key={key}
                    dataKey={key}
                    name={name}
                    stroke={color}
                    strokeWidth={2}
                    dot={false}
                    activeDot={{ r: 4, strokeWidth: 2, stroke: '#1a1a19' }}
                    isAnimationActive={false}
                  />
                ))}
              </LineChart>
            </ResponsiveContainer>
          </div>
        </Panel>

        <Panel
          title={`Error distribution · ${horizon}h`}
          subtitle="Share of hours by forecast − actual (GW). Right of zero: wind came in below forecast."
          loading={comparison.loading}
          error={comparison.error}
          empty={bins.length === 0}
        >
          <div className="chart">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart
                data={bins}
                margin={{ top: 8, right: 16, bottom: 0, left: 0 }}
                barCategoryGap={2}
              >
                <CartesianGrid {...gridProps} />
                <XAxis dataKey="label" interval="preserveStartEnd" minTickGap={16} {...axisProps} />
                <YAxis tickFormatter={(v: number) => `${v}%`} width={44} {...axisProps} />
                <Tooltip
                  {...tooltipProps}
                  cursor={{ fill: 'rgba(255,255,255,0.05)' }}
                  labelFormatter={(_, p) => {
                    const from = (p?.[0]?.payload as Bin | undefined)?.from;
                    return from == null
                      ? ''
                      : `${fmtMW(from, true)} to ${fmtMW(from + BIN_MW, true)}`;
                  }}
                  formatter={(v, _n, item) => [
                    `${Number(v).toFixed(1)}% (${(item.payload as Bin).count} h)`,
                    'Share',
                  ]}
                />
                <Bar
                  dataKey="share"
                  fill={COLORS.actual}
                  radius={[4, 4, 0, 0]}
                  isAnimationActive={false}
                />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </Panel>

        <Panel
          title={`Error by hour of day · ${horizon}h`}
          subtitle="MAE (bars) and bias (line) per UTC hour of the target slot."
          loading={byHour.loading}
          error={byHour.error}
          empty={!byHour.data?.some((r) => r.n > 0)}
        >
          <div className="chart">
            <ResponsiveContainer width="100%" height="100%">
              <ComposedChart
                data={byHour.data ?? []}
                margin={{ top: 8, right: 16, bottom: 0, left: 0 }}
              >
                <CartesianGrid {...gridProps} />
                <XAxis
                  dataKey="hour"
                  tickFormatter={(v: number) => String(v).padStart(2, '0')}
                  interval={2}
                  {...axisProps}
                />
                <YAxis tickFormatter={mwTick} width={64} {...axisProps} />
                <Tooltip
                  {...tooltipProps}
                  cursor={{ fill: 'rgba(255,255,255,0.05)' }}
                  labelFormatter={(v: number) => `${String(v).padStart(2, '0')}:00 UTC`}
                  formatter={mwFormatter}
                />
                <Legend {...legendProps} />
                <ReferenceLine y={0} stroke={COLORS.zero} />
                <Bar
                  dataKey="mae"
                  name="MAE"
                  fill={COLORS.actual}
                  radius={[4, 4, 0, 0]}
                  isAnimationActive={false}
                />
                <Line
                  dataKey="bias"
                  name="Bias"
                  stroke={COLORS.forecast}
                  strokeWidth={2}
                  dot={false}
                  isAnimationActive={false}
                />
              </ComposedChart>
            </ResponsiveContainer>
          </div>
        </Panel>
      </div>
    </div>
  );
}
