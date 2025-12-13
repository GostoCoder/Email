/**
 * Composant React Campaign
 * View - Interface utilisateur pour la gestion de campagnes
 * Utilise le design system Reception avec glassmorphism
 */

import React, { useEffect, useState } from 'react';
import { Send, Upload, Play, CheckCircle, AlertCircle } from 'lucide-react';
import { campaignApiService } from '../viewmodel/campaign_api.service';
import type { CSVFile, EmailTemplate, CampaignStatus } from '../model/campaign_types';
import { GlassCard, GlassButton, Alert } from '@/core/shared/components';

const Campaign: React.FC = () => {
  const [csvFiles, setCSVFiles] = useState<CSVFile[]>([]);
  const [templates, setTemplates] = useState<EmailTemplate[]>([]);
  const [selectedCSV, setSelectedCSV] = useState<string>('');
  const [selectedTemplate, setSelectedTemplate] = useState<string>('default');
  const [uploading, setUploading] = useState(false);
  const [campaignRunning, setCampaignRunning] = useState(false);
  const [status, setStatus] = useState<CampaignStatus | null>(null);
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

  useEffect(() => {
    loadData();
    const interval = setInterval(loadStatus, 2000);
    return () => clearInterval(interval);
  }, []);

  const loadData = async () => {
    try {
      const [csvData, templateData] = await Promise.all([
        campaignApiService.listCSVFiles(),
        campaignApiService.listTemplates(),
      ]);
      setCSVFiles(csvData.files);
      setTemplates(templateData.templates);
    } catch (err) {
      console.error('Erreur chargement données:', err);
    }
  };

  const loadStatus = async () => {
    try {
      const statusData = await campaignApiService.getCampaignStatus();
      setStatus(statusData);
      setCampaignRunning(statusData.running);
    } catch (err) {
      console.error('Erreur chargement statut:', err);
    }
  };

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setUploading(true);
    setMessage(null);

    try {
      const result = await campaignApiService.uploadCSV(file);
      if (result.success) {
        setMessage({ type: 'success', text: `Fichier validé: ${result.rows} lignes` });
        setSelectedCSV(result.filename!);
        await loadData();
      } else {
        setMessage({ type: 'error', text: result.message });
      }
    } catch (err: any) {
      setMessage({ type: 'error', text: err.response?.data?.message || 'Erreur upload' });
    } finally {
      setUploading(false);
      e.target.value = '';
    }
  };

  const handleStartCampaign = async () => {
    if (!selectedCSV) {
      setMessage({ type: 'error', text: 'Veuillez sélectionner un fichier CSV' });
      return;
    }

    setMessage(null);

    try {
      const result = await campaignApiService.startCampaign(selectedCSV, selectedTemplate);
      if (result.success) {
        setMessage({ type: 'success', text: 'Campagne démarrée !' });
        setCampaignRunning(true);
      }
    } catch (err: any) {
      setMessage({ type: 'error', text: err.response?.data?.message || 'Erreur démarrage' });
    }
  };

  return (
    <div className="page">
      <div className="page-header">
        <h1 className="text-gradient">
          <Send size={32} style={{ display: 'inline', verticalAlign: 'middle', marginRight: '0.5rem' }} />
          Gestion de Campagne
        </h1>
        <p>Créez et lancez vos campagnes d'emailing</p>
      </div>

      {message && (
        <Alert type={message.type} title={message.type === 'success' ? 'Succès' : 'Erreur'}>
          {message.text}
        </Alert>
      )}

      {campaignRunning && status && (
        <Alert type="info" title="Campagne en cours...">
          <p>
            Traités: {status.processed} | Envoyés: {status.sent} | Échoués: {status.failed} | Invalides: {status.invalid}
          </p>
        </Alert>
      )}

      <GlassCard>
        <h2>
          <Upload size={24} style={{ display: 'inline', verticalAlign: 'middle', marginRight: '0.5rem' }} />
          1. Upload du fichier CSV
        </h2>
        <p style={{ marginBottom: '1.5rem' }}>Importez votre liste de contacts au format CSV</p>
        
        <div className="file-upload">
          <input
            type="file"
            id="csv-file"
            accept=".csv"
            onChange={handleFileUpload}
            disabled={uploading || campaignRunning}
          />
          <label htmlFor="csv-file">
            <GlassButton variant="secondary" disabled={uploading || campaignRunning}>
              {uploading ? 'Upload en cours...' : 'Choisir un fichier CSV'}
            </GlassButton>
          </label>
        </div>

        {csvFiles.length > 0 && (
          <div className="file-list">
            <h3>Fichiers disponibles:</h3>
            {csvFiles.map((file) => (
              <div
                key={file.filename}
                className={`file-item ${selectedCSV === file.filename ? 'selected' : ''}`}
                onClick={() => !campaignRunning && setSelectedCSV(file.filename)}
              >
                <div>
                  <strong>{file.filename}</strong>
                  <p>Taille: {(file.size / 1024).toFixed(2)} KB</p>
                </div>
                {selectedCSV === file.filename && <CheckCircle size={20} color="rgb(0, 89, 96)" />}
              </div>
            ))}
          </div>
        )}
      </GlassCard>

      <GlassCard>
        <h2>2. Sélection du template</h2>
        <p style={{ marginBottom: '1.5rem' }}>Choisissez le template d'email à utiliser</p>

        <div className="form-group">
          <label htmlFor="template">Template:</label>
          <select
            id="template"
            className="input-glass"
            value={selectedTemplate}
            onChange={(e) => setSelectedTemplate(e.target.value)}
            disabled={campaignRunning}
          >
            {templates.map((template) => (
              <option key={template.name} value={template.name}>
                {template.name}
              </option>
            ))}
          </select>
        </div>
      </GlassCard>

      <GlassCard>
        <h2>3. Lancement de la campagne</h2>
        <p style={{ marginBottom: '1.5rem' }}>Vérifiez vos paramètres et lancez l'envoi</p>

        <div className="campaign-summary">
          <div className="summary-item">
            <strong>Fichier CSV:</strong>
            <span>{selectedCSV || 'Aucun fichier sélectionné'}</span>
          </div>
          <div className="summary-item">
            <strong>Template:</strong>
            <span>{selectedTemplate}</span>
          </div>
        </div>

        <GlassButton
          variant="primary"
          size="large"
          onClick={handleStartCampaign}
          disabled={!selectedCSV || campaignRunning}
          icon={<Play size={20} />}
        >
          {campaignRunning ? 'Campagne en cours...' : 'Démarrer la campagne'}
        </GlassButton>
      </GlassCard>

      {status?.stats && (
        <GlassCard className="gradient-tinted">
          <h2>Rapport de campagne</h2>
          <pre className="stats-report">{status.stats}</pre>
        </GlassCard>
      )}
    </div>
  );
};

export default Campaign;
