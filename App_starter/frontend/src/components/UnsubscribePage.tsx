import { useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import { campaignApi } from '../lib/campaignApi';

export function UnsubscribePage() {
  const [searchParams] = useSearchParams();
  const [email, setEmail] = useState(searchParams.get('email') || '');
  const [reason, setReason] = useState('');
  const [status, setStatus] = useState<'form' | 'processing' | 'success' | 'error'>('form');
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!email.trim()) {
      setError('Veuillez saisir votre adresse email');
      return;
    }

    setStatus('processing');
    setError(null);

    try {
      const campaignId = searchParams.get('campaign_id') || undefined;
      await campaignApi.unsubscribe(email, reason || undefined, campaignId);
      setStatus('success');
    } catch (err: any) {
      setError(err.message || 'Une erreur est survenue');
      setStatus('error');
    }
  };

  return (
    <div className="unsubscribe-page">
      <div className="unsubscribe-container">
        {status === 'form' && (
          <>
            <div className="unsubscribe-header">
              <h1>🔕 Se désinscrire</h1>
              <p>Nous sommes désolés de vous voir partir.</p>
            </div>

            {error && <div className="error-message">{error}</div>}

            <form onSubmit={handleSubmit} className="unsubscribe-form">
              <div className="form-group">
                <label htmlFor="email">Adresse email *</label>
                <input
                  type="email"
                  id="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="votre.email@example.com"
                  required
                  autoComplete="email"
                />
              </div>

              <div className="form-group">
                <label htmlFor="reason">Raison de la désinscription (optionnel)</label>
                <textarea
                  id="reason"
                  value={reason}
                  onChange={(e) => setReason(e.target.value)}
                  placeholder="Aidez-nous à améliorer nos communications..."
                  rows={4}
                />
              </div>

              <button type="submit" className="btn-primary btn-large">
                Confirmer la désinscription
              </button>
            </form>

            <div className="unsubscribe-info">
              <h3>Ce que cela signifie :</h3>
              <ul>
                <li>✓ Vous ne recevrez plus d'emails marketing de notre part</li>
                <li>✓ Votre demande sera traitée immédiatement</li>
                <li>✓ Vous pouvez vous réinscrire à tout moment</li>
              </ul>

              <p className="legal-notice">
                Conformément au RGPD et à la législation en vigueur, vous avez le droit de vous désinscrire
                de nos communications marketing à tout moment. Cette action n'affecte pas les emails
                transactionnels liés à vos commandes ou services.
              </p>
            </div>
          </>
        )}

        {status === 'processing' && (
          <div className="unsubscribe-processing">
            <div className="spinner"></div>
            <p>Traitement en cours...</p>
          </div>
        )}

        {status === 'success' && (
          <div className="unsubscribe-success">
            <div className="success-icon">✅</div>
            <h2>Désinscription confirmée</h2>
            <p>
              L'adresse <strong>{email}</strong> a été retirée de notre liste de diffusion.
            </p>
            <p>Vous ne recevrez plus d'emails marketing de notre part.</p>
            <div className="success-message">
              <p>Merci d'avoir été avec nous !</p>
              <p>Si vous changez d'avis, vous pouvez toujours vous réinscrire via notre site web.</p>
            </div>
          </div>
        )}

        {status === 'error' && (
          <div className="unsubscribe-error">
            <div className="error-icon">❌</div>
            <h2>Erreur</h2>
            <p>{error}</p>
            <button onClick={() => setStatus('form')} className="btn-secondary">
              Réessayer
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
