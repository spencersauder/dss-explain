import type { ChangeEvent } from 'react';
import { useMemo, useState } from 'react';
import './App.css';
import type { StageName } from './api/types';
import { FormField } from './components/common/FormField';
import { SpectrumModal } from './components/common/SpectrumModal';
import { TransceiverDiagram } from './components/transceiver/TransceiverDiagram';
import type { SimulationFormValues } from './state/simulationStore';
import { useSimulationStore } from './state/simulationStore';

const STAGE_ORDER: StageName[] = ['source', 'spreader', 'modulator', 'channel', 'correlator', 'decoder'];
const NUMERIC_FIELDS: Array<keyof SimulationFormValues> = [
  'chip_rate',
  'carrier_freq',
  'noise_power',
  'oversampling',
];

function App() {
  const { form, setForm, runSimulation, loading, result, error, stageLoading, loadStageDetail, stageDetails } =
    useSimulationStore();
  const [modalStage, setModalStage] = useState<StageName | null>(null);

  const availableStages = useMemo(() => {
    const fromResult = result?.available_stages;
    if (!fromResult) return STAGE_ORDER;
    return STAGE_ORDER.filter((stage) => fromResult.includes(stage));
  }, [result]);

  const handleInputChange = (event: ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) => {
    const { name, value } = event.target;
    if (NUMERIC_FIELDS.includes(name as keyof SimulationFormValues)) {
      setForm({ [name]: Number(value) } as Partial<SimulationFormValues>);
    } else {
      setForm({ [name]: value } as Partial<SimulationFormValues>);
    }
  };

  const handleStageInspect = async (stage: StageName) => {
    if (!result) return;
    setModalStage(stage);
    await loadStageDetail(stage);
  };

  const closeModal = () => setModalStage(null);

  return (
    <div className="app-shell">
      <header className="hero">
        <div>
          <p className="hero-label">DSSS Link Explorer</p>
          <h1>Visualize transmitter/receiver stages with live spectra</h1>
          <p className="hero-subtitle">
            Encode a message with a secret phrase, push it over an AWGN channel, and analyze how spreading protects the
            payload at each tap of the chain.
          </p>
        </div>
      </header>
      <main className="layout">
        <section className="panel">
          <h2>Transmitter</h2>
          <div className="form-grid">
            <FormField label="Payload message" name="message" value={form.message} onChange={handleInputChange} textarea />
            <FormField label="TX secret phrase" name="tx_secret" value={form.tx_secret} onChange={handleInputChange} />
            <FormField label="RX secret phrase" name="rx_secret" value={form.rx_secret} onChange={handleInputChange} />
            <FormField
              label="Chip rate (chips/s)"
              name="chip_rate"
              type="number"
              min={10_000}
              max={1_000_000}
              step={10_000}
              value={form.chip_rate}
              onChange={handleInputChange}
            />
            <FormField
              label="Carrier frequency (Hz)"
              name="carrier_freq"
              type="number"
              min={100_000}
              max={5_000_000}
              step={50_000}
              value={form.carrier_freq}
              onChange={handleInputChange}
            />
            <label className="form-field">
              <span className="form-label">Noise power</span>
              <input
                type="range"
                min={0}
                max={5}
                step={0.1}
                name="noise_power"
                value={form.noise_power}
                onChange={handleInputChange}
              />
              <span className="slider-value">{form.noise_power.toFixed(1)}</span>
            </label>
            <label className="form-field">
              <span className="form-label">Oversampling</span>
              <select name="oversampling" value={form.oversampling} onChange={handleInputChange}>
                {[4, 8, 16, 32].map((value) => (
                  <option key={value} value={value}>
                    {value}x
                  </option>
                ))}
              </select>
            </label>
          </div>
          <button className="primary-button" onClick={runSimulation} disabled={loading}>
            {loading ? 'Simulating...' : 'Transmit & capture'}
          </button>
          {error && <p className="error-text">{error}</p>}
          {result?.inline_spectra && (
            <div className="inline-spectra">
              <h3>Inline spectra</h3>
              <ul>
                {result.inline_spectra.map((snapshot) => (
                  <li key={snapshot.stage}>
                    {snapshot.stage} - {snapshot.frequencies.length} bins
                  </li>
                ))}
              </ul>
            </div>
          )}
        </section>

        <section className="panel">
          <h2>Signal flow</h2>
          <TransceiverDiagram
            stages={availableStages}
            onInspect={handleStageInspect}
            stageLoading={stageLoading}
            decodedMessage={result?.decoded_message}
            mismatch={result?.mismatch}
            canInspect={Boolean(result)}
          />
        </section>
      </main>
      <SpectrumModal
        open={Boolean(modalStage)}
        stage={modalStage}
        detail={modalStage ? stageDetails[modalStage] : undefined}
        loading={modalStage ? stageLoading === modalStage : false}
        onClose={closeModal}
      />
    </div>
  );
}

export default App;
