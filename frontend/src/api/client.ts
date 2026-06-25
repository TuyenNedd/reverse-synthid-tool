import axios from 'axios';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_URL,
});

export type DetectionStatus = 'clean' | 'uncertain' | 'watermarked';

export interface DetectionResult {
  is_watermarked: boolean;
  status: DetectionStatus;
  confidence: number;
  phase_match: number;
  details: Record<string, unknown>;
}

export async function detectWatermark(file: File): Promise<DetectionResult> {
  const formData = new FormData();
  formData.append('file', file);
  const response = await api.post<DetectionResult>('/api/detect', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
  return response.data;
}

export async function removeWatermark(
  file: File,
  mode: 'fast' | 'full' = 'fast',
  strength?: string,
  model?: string
): Promise<Blob> {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('mode', mode);
  if (strength) formData.append('strength', strength);
  if (model) formData.append('model', model);
  const response = await api.post('/api/remove/sync', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
    responseType: 'blob',
  });
  return response.data;
}
