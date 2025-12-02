import axios from 'axios';
import { API_BASE_URL } from '../config';
import type {
  SimulationRequest,
  SimulationResponse,
  StageDetailResponse,
  StageName,
} from './types';

const http = axios.create({
  baseURL: API_BASE_URL,
  timeout: 15000,
});

export async function simulate(payload: SimulationRequest): Promise<SimulationResponse> {
  const { data } = await http.post<SimulationResponse>('/simulate', payload);
  return data;
}

export async function fetchStageDetail(
  simulationId: string,
  stage: StageName,
): Promise<StageDetailResponse> {
  const { data } = await http.get<StageDetailResponse>(`/spectra/${stage}`, {
    params: { simulation_id: simulationId },
  });
  return data;
}
