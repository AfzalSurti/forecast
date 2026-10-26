import type { ReactNode } from 'react';

interface PanelProps {
  title: string;
  subtitle?: ReactNode;
  loading?: boolean;
  error?: string | null;
  empty?: boolean;
  className?: string;
  children: ReactNode;
}

/** Card wrapper with consistent loading, error and empty states. */
export function Panel({ title, subtitle, loading, error, empty, className, children }: PanelProps) {
  let body = children;
  if (error) {
    body = (
      <div className="state state-error" role="alert">
        <strong>Could not load data.</strong>
        <span>{error}</span>
      </div>
    );
  } else if (loading && empty) {
    body = (
      <div className="state" aria-busy="true">
        <span className="spinner" aria-hidden="true" />
        Loading…
      </div>
    );
  } else if (empty) {
    body = <div className="state">No data for the selected window.</div>;
  }

  return (
    <section className={`panel ${className ?? ''}`}>
      <header className="panel-header">
        <h2>{title}</h2>
        {loading && !empty && !error && <span className="updating">Updating…</span>}
      </header>
      {subtitle && <p className="panel-subtitle">{subtitle}</p>}
      <div className="panel-body">{body}</div>
    </section>
  );
}

interface KpiCardProps {
  label: string;
  value: string;
  hint: string;
}

export function KpiCard({ label, value, hint }: KpiCardProps) {
  return (
    <div className="kpi">
      <span className="kpi-label">{label}</span>
      <span className="kpi-value">{value}</span>
      <span className="kpi-hint">{hint}</span>
    </div>
  );
}
