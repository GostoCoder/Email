/**
 * Types TypeScript pour la feature Campaign
 * Model - Représente les structures de données
 */

export interface CSVFile {
  filename: string;
  size: number;
  uploaded: string;
}

export interface CSVValidation {
  success: boolean;
  message: string;
  filename?: string;
  filepath?: string;
  rows?: number;
  headers?: string[];
  errors?: string[];
}

export interface EmailTemplate {
  name: string;
  filename: string;
  size: number;
}

export interface CampaignStatus {
  running: boolean;
  processed: number;
  sent: number;
  failed: number;
  invalid: number;
  stats?: string;
}

export interface ApiResponse<T> {
  success: boolean;
  message?: string;
  data?: T;
}
