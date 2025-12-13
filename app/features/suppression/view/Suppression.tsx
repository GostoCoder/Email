/**
 * Composant React Suppression
 * View - Interface utilisateur pour la liste de suppression
 * Utilise le design system Reception avec glassmorphism
 */

import React, { useEffect, useState } from 'react';
import { UserX, Plus, Trash2, AlertCircle, CheckCircle } from 'lucide-react';
import { suppressionApiService } from '../viewmodel/suppression_api.service';
import { GlassCard, GlassButton, GlassInput, Alert, SearchBox } from '@/core/shared/components';

const Suppression: React.FC = () => {
  const [emails, setEmails] = useState<string[]>([]);
  const [newEmail, setNewEmail] = useState('');
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

  useEffect(() => {
    loadEmails();
  }, []);

  const loadEmails = async () => {
    try {
      const data = await suppressionApiService.getSuppressionList();
      setEmails(data.emails);
    } catch (err) {
      console.error('Erreur chargement liste:', err);
    }
  };

  const handleAdd = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newEmail) return;

    setLoading(true);
    setMessage(null);

    try {
      const result = await suppressionApiService.addToSuppressionList(newEmail);
      if (result.success) {
        setMessage({ type: 'success', text: 'Email ajouté à la liste de suppression' });
        setNewEmail('');
        await loadEmails();
      }
    } catch (err: any) {
      setMessage({ type: 'error', text: err.response?.data?.message || 'Erreur ajout' });
    } finally {
      setLoading(false);
    }
  };

  const handleRemove = async (email: string) => {
    if (!confirm(`Voulez-vous vraiment retirer ${email} de la liste ?`)) return;

    try {
      await suppressionApiService.removeFromSuppressionList(email);
      setMessage({ type: 'success', text: 'Email retiré de la liste' });
      await loadEmails();
    } catch (err: any) {
      setMessage({ type: 'error', text: err.response?.data?.message || 'Erreur suppression' });
    }
  };

  return (
    <div className="page">
      <div className="page-header">
        <h1 className="text-gradient">
          <UserX size={32} style={{ display: 'inline', verticalAlign: 'middle', marginRight: '0.5rem' }} />
          Liste de Suppression
        </h1>
        <p>Gérez les adresses qui ne doivent plus recevoir d'emails (RGPD)</p>
      </div>

      {message && (
        <Alert type={message.type} title={message.type === 'success' ? 'Succès' : 'Erreur'}>
          {message.text}
        </Alert>
      )}

      <GlassCard>
        <h2>
          <Plus size={24} style={{ display: 'inline', verticalAlign: 'middle', marginRight: '0.5rem' }} />
          Ajouter un email
        </h2>
        <form onSubmit={handleAdd} className="add-email-form">
          <input
            type="email"
            className="input-glass"
            placeholder="email@exemple.com"
            value={newEmail}
            onChange={(e) => setNewEmail(e.target.value)}
            disabled={loading}
            required
          />
          <GlassButton
            type="submit"
            variant="primary"
            disabled={loading}
            icon={<Plus size={16} />}
          >
            {loading ? 'Ajout...' : 'Ajouter'}
          </GlassButton>
        </form>
      </GlassCard>

      <GlassCard>
        <h2>Liste des emails ({emails.length})</h2>
        
        {emails.length === 0 ? (
          <p className="empty-state">Aucun email dans la liste de suppression</p>
        ) : (
          <div className="email-list">
            {emails.map((email) => (
              <div key={email} className="email-item">
                <span>{email}</span>
                <GlassButton
                  variant="danger"
                  size="small"
                  onClick={() => handleRemove(email)}
                  icon={<Trash2 size={16} />}
                >
                  Supprimer
                </GlassButton>
              </div>
            ))}
          </div>
        )}
      </GlassCard>

      <GlassCard className="info-card gradient-tinted">
        <h3>ℹ️ À propos de la liste de suppression</h3>
        <p>
          La liste de suppression contient les adresses email qui ont demandé à ne plus recevoir
          de messages. Conformément au RGPD, ces adresses seront automatiquement exclues de toutes
          vos campagnes.
        </p>
        <ul>
          <li>Les désinscriptions via le lien dans les emails sont automatiquement ajoutées</li>
          <li>Vous pouvez manuellement ajouter ou retirer des adresses</li>
          <li>Cette liste est vérifiée avant chaque envoi</li>
        </ul>
      </GlassCard>
    </div>
  );
};

export default Suppression;
