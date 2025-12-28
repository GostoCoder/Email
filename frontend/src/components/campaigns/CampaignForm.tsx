import { useState } from 'react';
import { Campaign, campaignApi } from '../../lib/campaignApi';

interface CampaignFormProps {
  campaign?: Campaign;
  onSuccess: (campaign: Campaign) => void;
  onCancel: () => void;
}

export function CampaignForm({ campaign, onSuccess, onCancel }: CampaignFormProps) {
  const [formData, setFormData] = useState({
    name: campaign?.name || '',
    subject: campaign?.subject || '',
    from_name: campaign?.from_name || '',
    from_email: campaign?.from_email || '',
    reply_to: campaign?.reply_to || '',
    html_content: campaign?.html_content || '',
    batch_size: campaign?.batch_size || 100,
    rate_limit_per_second: campaign?.rate_limit_per_second || 10,
    scheduled_at: campaign?.scheduled_at ? new Date(campaign.scheduled_at).toISOString().slice(0, 16) : '',
  });

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [enableSchedule, setEnableSchedule] = useState(!!campaign?.scheduled_at);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      // Prepare data
      const submitData: any = { ...formData };
      
      // Handle scheduled_at
      if (enableSchedule && formData.scheduled_at) {
        submitData.scheduled_at = new Date(formData.scheduled_at).toISOString();
      } else {
        delete submitData.scheduled_at;
      }

      let result: Campaign;
      if (campaign) {
        result = await campaignApi.updateCampaign(campaign.id, submitData);
      } else {
        result = await campaignApi.createCampaign(submitData);
      }
      onSuccess(result);
    } catch (err: any) {
      setError(err.message || 'Failed to save campaign');
    } finally {
      setLoading(false);
    }
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
  };

  // Get minimum datetime (now + 5 minutes)
  const getMinDateTime = () => {
    const now = new Date();
    now.setMinutes(now.getMinutes() + 5);
    return now.toISOString().slice(0, 16);
  };

  return (
    <form onSubmit={handleSubmit} className="campaign-form">
      <h2>{campaign ? 'Modifier la campagne' : 'Nouvelle campagne'}</h2>

      {error && <div className="error-message">{error}</div>}

      <div className="form-group">
        <label htmlFor="name">Nom de la campagne *</label>
        <input
          type="text"
          id="name"
          name="name"
          value={formData.name}
          onChange={handleChange}
          required
          placeholder="Ex: Newsletter Décembre 2024"
        />
      </div>

      <div className="form-group">
        <label htmlFor="subject">Sujet de l'email *</label>
        <input
          type="text"
          id="subject"
          name="subject"
          value={formData.subject}
          onChange={handleChange}
          required
          placeholder="Ex: Découvrez nos nouvelles fonctionnalités"
        />
      </div>

      <div className="form-row">
        <div className="form-group">
          <label htmlFor="from_name">Nom de l'expéditeur *</label>
          <input
            type="text"
            id="from_name"
            name="from_name"
            value={formData.from_name}
            onChange={handleChange}
            required
            placeholder="Ex: Équipe Marketing"
          />
        </div>

        <div className="form-group">
          <label htmlFor="from_email">Email de l'expéditeur *</label>
          <input
            type="email"
            id="from_email"
            name="from_email"
            value={formData.from_email}
            onChange={handleChange}
            required
            placeholder="contact@example.com"
          />
        </div>
      </div>

      <div className="form-group">
        <label htmlFor="reply_to">Email de réponse</label>
        <input
          type="email"
          id="reply_to"
          name="reply_to"
          value={formData.reply_to}
          onChange={handleChange}
          placeholder="reply@example.com (optionnel)"
        />
      </div>

      <div className="form-group">
        <label htmlFor="html_content">Contenu HTML *</label>
        <textarea
          id="html_content"
          name="html_content"
          value={formData.html_content}
          onChange={handleChange}
          required
          rows={10}
          placeholder="Contenu HTML de l'email..."
        />
        <small>Variables disponibles: {`{{firstname}}, {{lastname}}, {{company}}, {{unsubscribe_url}}`}</small>
      </div>

      <div className="form-row">
        <div className="form-group">
          <label htmlFor="batch_size">Taille du batch</label>
          <input
            type="number"
            id="batch_size"
            name="batch_size"
            value={formData.batch_size}
            onChange={handleChange}
            min="1"
            max="1000"
          />
          <small>Nombre d'emails par batch (1-1000)</small>
        </div>

        <div className="form-group">
          <label htmlFor="rate_limit_per_second">Limite d'envoi /sec</label>
          <input
            type="number"
            id="rate_limit_per_second"
            name="rate_limit_per_second"
            value={formData.rate_limit_per_second}
            onChange={handleChange}
            min="1"
            max="100"
          />
          <small>Emails par seconde (1-100)</small>
        </div>
      </div>

      <div className="form-group schedule-section">
        <div className="schedule-toggle">
          <label className="toggle-label">
            <input
              type="checkbox"
              checked={enableSchedule}
              onChange={(e) => setEnableSchedule(e.target.checked)}
            />
            <span className="toggle-text">📅 Planifier l'envoi</span>
          </label>
        </div>
        
        {enableSchedule && (
          <div className="schedule-input">
            <label htmlFor="scheduled_at">Date et heure d'envoi</label>
            <input
              type="datetime-local"
              id="scheduled_at"
              name="scheduled_at"
              value={formData.scheduled_at}
              onChange={handleChange}
              min={getMinDateTime()}
              required={enableSchedule}
            />
            <small>L'envoi démarrera automatiquement à l'heure indiquée</small>
          </div>
        )}
      </div>

      <div className="form-actions">
        <button type="button" onClick={onCancel} className="btn-secondary" disabled={loading}>
          Annuler
        </button>
        <button type="submit" className="btn-primary" disabled={loading}>
          {loading ? 'Enregistrement...' : campaign ? 'Mettre à jour' : 'Créer'}
        </button>
      </div>
    </form>
  );
}
