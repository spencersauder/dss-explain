import { Fragment } from 'react';
import type { StageName } from '../../api/types';

const STAGE_META: Record<
  StageName,
  { title: string; description: string; annotation: string; className?: string }
> = {
  source: {
    title: 'Исходные биты',
    description: 'Поток данных',
    annotation: 'Вход',
  },
  spreader: {
    title: 'Перемножитель с ПСП',
    description: 'Генератор псевдошума',
    annotation: 'Расширение спектра',
  },
  modulator: {
    title: 'Фильтр основной полосы',
    description: 'Формирование сигнала основной полосы',
    annotation: 'Основная полоса',
  },
  channel: {
    title: 'Модулятор / канал',
    description: 'Перемножение с несущей + шум',
    annotation: 'Канал с шумом',
  },
  correlator: {
    title: 'Коррелятор',
    description: 'Сведение с опорным кодом',
    annotation: 'Приёмник',
  },
  decoder: {
    title: 'Декодер',
    description: 'Решение по битам',
    annotation: 'Выход',
  },
};

interface TransceiverDiagramProps {
  stages: StageName[];
  onInspect: (stage: StageName) => void;
  stageLoading?: StageName;
  decodedMessage?: string;
  mismatch?: boolean;
  canInspect: boolean;
  codingScheme?: string;
}

export function TransceiverDiagram({
  stages,
  onInspect,
  stageLoading,
  decodedMessage,
  mismatch,
  canInspect,
  codingScheme,
}: TransceiverDiagramProps) {
  return (
    <div className="diagram-plane">
      <div className="pipeline" role="list">
        {stages.map((stage, index) => {
          const meta = STAGE_META[stage];
          return (
            <Fragment key={stage}>
              <button
                type="button"
                className="pipeline-node"
                onClick={() => onInspect(stage)}
                disabled={!canInspect}
              >
                <span className="pipeline-node__annotation">{meta.annotation}</span>
                <span className="pipeline-node__title">{meta.title}</span>
                <span className="pipeline-node__description">{meta.description}</span>
                {stageLoading === stage && <span className="pipeline-node__status">Загрузка...</span>}
              </button>
              {index < stages.length - 1 && (
                <div className="pipeline-connector" aria-hidden="true">
                  <span />
                </div>
              )}
            </Fragment>
          );
        })}
      </div>
      <p className="diagram-hint">Нажмите любой блок, чтобы открыть его форму сигнала и спектр.</p>
      <div className="receiver-panel">
        <p className="receiver-panel__label">Принятое сообщение</p>
        <p className="receiver-panel__message">{decodedMessage || '--'}</p>
        {typeof mismatch !== 'undefined' && (
          <p className={mismatch ? 'receiver-panel__status receiver-panel__status--warn' : 'receiver-panel__status'}>
            {mismatch ? 'Секреты не совпали, данные искажены' : 'Секреты совпали, полезная нагрузка восстановлена'}
          </p>
        )}
        {codingScheme && <p className="receiver-panel__status">Кодирование: {CODING_LABELS[codingScheme] ?? codingScheme}</p>}
      </div>
    </div>
  );
}

const CODING_LABELS: Record<string, string> = {
  nrz: 'NRZ',
  manchester: 'Манчестер',
  rep3: 'Повторение ×3',
  hamming74: 'Hamming (7,4)',
};
