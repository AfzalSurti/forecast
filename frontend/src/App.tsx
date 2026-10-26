import { useState } from 'react';
import { HorizonSlider, WindowPicker } from './components/Controls';
import { DATA_END, DATA_START, localInputToIso } from './lib/format';
import { ForecastAccuracy } from './views/ForecastAccuracy';
import { ForecastVsActual } from './views/ForecastVsActual';

type View = 'vs' | 'accuracy';

const TABS: { id: View; label: string }[] = [
  { id: 'vs', label: 'Forecast vs Actual' },
  { id: 'accuracy', label: 'Forecast Accuracy' },
];

const viewFromHash = (): View => (window.location.hash === '#accuracy' ? 'accuracy' : 'vs');

export default function App() {
  const [view, setViewState] = useState<View>(viewFromHash);
  const [start, setStart] = useState(DATA_START);
  const [end, setEnd] = useState(DATA_END);
  // Each view keeps its own horizon: 4h for monitoring, 24h for day-ahead accuracy.
  const [horizonByView, setHorizonByView] = useState<Record<View, number>>({
    vs: 4,
    accuracy: 24,
  });

  const timeWindow = { start: localInputToIso(start), end: localInputToIso(end) };
  const horizon = horizonByView[view];

  const setView = (next: View) => {
    setViewState(next);
    // Keep the active view linkable.
    window.history.replaceState(null, '', next === 'accuracy' ? '#accuracy' : '#');
  };

  return (
    <div className="app">
      <header className="topbar">
        <div className="brand">
          <span className="brand-mark" aria-hidden="true" />
          <div>
            <h1>Wind Forecast Monitor</h1>
            <p>GB national wind · Elexon BMRS · January 2026 · all times UTC</p>
          </div>
        </div>
        <nav className="tabs" role="tablist" aria-label="Views">
          {TABS.map((tab) => (
            <button
              key={tab.id}
              type="button"
              role="tab"
              aria-selected={view === tab.id}
              className={view === tab.id ? 'tab active' : 'tab'}
              onClick={() => setView(tab.id)}
            >
              {tab.label}
            </button>
          ))}
        </nav>
      </header>

      <div className="toolbar">
        <WindowPicker
          start={start}
          end={end}
          onChange={(s, e) => {
            setStart(s);
            setEnd(e);
          }}
        />
        <HorizonSlider
          value={horizon}
          onChange={(h) => setHorizonByView((prev) => ({ ...prev, [view]: h }))}
        />
      </div>

      <main>
        {view === 'vs' ? (
          <ForecastVsActual window={timeWindow} horizon={horizon} />
        ) : (
          <ForecastAccuracy window={timeWindow} horizon={horizon} />
        )}
      </main>

      <footer className="footer">
        Forecast for target time T at horizon H = latest WINDFOR publication with publish time ≤ T −
        H (max 48h lead). Error = forecast − actual.
      </footer>
    </div>
  );
}
