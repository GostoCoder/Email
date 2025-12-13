/**
 * Service API pour la feature Suppression
 * ViewModel - Logique de présentation et communication avec l'API
 */

import axios from 'axios';
import type { SuppressionList, ApiResponse } from '../model/suppression_types';

const API_BASE_URL = '/api';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const suppressionApiService = {
  // Suppression List
  async getSuppressionList(): Promise<SuppressionList> {
    const response = await api.get('/suppression');
    return response.data;
  },

  async addToSuppressionList(email: string): Promise<ApiResponse<void>> {
    const response = await api.post('/suppression', { email });
    return response.data;
  },

  async removeFromSuppressionList(email: string): Promise<ApiResponse<void>> {
    const response = await api.delete(`/suppression/${email}`);
    return response.data;
  },
};
