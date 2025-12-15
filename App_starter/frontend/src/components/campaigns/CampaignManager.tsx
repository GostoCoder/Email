import { useState, useEffect } from 'react';
import { Campaign, campaignApi, CSVImportResult } from '../../lib/campaignApi';
import { CampaignForm } from './CampaignForm';
import { CSVImport } from './CSVImport';
import { CampaignDetails } from './CampaignDetails';

type View = 'list' | 'create' | 'edit' | 'details' | 'import';

export function CampaignManager() {
  const [campaigns, setCampaigns] = useState<Campaign[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [view, setView] = useState<View>('list');
  const [selectedCampaign, setSelectedCampaign] = useState<Campaign | null>(null);
  const [filterStatus, setFilterStatus] = useState<string>('');

  useEffect(() => {
    loadCampaigns();
  }, [filterStatus]);

  const loadCampaigns = async () => {
    try {
      setLoading(true);
      const data = await campaignApi.getCampaigns(filterStatus || undefined);
      setCampaigns(data);
      setError(null);
    } catch (err: any) {
      setError(err.message || 'Failed to load campaigns');
    } finally {
      setLoading(false);
    }
  };

  const handleCreateSuccess = (campaign: Campaign) => {
    setCampaigns([campaign, ...campaigns]);
    setSelectedCampaign(campaign);
    setView('import');
  };

  const handleUpdateSuccess = (campaign: Campaign) => {
    setCampaigns(campaigns.map((c) => (c.id === campaign.id ? campaign : c)));
    setSelectedCampaign(campaign);
    setView('details');
  };

  const handleImportSuccess = (result: CSVImportResult) => {
    alert(`Importation réussie !\n\n✅ ${result.valid_rows} lignes importées\n❌ ${result.invalid_rows} lignes invalides\n🔁 ${result.duplicates} doublons ignorés`);
    loadCampaigns();
    setView('details');
  };

  const handleViewDetails = (campaign: Campaign) => {
    setSelectedCampaign(campaign);
    setView('details');
  };

  const handleEdit = (campaign: Campaign) => {
    setSelectedCampaign(campaign);
    setView('edit');
  };

  const handleImportRecipients = (campaign: Campaign) => {
    setSelectedCampaign(campaign);
    setView('import');
  };

  if (loading && campaigns.length === 0) {
    return <div className="loading">Chargement des campagnes...</div>;
  }

  return (
    <div className="campaign-manager">
      {view === 'list' && (
        <>
          <div className="manager-header">
            <div>
              <h1>📧 Gestion des Campagnes Email</h1>
              <p className="subtitle">Créez et gérez vos campagnes d'emailing à grande échelle</p>
            </div>
            <button onClick={() => setView('create')} className="btn-primary">
              ➕ Nouvelle campagne
            </button>
          </div>

          {error && <div className="error-message">{error}</div>}

          <div className="filter-bar">
            <select
              value={filterStatus}
              onChange={(e) => setFilterStatus(e.target.value)}
              className="filter-select"
            >
              <option value="">Tous les statuts</option>
              <option value="draft">Brouillon</option>
              <option value="scheduled">Planifiée</option>
              <option value="sending">En cours d'envoi</option>
              <option value="paused">En pause</option>
              <option value="completed">Terminée</option>
              <option value="failed">Échec</option>
            </select>
          </div>

          {campaigns.length === 0 ? (
            <div className="empty-state">
              <div className="empty-icon">📭</div>
              <h2>Aucune campagne</h2>
              <p>Créez votre première campagne d'emailing pour commencer.</p>
              <button onClick={() => setView('create')} className="btn-primary">
                Créer une campagne
              </button>
            </div>
          ) : (
            <div className="campaigns-grid">
              {campaigns.map((campaign) => (
                <div key={campaign.id} className="campaign-card">
                  <div className="card-header">
                    <h3>{campaign.name}</h3>
                    <span className={`status-badge status-${campaign.status}`}>
                      {getStatusLabel(campaign.status)}
                    </span>
                  </div>

                  <div className="card-body">
                    <p className="campaign-subject">{campaign.subject}</p>

                    <div className="campaign-meta">
                      <div className="meta-item">
                        <span className="meta-label">Destinataires:</span>
                        <span className="meta-value">{campaign.total_recipients}</span>
                      </div>
                      <div className="meta-item">
                        <span className="meta-label">Envoyés:</span>
                        <span className="meta-value">{campaign.sent_count}</span>
                      </div>
                      {campaign.failed_count > 0 && (
                        <div className="meta-item meta-error">
                          <span className="meta-label">Échecs:</span>
                          <span className="meta-value">{campaign.failed_count}</span>
                        </div>
                      )}
                    </div>

                    {campaign.status === 'sending' && (
                      <div className="mini-progress-bar">
                        <div
                          className="mini-progress-fill"
                          style={{
                            width: `${
                              campaign.total_recipients > 0
                                ? (campaign.sent_count / campaign.total_recipients) * 100
                                : 0
                            }%`,
                          }}
                        />
                      </div>
                    )}
                  </div>

                  <div className="card-footer">
                    <button
                      onClick={() => handleViewDetails(campaign)}
                      className="btn-secondary btn-small"
                    >
                      Voir détails
                    </button>
                    {campaign.status === 'draft' && (
                      <button
                        onClick={() => handleImportRecipients(campaign)}
                        className="btn-primary btn-small"
                      >
                        Importer CSV
                      </button>
                    )}
                  </div>

                  <div className="card-date">
                    Créée le {new Date(campaign.created_at).toLocaleDateString('fr-FR')}
                  </div>
                </div>
              ))}
            </div>
          )}
        </>
      )}

      {view === 'create' && (
        <div className="form-container">
          <CampaignForm
            onSuccess={handleCreateSuccess}
            onCancel={() => setView('list')}
          />
        </div>
      )}

      {view === 'edit' && selectedCampaign && (
        <div className="form-container">
          <CampaignForm
            campaign={selectedCampaign}
            onSuccess={handleUpdateSuccess}
            onCancel={() => setView('details')}
          />
        </div>
      )}

      {view === 'details' && selectedCampaign && (
        <CampaignDetails
          campaignId={selectedCampaign.id}
          onBack={() => {
            setView('list');
            loadCampaigns();
          }}
          onEdit={handleEdit}
        />
      )}

      {view === 'import' && selectedCampaign && (
        <div className="form-container">
          <CSVImport
            campaignId={selectedCampaign.id}
            onSuccess={handleImportSuccess}
            onCancel={() => setView('details')}
          />
        </div>
      )}
    </div>
  );
}

function getStatusLabel(status: string): string {
  const labels: Record<string, string> = {
    draft: 'Brouillon',
    scheduled: 'Planifiée',
    sending: 'En cours',
    paused: 'Pause',
    completed: 'Terminée',
    failed: 'Échec',
    cancelled: 'Annulée',
  };
  return labels[status] || status;
}
