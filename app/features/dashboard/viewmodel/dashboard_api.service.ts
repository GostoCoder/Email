/**
 * Service API pour la feature Dashboard
 * ViewModel - Logique de présentation et communication avec l'API
 */

import axios from 'axios';
import type { Stats } from '../model/dashboard_types';

const API_BASE_URL = '/api';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const dashboardApiService = {
  // Dashboard & Statistics
  async getStats(): Promise<Stats> {
    const response = await api.get('/dashboard/stats');
    return response.data;
  },

  // Health check
  async healthCheck(): Promise<{ status: string; timestamp: string }> {
    const response = await api.get('/health');
    return response.data;
  },
};
