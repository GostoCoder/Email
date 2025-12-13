/**
 * Composant React Dashboard
 * View - Interface utilisateur pour le tableau de bord
 * Utilise le design system Reception avec glassmorphism
 */

import React, { useEffect, useState } from 'react';
import { BarChart3, Send, FileText, UserX, AlertCircle, CheckCircle } from 'lucide-react';
import { dashboardApiService } from '../viewmodel/dashboard_api.service';
import type { Stats } from '../model/dashboard_types';
import { GlassCard, Spinner, Alert } from '@/core/shared/components';

const Dashboard: React.FC = () => {
  const [stats, setStats] = useState<Stats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadStats();
  }, []);

  const loadStats = async () => {
    try {
      setLoading(true);
      const data = await dashboardApiService.getStats();
      setStats(data);
      setError(null);
    } catch (err) {
      setError('Erreur lors du chargement des statistiques');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="page">
        <Spinner label="Chargement des statistiques..." />
      </div>
    );
  }

  if (error) {
    return (
      <div className="page">
        <Alert type="error" title="Erreur">
          {error}
        </Alert>
      </div>
    );
  }

  return (
    <div className="page">
      <div className="page-header">
        <h1 className="text-gradient">
          <BarChart3 size={32} style={{ display: 'inline', verticalAlign: 'middle', marginRight: '0.5rem' }} />
          Dashboard
        </h1>
        <p>Vue d'ensemble de votre outil d'emailing</p>
      </div>

      <div className="stats-grid">
        <GlassCard className="stat-card">
          <div className="stat-icon">
            <BarChart3 size={28} color="rgb(0, 89, 96)" />
          </div>
          <div className="stat-content">
            <h3>Campagnes</h3>
            <p className="stat-value">{stats?.total_campaigns || 0}</p>
          </div>
        </GlassCard>

        <GlassCard className="stat-card">
          <div className="stat-icon">
            <Send size={28} color="rgb(0, 89, 96)" />
          </div>
          <div className="stat-content">
            <h3>Emails Envoyés</h3>
            <p className="stat-value">{stats?.total_sent || 0}</p>
          </div>
        </GlassCard>

        <GlassCard className="stat-card">
          <div className="stat-icon">
            <FileText size={28} color="rgb(255, 199, 59)" />
          </div>
          <div className="stat-content">
            <h3>Templates</h3>
            <p className="stat-value">{stats?.templates_count || 0}</p>
          </div>
        </GlassCard>

        <GlassCard className="stat-card">
          <div className="stat-icon">
            <UserX size={28} color="rgb(255, 199, 59)" />
          </div>
          <div className="stat-content">
            <h3>Liste Suppression</h3>
            <p className="stat-value">{stats?.suppression_count || 0}</p>
          </div>
        </GlassCard>
      </div>

      <GlassCard>
        <h2 className="text-gradient">Bienvenue sur votre Outil d'Emailing</h2>
        <p style={{ marginBottom: '1.5rem' }}>
          Cette application vous permet de gérer vos campagnes d'emailing de manière
          professionnelle et conforme au RGPD.
        </p>
        <div className="features-list">
          <div className="feature-item">
            <div className="feature-bullet">
              <CheckCircle size={16} />
            </div>
            <div>
              <strong>Configuration SMTP</strong>
              <p>Configurez votre serveur SMTP et testez la connexion</p>
            </div>
          </div>
          <div className="feature-item">
            <div className="feature-bullet">
              <CheckCircle size={16} />
            </div>
            <div>
              <strong>Import CSV</strong>
              <p>Uploadez vos listes de contacts au format CSV</p>
            </div>
          </div>
          <div className="feature-item">
            <div className="feature-bullet">
              <CheckCircle size={16} />
            </div>
            <div>
              <strong>Templates Personnalisables</strong>
              <p>Utilisez des templates HTML avec variables dynamiques</p>
            </div>
          </div>
          <div className="feature-item">
            <div className="feature-bullet">
              <CheckCircle size={16} />
            </div>
            <div>
              <strong>Gestion RGPD</strong>
              <p>Liste de suppression automatique et liens de désinscription</p>
            </div>
          </div>
        </div>
      </GlassCard>
    </div>
  );
};

export default Dashboard;
