import { useMemo, type ReactNode } from 'react';
import {
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';
import type { StageDetailResponse, StageName } from '../../api/types';

interface SpectrumModalProps {
  open: boolean;
  stage: StageName | null;
  detail?: StageDetailResponse;
  loading?: boolean;
  onClose: () => void;
}

export function SpectrumModal({ open, stage, detail, loading, onClose }: SpectrumModalProps) {
  const spectrumData = useMemo(() => {
    if (!detail) return [];
    return detail.spectrum.frequencies.map((freq, index) => ({
      freq,
      magnitude: detail.spectrum.magnitudes[index] ?? 0,
    }));
  }, [detail]);

  const waveformData = useMemo(() => {
    if (!detail) return [];
    const sampleRate = detail.waveform.sample_rate;
    return detail.waveform.samples.map((value, index) => ({
      time: index / sampleRate,
      value,
    }));
  }, [detail]);

  if (!open || !stage) return null;

  return (
    <div className="spectrum-backdrop">
      <div className="spectrum-modal">
        <header className="spectrum-header">
          <div>
            <p className="spectrum-subtitle">Stage</p>
            <h2 className="spectrum-title">{stage.toUpperCase()}</h2>
          </div>
          <button
            onClick={onClose}
            className="ghost-button"
          >
            Close
          </button>
        </header>
        {loading && <p className="muted-text">Loading spectra...</p>}
        {!loading && detail && (
          <div className="spectrum-grid">
            <ChartPanel title="Amplitude Spectrum" xLabel="Frequency (Hz)">
              <ResponsiveContainer width="100%" height={240}>
                <LineChart data={spectrumData} margin={{ top: 10, left: 10, right: 10, bottom: 10 }}>
                  <XAxis
                    dataKey="freq"
                    tickFormatter={(value) => `${(value / 1e6).toFixed(2)}M`}
                    stroke="#94a3b8"
                  />
                  <YAxis stroke="#94a3b8" tickFormatter={(value) => value.toExponential(1)} />
                  <Tooltip formatter={(value: number) => value.toPrecision(3)} labelFormatter={(label) => `${label.toFixed(0)} Hz`} />
                  <Line type="monotone" dataKey="magnitude" stroke="#6366f1" dot={false} strokeWidth={2} />
                </LineChart>
              </ResponsiveContainer>
            </ChartPanel>
            <ChartPanel title="Waveform" xLabel="Time (s)">
              <ResponsiveContainer width="100%" height={240}>
                <LineChart data={waveformData} margin={{ top: 10, left: 10, right: 10, bottom: 10 }}>
                  <XAxis dataKey="time" stroke="#94a3b8" tickFormatter={(value) => value.toFixed(3)} />
                  <YAxis stroke="#94a3b8" domain={['auto', 'auto']} />
                  <Tooltip formatter={(value: number) => value.toFixed(3)} labelFormatter={(label) => `${label.toFixed(4)} s`} />
                  <Line type="linear" dataKey="value" stroke="#0ea5e9" dot={false} strokeWidth={1.5} />
                </LineChart>
              </ResponsiveContainer>
            </ChartPanel>
          </div>
        )}
        {!loading && !detail && <p className="text-sm text-rose-500">Failed to fetch spectrum.</p>}
      </div>
    </div>
  );
}

function ChartPanel({ title, children, xLabel }: { title: string; children: ReactNode; xLabel: string }) {
  return (
    <div className="chart-panel">
      <h3 className="chart-panel__title">{title}</h3>
      <div className="chart-panel__canvas">{children}</div>
      <p className="chart-panel__label">{xLabel}</p>
    </div>
  );
}
