/**
 * Types TypeScript pour la feature Templates
 * Model - Représente les structures de données
 */

export interface EmailTemplate {
  id: string | null;
  name: string;
  subject: string;
  html_content: string;
  text_content: string;
  created_at: string;
}

export interface TemplatePreview {
  success: boolean;
  template: {
    id: string | null;
    name: string;
    subject: string;
    html_content: string;
    text_content: string;
    created_at: string;
  };
}

export interface ApiResponse<T> {
  success: boolean;
  message?: string;
  data?: T;
}
