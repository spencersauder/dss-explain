interface SpectrumComparisonProps {
  chipRate: number;
  noisePower: number;
  noiseBandwidth: number;
  secretLength: number;
}

export function SpectrumComparison({ chipRate, noisePower, noiseBandwidth, secretLength }: SpectrumComparisonProps) {
  const chipsPerBit = Math.max(8, secretLength * 4);
  const basebandWidth = chipRate;
  const spreadWidth = chipRate * chipsPerBit;
  const maxWidth = Math.max(spreadWidth, noiseBandwidth, basebandWidth, 1);

  const toPercent = (value: number) => `${Math.min(100, (value / maxWidth) * 100).toFixed(2)}%`;

  return (
    <div className="spectrum-compare">
      <div className="spectrum-row">
        <span className="spectrum-label">До расширения</span>
        <div className="spectrum-bar">
          <span className="spectrum-bar__noise" style={{ width: toPercent(noiseBandwidth) }} />
          <span className="spectrum-bar__signal" style={{ width: toPercent(basebandWidth) }} />
        </div>
      </div>
      <div className="spectrum-row">
        <span className="spectrum-label">После расширения</span>
        <div className="spectrum-bar">
          <span className="spectrum-bar__noise" style={{ width: toPercent(noiseBandwidth) }} />
          <span className="spectrum-bar__signal" style={{ width: toPercent(spreadWidth) }} />
        </div>
      </div>
      <div className="spectrum-legend">
        <span>
          <span className="legend-dot legend-dot--signal" />Сигнал (≈ {Math.round(basebandWidth / 1000)} кГц →
          {Math.round(spreadWidth / 1000)} кГц)
        </span>
        <span>
          <span className="legend-dot legend-dot--noise" />Полоса шума ≈ {Math.round(noiseBandwidth / 1000)} кГц, уровень σ² ={' '}
          {noisePower.toFixed(1)}
        </span>
      </div>
    </div>
  );
}
