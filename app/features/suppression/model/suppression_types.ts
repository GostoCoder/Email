/**
 * Types TypeScript pour la feature Suppression
 * Model - Représente les structures de données
 */

export interface SuppressionList {
  emails: string[];
  count: number;
}

export interface ApiResponse<T> {
  success: boolean;
  message?: string;
  data?: T;
}
