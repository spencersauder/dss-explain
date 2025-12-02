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

export type CodingScheme = 'nrz' | 'manchester' | 'rep3' | 'hamming74';

export interface SimulationRequest {
  message: string;
  tx_secret: string;
  rx_secret: string;
  chip_rate: number;
  carrier_freq: number;
  noise_power: number;
  noise_bandwidth: number;
  oversampling: number;
  coding_scheme: CodingScheme;
}

export interface SimulationResponse {
  simulation_id: string;
  decoded_message: string;
  mismatch: boolean;
  coding_scheme: CodingScheme;
  noise_bandwidth: number;
  available_stages: StageName[];
  inline_spectra?: SpectrumSnapshot[] | null;
}

export interface StageDetailResponse {
  stage: StageName;
  waveform: WaveformSnapshot;
  spectrum: SpectrumSnapshot;
}
