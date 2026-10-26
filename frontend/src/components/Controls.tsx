import { DATA_END, DATA_START } from '../lib/format';

interface WindowPickerProps {
  start: string;
  end: string;
  onChange: (start: string, end: string) => void;
}

/** Start/end pickers constrained to January 2026 (values are UTC). */
export function WindowPicker({ start, end, onChange }: WindowPickerProps) {
  return (
    <div className="control-group">
      <label className="control">
        <span className="control-label">Start (UTC)</span>
        <input
          type="datetime-local"
          min={DATA_START}
          max={end}
          step={1800}
          value={start}
          onChange={(e) => e.target.value && onChange(e.target.value, end)}
        />
      </label>
      <label className="control">
        <span className="control-label">End (UTC)</span>
        <input
          type="datetime-local"
          min={start}
          max={DATA_END}
          step={1800}
          value={end}
          onChange={(e) => e.target.value && onChange(start, e.target.value)}
        />
      </label>
      <button
        type="button"
        className="ghost-button"
        onClick={() => onChange(DATA_START, DATA_END)}
        disabled={start === DATA_START && end === DATA_END}
      >
        Full month
      </button>
    </div>
  );
}

interface HorizonSliderProps {
  value: number;
  onChange: (value: number) => void;
}

/** Forecast horizon selector, 0–48 hours. */
export function HorizonSlider({ value, onChange }: HorizonSliderProps) {
  return (
    <label className="control control-slider">
      <span className="control-label">
        Forecast horizon <strong className="horizon-value">{value}h</strong>
      </span>
      <input
        type="range"
        min={0}
        max={48}
        step={1}
        value={value}
        onChange={(e) => onChange(Number(e.target.value))}
        aria-valuetext={`${value} hours ahead`}
      />
      <span className="slider-scale" aria-hidden="true">
        <span>0h</span>
        <span>12h</span>
        <span>24h</span>
        <span>36h</span>
        <span>48h</span>
      </span>
    </label>
  );
}
