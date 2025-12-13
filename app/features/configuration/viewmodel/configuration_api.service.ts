/**
 * Service API pour la feature Configuration
 * ViewModel - Logique de présentation et communication avec l'API
 */

import axios from 'axios';
import type { SMTPConfig, ApiResponse } from '../model/configuration_types';

const API_BASE_URL = '/api';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const configurationApiService = {
  // Configuration
  async getConfig(): Promise<SMTPConfig> {
    const response = await api.get('/configuration/get');
    return response.data;
  },

  async saveConfig(config: SMTPConfig): Promise<ApiResponse<void>> {
    const response = await api.post('/configuration/update', config);
    return response.data;
  },

  async testSMTP(): Promise<ApiResponse<void>> {
    const response = await api.post('/configuration/test-smtp');
    return response.data;
  },
};
