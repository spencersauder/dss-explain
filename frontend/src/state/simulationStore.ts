import { create } from 'zustand';
import { fetchStageDetail, simulate } from '../api/client';
import type {
  SimulationRequest,
  SimulationResponse,
  StageDetailResponse,
  StageName,
} from '../api/types';

export interface SimulationFormValues {
  message: string;
  tx_secret: string;
  rx_secret: string;
  chip_rate: number;
  carrier_freq: number;
  noise_power: number;
  oversampling: number;
}

interface SimulationState {
  form: SimulationFormValues;
  result?: SimulationResponse;
  stageDetails: Partial<Record<StageName, StageDetailResponse>>;
  loading: boolean;
  stageLoading?: StageName;
  error?: string;
  setForm: (values: Partial<SimulationFormValues>) => void;
  runSimulation: () => Promise<void>;
  loadStageDetail: (stage: StageName) => Promise<StageDetailResponse | undefined>;
}

const initialForm: SimulationFormValues = {
  message: 'Привет, DSSS!',
  tx_secret: 'TX-SECRET',
  rx_secret: 'TX-SECRET',
  chip_rate: 100_000,
  carrier_freq: 1_000_000,
  noise_power: 0.0,
  oversampling: 8,
};

export const useSimulationStore = create<SimulationState>((set, get) => ({
  form: initialForm,
  stageDetails: {},
  loading: false,
  stageLoading: undefined,
  setForm: (values) => set((state) => ({ form: { ...state.form, ...values } })),
  runSimulation: async () => {
    const { form } = get();
    const payload: SimulationRequest = { ...form };

    set({ loading: true, error: undefined, stageLoading: undefined });
    try {
      const response = await simulate(payload);
      set({ result: response, stageDetails: {}, loading: false });
    } catch (error) {
      set({ error: error instanceof Error ? error.message : 'Ошибка моделирования', loading: false });
    }
  },
  loadStageDetail: async (stage: StageName) => {
    const { result, stageDetails } = get();
    if (!result) return undefined;
    if (stageDetails[stage]) return stageDetails[stage];

    set({ stageLoading: stage });
    try {
      const detail = await fetchStageDetail(result.simulation_id, stage);
      set((state) => ({
        stageDetails: { ...state.stageDetails, [stage]: detail },
        stageLoading: undefined,
      }));
      return detail;
    } catch (error) {
      set({
        error: error instanceof Error ? error.message : 'Не удалось загрузить данные участка',
        stageLoading: undefined,
      });
      return undefined;
    }
  },
}));
