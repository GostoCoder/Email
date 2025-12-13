/**
 * Service API pour la feature Campaign
 * ViewModel - Logique de présentation et communication avec l'API
 */

import axios from 'axios';
import type { CSVFile, CSVValidation, EmailTemplate, CampaignStatus, ApiResponse } from '../model/campaign_types';

const API_BASE_URL = '/api';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const campaignApiService = {
  // CSV Files
  async uploadCSV(file: File): Promise<CSVValidation> {
    const formData = new FormData();
    formData.append('file', file);
    const response = await api.post('/csv/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  },

  async listCSVFiles(): Promise<{ files: CSVFile[] }> {
    const response = await api.get('/csv/list');
    return response.data;
  },

  // Templates
  async listTemplates(): Promise<{ templates: EmailTemplate[] }> {
    const response = await api.get('/templates');
    return response.data;
  },

  // Campaign
  async startCampaign(csv_filename: string, template_name: string): Promise<ApiResponse<void>> {
    const response = await api.post('/campaign/start', {
      csv_filename,
      template_name,
    });
    return response.data;
  },

  async getCampaignStatus(): Promise<CampaignStatus> {
    const response = await api.get('/campaign/status');
    return response.data;
  },
};
