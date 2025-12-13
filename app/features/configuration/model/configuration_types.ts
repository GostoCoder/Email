/**
 * Types TypeScript pour la feature Configuration
 * Model - Représente les structures de données
 */

export interface SMTPConfig {
  smtp_host: string;
  smtp_port: string;
  smtp_user: string;
  smtp_pass: string;
  sender_email: string;
  sender_name: string;
  rate_limit: string;
  max_retries: string;
  num_workers: string;
  debug_mode: string;
  test_email: string;
  unsubscribe_base_url: string;
}

export interface ApiResponse<T> {
  success: boolean;
  message?: string;
  data?: T;
}
