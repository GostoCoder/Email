/**
 * Composant React Templates
 * View - Interface utilisateur pour les templates d'emails
 * Utilise le design system Reception avec glassmorphism
 */

import React, { useEffect, useState } from 'react';
import { FileText, Eye } from 'lucide-react';
import { templatesApiService } from '../viewmodel/templates_api.service';
import type { EmailTemplate, TemplatePreview } from '../model/templates_types';
import { GlassCard, GlassButton, Spinner, Modal } from '@/core/shared/components';

const Templates: React.FC = () => {
  const [templates, setTemplates] = useState<EmailTemplate[]>([]);
  const [preview, setPreview] = useState<TemplatePreview | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    loadTemplates();
  }, []);

  const loadTemplates = async () => {
    try {
      const data = await templatesApiService.listTemplates();
      setTemplates(data.templates);
    } catch (err) {
      console.error('Erreur chargement templates:', err);
    }
  };

  const handlePreview = async (name: string) => {
    setLoading(true);
    try {
      const data = await templatesApiService.getTemplate(name);
      setPreview(data);
    } catch (err) {
      console.error('Erreur chargement template:', err);
    } finally {
      setLoading(false);
    }
  };

  const closePreview = () => {
    setPreview(null);
  };

  return (
    <div className="page">
      <div className="page-header">
        <h1 className="text-gradient">
          <FileText size={32} style={{ display: 'inline', verticalAlign: 'middle', marginRight: '0.5rem' }} />
          Templates d'Emails
        </h1>
        <p>Gérez vos templates HTML et prévisualisez-les</p>
      </div>

      <div className="templates-grid">
        {templates.map((template) => (
          <GlassCard key={template.name} className="template-card">
            <div className="template-icon">
              <FileText size={40} />
            </div>
            <h3>{template.name}</h3>
            <p className="template-subject">{template.subject}</p>
            <p className="template-date">{new Date(template.created_at).toLocaleDateString('fr-FR')}</p>
            <GlassButton
              variant="secondary"
              onClick={() => handlePreview(template.name)}
              disabled={loading}
              icon={<Eye size={16} />}
            >
              Prévisualiser
            </GlassButton>
          </GlassCard>
        ))}
      </div>

      {templates.length === 0 && (
        <GlassCard>
          <p>Aucun template disponible</p>
        </GlassCard>
      )}

      {preview && (
        <Modal
          isOpen={!!preview}
          onClose={closePreview}
          title={`Prévisualisation: ${preview.template.name}`}
          size="large"
        >
          <div className="preview-section">
            <h3>Sujet:</h3>
            <p className="preview-subject">{preview.template.subject}</p>
          </div>

          <div className="preview-html" style={{ marginTop: '1.5rem' }}>
            <iframe
              srcDoc={preview.template.html_content}
              title="Email Preview"
              style={{ 
                width: '100%', 
                height: '600px', 
                border: '1px solid var(--glass-border)',
                borderRadius: 'var(--border-radius-md)'
              }}
            />
          </div>
        </Modal>
      )}
    </div>
  );
};

export default Templates;
