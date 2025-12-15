import { useCampaignProgress } from '../../hooks/useCampaignProgress';

interface CampaignProgressProps {
  campaignId: string;
  onComplete?: () => void;
}

export function CampaignProgressBar({ campaignId, onComplete }: CampaignProgressProps) {
  const { progress, loading, error } = useCampaignProgress({
    campaignId,
    enabled: true,
    interval: 2000,
  });

  if (loading && !progress) {
    return <div className="progress-loading">Chargement...</div>;
  }

  if (error) {
    return <div className="progress-error">Erreur: {error}</div>;
  }

  if (!progress) {
    return null;
  }

  const { status, sent_count, failed_count, total_recipients, progress_percentage, remaining, errors } = progress;

  // Call onComplete when campaign is done
  if ((status === 'completed' || status === 'failed') && onComplete) {
    setTimeout(onComplete, 1000);
  }

  return (
    <div className="campaign-progress">
      <div className="progress-header">
        <h3>Progression de l'envoi</h3>
        <span className={`status-badge status-${status}`}>{getStatusLabel(status)}</span>
      </div>

      <div className="progress-bar-wrapper">
        <div className="progress-bar">
          <div
            className="progress-bar-fill"
            style={{ width: `${progress_percentage}%` }}
          />
        </div>
        <div className="progress-percentage">{progress_percentage.toFixed(1)}%</div>
      </div>

      <div className="progress-stats">
        <div className="stat-item">
          <span className="stat-label">Total</span>
          <span className="stat-value">{total_recipients}</span>
        </div>
        <div className="stat-item stat-success">
          <span className="stat-label">Envoyés</span>
          <span className="stat-value">{sent_count}</span>
        </div>
        <div className="stat-item stat-error">
          <span className="stat-label">Échecs</span>
          <span className="stat-value">{failed_count}</span>
        </div>
        <div className="stat-item">
          <span className="stat-label">Restants</span>
          <span className="stat-value">{remaining}</span>
        </div>
      </div>

      {errors && errors.length > 0 && (
        <div className="progress-errors">
          <h4>Erreurs récentes</h4>
          <ul>
            {errors.slice(0, 5).map((err, idx) => (
              <li key={idx}>
                <strong>{err.email}</strong>: {err.error_message}
              </li>
            ))}
          </ul>
          {errors.length > 5 && (
            <p className="errors-more">...et {errors.length - 5} erreur(s) supplémentaire(s)</p>
          )}
        </div>
      )}
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
