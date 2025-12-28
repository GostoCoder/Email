import { useState, useEffect } from 'react';
import { Campaign, CampaignStats, campaignApi } from '../../lib/campaignApi';
import { CampaignProgressBar } from './CampaignProgress';

interface CampaignDetailsProps {
  campaignId: string;
  onBack: () => void;
  onEdit: (campaign: Campaign) => void;
}

export function CampaignDetails({ campaignId, onBack, onEdit }: CampaignDetailsProps) {
  const [campaign, setCampaign] = useState<Campaign | null>(null);
  const [stats, setStats] = useState<CampaignStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [sendingTest, setSendingTest] = useState(false);
  const [testEmail, setTestEmail] = useState('');
  
  // Scheduling state
  const [showScheduleModal, setShowScheduleModal] = useState(false);
  const [scheduleDate, setScheduleDate] = useState('');
  const [scheduling, setScheduling] = useState(false);

  useEffect(() => {
    loadCampaign();
    loadStats();
  }, [campaignId]);

  const loadCampaign = async () => {
    try {
      setLoading(true);
      const data = await campaignApi.getCampaign(campaignId);
      setCampaign(data);
      if (data.scheduled_at) {
        setScheduleDate(new Date(data.scheduled_at).toISOString().slice(0, 16));
      }
    } catch (err: any) {
      setError(err.message || 'Failed to load campaign');
    } finally {
      setLoading(false);
    }
  };

  const loadStats = async () => {
    try {
      const data = await campaignApi.getCampaignStats(campaignId);
      setStats(data);
    } catch (err: any) {
      console.error('Failed to load stats:', err);
    }
  };

  const handleSendCampaign = async () => {
    if (!campaign) return;
    
    if (!confirm('Êtes-vous sûr de vouloir lancer cette campagne ?')) {
      return;
    }

    try {
      await campaignApi.sendCampaign(campaignId);
      await loadCampaign();
    } catch (err: any) {
      alert('Erreur: ' + err.message);
    }
  };

  const handleSendTest = async () => {
    if (!testEmail.trim()) {
      alert('Veuillez saisir une adresse email de test');
      return;
    }

    setSendingTest(true);
    try {
      await campaignApi.sendCampaign(campaignId, true, [testEmail]);
      alert('Email de test envoyé avec succès !');
      setTestEmail('');
    } catch (err: any) {
      alert('Erreur: ' + err.message);
    } finally {
      setSendingTest(false);
    }
  };

  const handlePause = async () => {
    try {
      await campaignApi.pauseCampaign(campaignId);
      await loadCampaign();
    } catch (err: any) {
      alert('Erreur: ' + err.message);
    }
  };

  const handleSchedule = async () => {
    if (!scheduleDate) {
      alert('Veuillez sélectionner une date et heure');
      return;
    }

    setScheduling(true);
    try {
      const scheduledAt = new Date(scheduleDate);
      
      if (campaign?.status === 'scheduled') {
        await campaignApi.rescheduleCampaign(campaignId, scheduledAt);
      } else {
        await campaignApi.scheduleCampaign(campaignId, scheduledAt);
      }
      
      await loadCampaign();
      setShowScheduleModal(false);
      alert('Campagne planifiée avec succès !');
    } catch (err: any) {
      alert('Erreur: ' + err.message);
    } finally {
      setScheduling(false);
    }
  };

  const handleCancelSchedule = async () => {
    if (!confirm('Êtes-vous sûr de vouloir annuler la planification ?')) {
      return;
    }

    try {
      await campaignApi.cancelScheduledCampaign(campaignId);
      await loadCampaign();
      alert('Planification annulée');
    } catch (err: any) {
      alert('Erreur: ' + err.message);
    }
  };

  const getMinDateTime = () => {
    const now = new Date();
    now.setMinutes(now.getMinutes() + 5);
    return now.toISOString().slice(0, 16);
  };

  const handleDelete = async () => {
    if (!confirm('Êtes-vous sûr de vouloir supprimer cette campagne ? Cette action est irréversible.')) {
      return;
    }

    try {
      await campaignApi.deleteCampaign(campaignId);
      onBack();
    } catch (err: any) {
      alert('Erreur: ' + err.message);
    }
  };

  const handleDuplicate = async () => {
    try {
      const duplicated = await campaignApi.duplicateCampaign(campaignId);
      alert(`Campagne "${duplicated.name}" créée avec succès !`);
      onBack(); // Go back to list to see the new campaign
    } catch (err: any) {
      alert('Erreur: ' + err.message);
    }
  };

  const handleExportStats = async () => {
    try {
      const blob = await campaignApi.exportCampaignStats(campaignId);
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `campaign_${campaign?.name.replace(/\s/g, '_')}_export.csv`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (err: any) {
      alert('Erreur: ' + err.message);
    }
  };

  if (loading) {
    return <div className="loading">Chargement...</div>;
  }

  if (error || !campaign) {
    return <div className="error">Erreur: {error || 'Campagne non trouvée'}</div>;
  }

  const canEdit = campaign.status === 'draft' || campaign.status === 'scheduled';
  const canSend = (campaign.status === 'draft' || campaign.status === 'scheduled') && campaign.total_recipients > 0;
  const canPause = campaign.status === 'sending';
  const canSchedule = (campaign.status === 'draft' || campaign.status === 'paused') && campaign.total_recipients > 0;
  const isScheduled = campaign.status === 'scheduled';
  const isSending = campaign.status === 'sending';

  return (
    <div className="campaign-details">
      <div className="details-header">
        <button onClick={onBack} className="btn-back">← Retour</button>
        <div className="header-actions">
          <button onClick={handleDuplicate} className="btn-secondary">
            📋 Dupliquer
          </button>
          {stats && (
            <button onClick={handleExportStats} className="btn-secondary">
              📥 Exporter CSV
            </button>
          )}
          {canEdit && (
            <button onClick={() => onEdit(campaign)} className="btn-secondary">
              ✏️ Modifier
            </button>
          )}
          {canPause && (
            <button onClick={handlePause} className="btn-warning">
              ⏸️ Pause
            </button>
          )}
          {isScheduled && (
            <button onClick={handleCancelSchedule} className="btn-warning">
              ❌ Annuler planification
            </button>
          )}
          {campaign.status === 'draft' && (
            <button onClick={handleDelete} className="btn-danger">
              🗑️ Supprimer
            </button>
          )}
        </div>
      </div>

      <div className="campaign-header">
        <h1>{campaign.name}</h1>
        <span className={`status-badge status-${campaign.status}`}>
          {getStatusLabel(campaign.status)}
        </span>
      </div>

      {/* Scheduled info banner */}
      {isScheduled && campaign.scheduled_at && (
        <div className="scheduled-banner">
          <div className="scheduled-info">
            <span className="scheduled-icon">📅</span>
            <span className="scheduled-text">
              Envoi planifié pour le <strong>{new Date(campaign.scheduled_at).toLocaleString('fr-FR', {
                weekday: 'long',
                year: 'numeric',
                month: 'long',
                day: 'numeric',
                hour: '2-digit',
                minute: '2-digit'
              })}</strong>
            </span>
          </div>
          <button onClick={() => setShowScheduleModal(true)} className="btn-secondary btn-small">
            Modifier
          </button>
        </div>
      )}

      <div className="campaign-info">
        <div className="info-grid">
          <div className="info-item">
            <span className="info-label">Sujet</span>
            <span className="info-value">{campaign.subject}</span>
          </div>
          <div className="info-item">
            <span className="info-label">De</span>
            <span className="info-value">
              {campaign.from_name} &lt;{campaign.from_email}&gt;
            </span>
          </div>
          <div className="info-item">
            <span className="info-label">Répondre à</span>
            <span className="info-value">{campaign.reply_to || campaign.from_email}</span>
          </div>
          <div className="info-item">
            <span className="info-label">Créée le</span>
            <span className="info-value">{new Date(campaign.created_at).toLocaleString('fr-FR')}</span>
          </div>
          {campaign.scheduled_at && (
            <div className="info-item">
              <span className="info-label">Planifié pour</span>
              <span className="info-value">{new Date(campaign.scheduled_at).toLocaleString('fr-FR')}</span>
            </div>
          )}
        </div>
      </div>

      {stats && (
        <div className="campaign-stats">
          <h2>Statistiques</h2>
          <div className="stats-grid">
            <div className="stat-card">
              <div className="stat-icon">📊</div>
              <div className="stat-content">
                <div className="stat-label">Total destinataires</div>
                <div className="stat-value">{stats.total_recipients}</div>
              </div>
            </div>
            <div className="stat-card stat-success">
              <div className="stat-icon">✉️</div>
              <div className="stat-content">
                <div className="stat-label">Envoyés</div>
                <div className="stat-value">{stats.sent_count}</div>
                <div className="stat-percent">{stats.delivery_rate}%</div>
              </div>
            </div>
            <div className="stat-card">
              <div className="stat-icon">📖</div>
              <div className="stat-content">
                <div className="stat-label">Ouverts</div>
                <div className="stat-value">{stats.opened_count}</div>
                <div className="stat-percent">{stats.open_rate}%</div>
              </div>
            </div>
            <div className="stat-card">
              <div className="stat-icon">🔗</div>
              <div className="stat-content">
                <div className="stat-label">Cliqués</div>
                <div className="stat-value">{stats.clicked_count}</div>
                <div className="stat-percent">{stats.click_rate}%</div>
              </div>
            </div>
            <div className="stat-card stat-error">
              <div className="stat-icon">❌</div>
              <div className="stat-content">
                <div className="stat-label">Échecs</div>
                <div className="stat-value">{stats.failed_count}</div>
              </div>
            </div>
            <div className="stat-card stat-warning">
              <div className="stat-icon">🚫</div>
              <div className="stat-content">
                <div className="stat-label">Désinscrits</div>
                <div className="stat-value">{stats.unsubscribed_count}</div>
                <div className="stat-percent">{stats.unsubscribe_rate}%</div>
              </div>
            </div>
          </div>
        </div>
      )}

      {isSending && (
        <CampaignProgressBar
          campaignId={campaignId}
          onComplete={() => {
            loadCampaign();
            loadStats();
          }}
        />
      )}

      {canSend && (
        <div className="campaign-actions">
          <div className="test-send-section">
            <h3>Envoyer un test</h3>
            <div className="test-send-form">
              <input
                type="email"
                value={testEmail}
                onChange={(e) => setTestEmail(e.target.value)}
                placeholder="votre.email@example.com"
                disabled={sendingTest}
              />
              <button
                onClick={handleSendTest}
                className="btn-secondary"
                disabled={sendingTest || !testEmail.trim()}
              >
                {sendingTest ? 'Envoi...' : 'Envoyer un test'}
              </button>
            </div>
          </div>

          <div className="send-section">
            <div className="send-buttons">
              <button onClick={handleSendCampaign} className="btn-primary btn-large">
                🚀 Lancer maintenant ({campaign.total_recipients} destinataires)
              </button>
              {canSchedule && !isScheduled && (
                <button onClick={() => setShowScheduleModal(true)} className="btn-secondary btn-large">
                  📅 Planifier l'envoi
                </button>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Schedule Modal */}
      {showScheduleModal && (
        <div className="modal-overlay" onClick={() => setShowScheduleModal(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3>📅 Planifier la campagne</h3>
              <button className="modal-close" onClick={() => setShowScheduleModal(false)}>×</button>
            </div>
            <div className="modal-body">
              <p>Choisissez la date et l'heure à laquelle vous souhaitez envoyer cette campagne.</p>
              <div className="form-group">
                <label htmlFor="schedule-date">Date et heure d'envoi</label>
                <input
                  type="datetime-local"
                  id="schedule-date"
                  value={scheduleDate}
                  onChange={(e) => setScheduleDate(e.target.value)}
                  min={getMinDateTime()}
                />
              </div>
              {scheduleDate && (
                <p className="schedule-preview">
                  L'envoi démarrera le <strong>{new Date(scheduleDate).toLocaleString('fr-FR', {
                    weekday: 'long',
                    year: 'numeric',
                    month: 'long',
                    day: 'numeric',
                    hour: '2-digit',
                    minute: '2-digit'
                  })}</strong>
                </p>
              )}
            </div>
            <div className="modal-footer">
              <button 
                onClick={() => setShowScheduleModal(false)} 
                className="btn-secondary"
                disabled={scheduling}
              >
                Annuler
              </button>
              <button 
                onClick={handleSchedule} 
                className="btn-primary"
                disabled={scheduling || !scheduleDate}
              >
                {scheduling ? 'Planification...' : isScheduled ? 'Modifier la planification' : 'Planifier'}
              </button>
            </div>
          </div>
        </div>
      )}

      <div className="campaign-content">
        <h2>Contenu de l'email</h2>
        <div className="content-preview">
          <div
            dangerouslySetInnerHTML={{ __html: campaign.html_content }}
            className="html-preview"
          />
        </div>
      </div>
    </div>
  );
}

function getStatusLabel(status: string): string {
  const labels: Record<string, string> = {
    draft: 'Brouillon',
    scheduled: 'Planifiée',
    sending: 'Envoi en cours',
    paused: 'En pause',
    completed: 'Terminée',
    failed: 'Échec',
    cancelled: 'Annulée',
  };
  return labels[status] || status;
}
