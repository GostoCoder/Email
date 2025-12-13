/**
 * Service API pour la feature Templates
 * ViewModel - Logique de présentation et communication avec l'API
 */

import axios from 'axios';
import type { EmailTemplate, TemplatePreview } from '../model/templates_types';

const API_BASE_URL = '/api';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const templatesApiService = {
  // Templates
  async listTemplates(): Promise<{ success: boolean; templates: EmailTemplate[] }> {
    const response = await api.get('/templates/list');
    return response.data;
  },

  async getTemplate(name: string): Promise<TemplatePreview> {
    const response = await api.get(`/templates/${name}`);
    return response.data;
  },
};
