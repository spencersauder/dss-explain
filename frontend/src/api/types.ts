export type StageName =
  | 'source'
  | 'spreader'
  | 'modulator'
  | 'channel'
  | 'correlator'
  | 'decoder';

export interface SpectrumSnapshot {
  stage: StageName;
  frequencies: number[];
  magnitudes: number[];
  sample_rate: number;
}

export interface WaveformSnapshot {
  stage: StageName;
  samples: number[];
  sample_rate: number;
}

export interface SimulationRequest {
  message: string;
  tx_secret: string;
  rx_secret: string;
  chip_rate: number;
  carrier_freq: number;
  noise_power: number;
  oversampling: number;
}

export interface SimulationResponse {
  simulation_id: string;
  decoded_message: string;
  mismatch: boolean;
  available_stages: StageName[];
  inline_spectra?: SpectrumSnapshot[] | null;
}

export interface StageDetailResponse {
  stage: StageName;
  waveform: WaveformSnapshot;
  spectrum: SpectrumSnapshot;
}
