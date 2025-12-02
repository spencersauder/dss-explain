import type { ChangeEvent } from 'react';
import { useMemo, useState } from 'react';
import './App.css';
import type { StageName } from './api/types';
import { FormField } from './components/common/FormField';
import { SpectrumComparison } from './components/common/SpectrumComparison';
import { SpectrumModal } from './components/common/SpectrumModal';
import { TransceiverDiagram } from './components/transceiver/TransceiverDiagram';
import type { SimulationFormValues } from './state/simulationStore';
import { useSimulationStore } from './state/simulationStore';

const STAGE_ORDER: StageName[] = ['source', 'spreader', 'modulator', 'channel', 'correlator', 'decoder'];
const NUMERIC_FIELDS: Array<keyof SimulationFormValues> = [
  'chip_rate',
  'carrier_freq',
  'noise_power',
  'noise_bandwidth',
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
          <p className="hero-label">Тракт DSSS</p>
          <h1>Наглядная схема передатчика и приёмника</h1>
          <p className="hero-subtitle">
            Задайте секретные фразы и параметры канала, запустите передачу и изучайте, как сигнал расширяет и сужает
            спектр на каждом блоке.
          </p>
        </div>
      </header>
      <main className="workspace">
        <section className="panel panel--diagram">
          <div className="panel-heading">
            <h2>Схема тракта</h2>
            <p>Главные узлы отображены слева направо — нажмите любой блок, чтобы увидеть его спектр.</p>
          </div>
          <TransceiverDiagram
            stages={availableStages}
            onInspect={handleStageInspect}
            stageLoading={stageLoading}
            decodedMessage={result?.decoded_message}
            mismatch={result?.mismatch}
            canInspect={Boolean(result)}
            codingScheme={result?.coding_scheme}
          />
          <SpectrumComparison
            chipRate={form.chip_rate}
            noisePower={form.noise_power}
            noiseBandwidth={form.noise_bandwidth}
            secretLength={form.tx_secret.length}
          />
        </section>
        <section className="panel panel--controls">
          <div className="panel-heading">
            <h2>Параметры передачи</h2>
            <p>Сообщение и секреты задаются в текстовых полях, остальные параметры — числовые.</p>
          </div>
          <div className="form-grid">
            <FormField label="Сообщение" name="message" value={form.message} onChange={handleInputChange} textarea />
            <FormField
              label="Секрет на передаче"
              name="tx_secret"
              value={form.tx_secret}
              onChange={handleInputChange}
              hint="Минимум 4 символа"
            />
            <FormField
              label="Секрет на приёме"
              name="rx_secret"
              value={form.rx_secret}
              onChange={handleInputChange}
              hint="Минимум 4 символа"
            />
            <FormField
              label="Частота чипов (chip/s)"
              name="chip_rate"
              type="number"
              min={10_000}
              max={1_000_000}
              step={10_000}
              value={form.chip_rate}
              onChange={handleInputChange}
            />
            <FormField
              label="Несущая (Гц)"
              name="carrier_freq"
              type="number"
              min={100_000}
              max={5_000_000}
              step={50_000}
              value={form.carrier_freq}
              onChange={handleInputChange}
            />
            <label className="form-field">
              <span className="form-label">Мощность помех (σ²)</span>
              <input
                type="range"
                min={0}
                max={20}
                step={0.5}
                name="noise_power"
                value={form.noise_power}
                onChange={handleInputChange}
              />
              <span className="slider-value">{form.noise_power.toFixed(1)}</span>
              <span className="slider-hint">Высокие значения создают заметные искажения текста.</span>
            </label>
            <label className="form-field">
              <span className="form-label">Ширина спектра помех (Гц)</span>
              <input
                type="range"
                min={5_000}
                max={500_000}
                step={5_000}
                name="noise_bandwidth"
                value={form.noise_bandwidth}
                onChange={handleInputChange}
              />
              <span className="slider-value">{(form.noise_bandwidth / 1000).toFixed(0)} кГц</span>
              <span className="slider-hint">Сравнивайте перекрытие и по ширине, и по уровню спектра.</span>
            </label>
            <label className="form-field">
              <span className="form-label">Передискретизация</span>
              <select name="oversampling" value={form.oversampling} onChange={handleInputChange}>
                {[4, 8, 16, 32].map((value) => (
                  <option key={value} value={value}>
                    {value}x
                  </option>
                ))}
              </select>
            </label>
            <label className="form-field">
              <span className="form-label">Кодирование</span>
              <select name="coding_scheme" value={form.coding_scheme} onChange={handleInputChange}>
                <option value="nrz">NRZ (базовый)</option>
                <option value="manchester">Манчестер</option>
                <option value="rep3">Повторение ×3</option>
                <option value="hamming74">Hamming (7,4)</option>
              </select>
              <span className="form-hint">
                Сравните, какая схема лучше восстанавливает сигнал при перекрытии помехой.
              </span>
            </label>
          </div>
          <button className="primary-button" onClick={runSimulation} disabled={loading}>
            {loading ? 'Передаём...' : 'Запустить передачу'}
          </button>
          {error && <p className="error-text">Ошибка симуляции: {error}</p>}
          {result?.inline_spectra && (
            <div className="inline-spectra">
              <h3>Буфер спектров</h3>
              <ul>
                {result.inline_spectra.map((snapshot) => (
                  <li key={snapshot.stage}>
                    {snapshot.stage} - {snapshot.frequencies.length} точек
                  </li>
                ))}
              </ul>
            </div>
          )}
        </section>
      </main>
      <SpectrumModal
        key={modalStage ?? 'none'}
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
