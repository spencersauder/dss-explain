import type { StageName } from '../../api/types';
import { SignalCard } from '../common/SignalCard';

const STAGE_META: Record<StageName, { title: string; description: string }> = {
  source: { title: 'Source', description: 'Binary data after NRZ mapping' },
  spreader: { title: 'Spreader', description: 'Data mixed with PRN code' },
  modulator: { title: 'Modulator', description: 'Carrier upconversion output' },
  channel: { title: 'Channel', description: 'Noise + interference environment' },
  correlator: { title: 'Correlator', description: 'Matched filter output' },
  decoder: { title: 'Decoder', description: 'Recovered bitstream waveform' },
};

interface TransceiverDiagramProps {
  stages: StageName[];
  onInspect: (stage: StageName) => void;
  stageLoading?: StageName;
  decodedMessage?: string;
  mismatch?: boolean;
  canInspect: boolean;
}

export function TransceiverDiagram({
  stages,
  onInspect,
  stageLoading,
  decodedMessage,
  mismatch,
  canInspect,
}: TransceiverDiagramProps) {
  return (
    <div className="diagram">
      <div className="diagram-grid">
        {stages.map((stage) => {
          const meta = STAGE_META[stage];
          return (
            <SignalCard
              key={stage}
              title={meta.title}
              stage={stage}
              status={meta.description}
              action={
                <button
                  onClick={() => onInspect(stage)}
                  className="ghost-button"
                  disabled={!canInspect}
                >
                  {stageLoading === stage ? 'Loading...' : 'View spectrum'}
                </button>
              }
            >
              <p>Tap into the {meta.title.toLowerCase()} to inspect its waveform and amplitude spectrum.</p>
            </SignalCard>
          );
        })}
      </div>
      <div className="receiver-panel">
        <p className="receiver-panel__label">Receiver Output</p>
        <p className="receiver-panel__message">{decodedMessage || '--'}</p>
        {typeof mismatch !== 'undefined' && (
          <p className={mismatch ? 'receiver-panel__status receiver-panel__status--warn' : 'receiver-panel__status'}>
            {mismatch ? 'Secrets mismatch - data corrupted' : 'Secrets aligned - payload recovered'}
          </p>
        )}
      </div>
    </div>
  );
}
