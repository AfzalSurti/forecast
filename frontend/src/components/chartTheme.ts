/** Shared Recharts styling, tuned for the dark trading-desk surface. */

export const COLORS = {
  actual: '#3987e5',
  forecast: '#d95926',
  series3: '#199e70',
  series4: '#c98500',
  grid: '#2c2c2a',
  axis: '#383835',
  muted: '#898781',
  zero: '#6b6a65',
};

export const axisProps = {
  stroke: COLORS.axis,
  tick: { fill: COLORS.muted, fontSize: 12 },
  tickLine: false,
} as const;

export const gridProps = {
  stroke: COLORS.grid,
  strokeDasharray: '0',
  vertical: false,
} as const;

export const tooltipProps = {
  contentStyle: {
    background: '#232322',
    border: '1px solid rgba(255,255,255,0.12)',
    borderRadius: 8,
    color: '#f0efec',
    fontSize: 13,
  },
  labelStyle: { color: '#c3c2b7', marginBottom: 4 },
  itemStyle: { padding: 0 },
  cursor: { stroke: COLORS.muted, strokeWidth: 1 },
} as const;

export const legendProps = {
  iconType: 'plainline',
  wrapperStyle: { fontSize: 13, color: '#c3c2b7', paddingTop: 8 },
} as const;

export const mwTick = (v: number) => `${(v / 1000).toFixed(v % 1000 === 0 ? 0 : 1)} GW`;
