/**
 * Composant React Configuration
 * View - Interface utilisateur pour la configuration SMTP
 * Utilise le design system Reception avec glassmorphism
 */

import React, { useEffect, useState } from 'react';
import { Settings, CheckCircle, XCircle } from 'lucide-react';
import { configurationApiService } from '../viewmodel/configuration_api.service';
import type { SMTPConfig } from '../model/configuration_types';
import { GlassCard, GlassButton, GlassInput, Alert, Toggle } from '@/core/shared/components';

const Configuration: React.FC = () => {
  const [config, setConfig] = useState<SMTPConfig>({
    smtp_host: '',
    smtp_port: '587',
    smtp_user: '',
    smtp_pass: '',
    sender_email: '',
    sender_name: '',
    rate_limit: '20',
    max_retries: '3',
    num_workers: '4',
    debug_mode: 'false',
    test_email: '',
    unsubscribe_base_url: 'http://localhost:5000',
  });

  const [loading, setLoading] = useState(false);
  const [testing, setTesting] = useState(false);
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

  useEffect(() => {
    loadConfig();
  }, []);

  const loadConfig = async () => {
    try {
      const data = await configurationApiService.getConfig();
      setConfig(data);
    } catch (err) {
      console.error('Erreur chargement config:', err);
    }
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const { name, value } = e.target;
    setConfig(prev => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setMessage(null);

    try {
      const result = await configurationApiService.saveConfig(config);
      setMessage({ type: 'success', text: result.message || 'Configuration sauvegardée !' });
    } catch (err: any) {
      setMessage({ type: 'error', text: err.response?.data?.message || 'Erreur de sauvegarde' });
    } finally {
      setLoading(false);
    }
  };

  const handleTest = async () => {
    setTesting(true);
    setMessage(null);

    try {
      const result = await configurationApiService.testSMTP();
      setMessage({ type: 'success', text: result.message || 'Connexion SMTP réussie !' });
    } catch (err: any) {
      setMessage({ type: 'error', text: err.response?.data?.message || 'Échec de la connexion SMTP' });
    } finally {
      setTesting(false);
    }
  };

  return (
    <div className="page">
      <div className="page-header">
        <h1 className="text-gradient">
          <Settings size={32} style={{ display: 'inline', verticalAlign: 'middle', marginRight: '0.5rem' }} />
          Configuration SMTP
        </h1>
        <p>Configurez les paramètres d'envoi d'emails</p>
      </div>

      {message && (
        <Alert type={message.type} title={message.type === 'success' ? 'Succès' : 'Erreur'}>
          {message.text}
        </Alert>
      )}

      <form onSubmit={handleSubmit}>
        <GlassCard>
          <h2>Paramètres SMTP</h2>
          
          <div className="form-grid">
            <div className="form-group">
              <label htmlFor="smtp_host">Hôte SMTP *</label>
              <input
                type="text"
                id="smtp_host"
                name="smtp_host"
                value={config.smtp_host}
                onChange={handleChange}
                placeholder="smtp.gmail.com"
                required
              />
            </div>

            <div className="form-group">
              <label htmlFor="smtp_port">Port SMTP *</label>
              <input
                type="number"
                id="smtp_port"
                name="smtp_port"
                value={config.smtp_port}
                onChange={handleChange}
                placeholder="587"
                required
              />
            </div>

            <div className="form-group">
              <label htmlFor="smtp_user">Utilisateur SMTP *</label>
              <input
                type="text"
                id="smtp_user"
                name="smtp_user"
                value={config.smtp_user}
                onChange={handleChange}
                placeholder="votre@email.com"
                required
              />
            </div>

            <div className="form-group">
              <label htmlFor="smtp_pass">Mot de passe SMTP *</label>
              <input
                type="password"
                id="smtp_pass"
                name="smtp_pass"
                value={config.smtp_pass}
                onChange={handleChange}
                placeholder="••••••••"
                required
              />
            </div>

            <div className="form-group">
              <label htmlFor="sender_email">Email expéditeur *</label>
              <input
                type="email"
                id="sender_email"
                name="sender_email"
                value={config.sender_email}
                onChange={handleChange}
                placeholder="votre@email.com"
                required
              />
            </div>

            <div className="form-group">
              <label htmlFor="sender_name">Nom expéditeur</label>
              <input
                type="text"
                id="sender_name"
                name="sender_name"
                value={config.sender_name}
                onChange={handleChange}
                placeholder="Votre Nom"
              />
            </div>
          </div>
        </GlassCard>

        <GlassCard>
          <h2>Paramètres avancés</h2>
          
          <div className="form-grid">
            <div className="form-group">
              <label htmlFor="rate_limit">Limite par minute</label>
              <input
                type="number"
                id="rate_limit"
                name="rate_limit"
                value={config.rate_limit}
                onChange={handleChange}
                min="1"
                max="100"
              />
              <small>Nombre maximum d'emails par minute</small>
            </div>

            <div className="form-group">
              <label htmlFor="max_retries">Tentatives max</label>
              <input
                type="number"
                id="max_retries"
                name="max_retries"
                value={config.max_retries}
                onChange={handleChange}
                min="1"
                max="10"
              />
              <small>Nombre de tentatives en cas d'échec</small>
            </div>

            <div className="form-group">
              <label htmlFor="num_workers">Workers</label>
              <input
                type="number"
                id="num_workers"
                name="num_workers"
                value={config.num_workers}
                onChange={handleChange}
                min="1"
                max="10"
              />
              <small>Nombre de threads d'envoi</small>
            </div>

            <div className="form-group">
              <label htmlFor="unsubscribe_base_url">URL de désinscription</label>
              <input
                type="url"
                id="unsubscribe_base_url"
                name="unsubscribe_base_url"
                value={config.unsubscribe_base_url}
                onChange={handleChange}
                placeholder="http://localhost:5000"
              />
            </div>

            <div className="form-group">
              <label htmlFor="debug_mode">Mode debug</label>
              <select
                id="debug_mode"
                name="debug_mode"
                value={config.debug_mode}
                onChange={handleChange}
              >
                <option value="false">Non</option>
                <option value="true">Oui</option>
              </select>
              <small>Limite l'envoi à quelques emails de test</small>
            </div>

            <div className="form-group">
              <label htmlFor="test_email">Email de test</label>
              <input
                type="email"
                id="test_email"
                name="test_email"
                value={config.test_email}
                onChange={handleChange}
                placeholder="test@email.com"
              />
              <small>Remplace tous les destinataires en mode debug</small>
            </div>
          </div>
        </GlassCard>

        <div className="button-group">
          <GlassButton
            type="submit"
            variant="primary"
            disabled={loading}
          >
            {loading ? 'Sauvegarde...' : 'Sauvegarder la configuration'}
          </GlassButton>
          <GlassButton
            type="button"
            variant="secondary"
            onClick={handleTest}
            disabled={testing}
          >
            {testing ? 'Test en cours...' : 'Tester la connexion SMTP'}
          </GlassButton>
        </div>
      </form>
    </div>
  );
};

export default Configuration;
