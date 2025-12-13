/**
 * Types TypeScript pour la feature Dashboard
 * Model - Représente les structures de données
 */

export interface Stats {
  total_campaigns: number;
  total_sent: number;
  templates_count: number;
  suppression_count: number;
}

export interface ApiResponse<T> {
  success: boolean;
  message?: string;
  data?: T;
}
