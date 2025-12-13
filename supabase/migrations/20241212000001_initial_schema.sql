-- =============================================================================
-- Migration initiale - Schéma de base de données pour Outil Emailing
-- =============================================================================

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- =============================================================================
-- Table: campaigns
-- Description: Gestion des campagnes d'emailing
-- =============================================================================
CREATE TABLE IF NOT EXISTS campaigns (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    subject VARCHAR(500) NOT NULL,
    template_id UUID,
    status VARCHAR(50) NOT NULL DEFAULT 'draft',
    -- Options: draft, scheduled, in_progress, completed, failed, paused
    
    -- Statistiques
    total_recipients INTEGER DEFAULT 0,
    sent_count INTEGER DEFAULT 0,
    opened_count INTEGER DEFAULT 0,
    clicked_count INTEGER DEFAULT 0,
    bounced_count INTEGER DEFAULT 0,
    unsubscribed_count INTEGER DEFAULT 0,
    
    -- Planification
    scheduled_at TIMESTAMP WITH TIME ZONE,
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    
    -- Métadonnées
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Contraintes
    CONSTRAINT status_check CHECK (status IN ('draft', 'scheduled', 'in_progress', 'completed', 'failed', 'paused'))
);

-- Index pour les recherches fréquentes
CREATE INDEX idx_campaigns_status ON campaigns(status);
CREATE INDEX idx_campaigns_created_at ON campaigns(created_at DESC);
CREATE INDEX idx_campaigns_scheduled_at ON campaigns(scheduled_at);

-- =============================================================================
-- Table: contacts
-- Description: Liste des contacts pour les campagnes
-- =============================================================================
CREATE TABLE IF NOT EXISTS contacts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) NOT NULL UNIQUE,
    first_name VARCHAR(255),
    last_name VARCHAR(255),
    
    -- Statut
    is_active BOOLEAN DEFAULT true,
    is_unsubscribed BOOLEAN DEFAULT false,
    unsubscribed_at TIMESTAMP WITH TIME ZONE,
    
    -- Données supplémentaires (JSON pour flexibilité)
    custom_fields JSONB DEFAULT '{}',
    
    -- Métadonnées
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Tags/Segments
    tags TEXT[] DEFAULT ARRAY[]::TEXT[]
);

-- Index pour les recherches
CREATE INDEX idx_contacts_email ON contacts(email);
CREATE INDEX idx_contacts_is_active ON contacts(is_active);
CREATE INDEX idx_contacts_is_unsubscribed ON contacts(is_unsubscribed);
CREATE INDEX idx_contacts_tags ON contacts USING GIN(tags);

-- =============================================================================
-- Table: campaign_contacts
-- Description: Relation many-to-many entre campaigns et contacts
-- =============================================================================
CREATE TABLE IF NOT EXISTS campaign_contacts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    campaign_id UUID NOT NULL REFERENCES campaigns(id) ON DELETE CASCADE,
    contact_id UUID NOT NULL REFERENCES contacts(id) ON DELETE CASCADE,
    
    -- Statut d'envoi
    status VARCHAR(50) NOT NULL DEFAULT 'pending',
    -- Options: pending, sent, opened, clicked, bounced, failed, unsubscribed
    
    -- Détails d'envoi
    sent_at TIMESTAMP WITH TIME ZONE,
    opened_at TIMESTAMP WITH TIME ZONE,
    clicked_at TIMESTAMP WITH TIME ZONE,
    bounced_at TIMESTAMP WITH TIME ZONE,
    
    -- Message d'erreur en cas d'échec
    error_message TEXT,
    
    -- Métadonnées
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Contraintes
    UNIQUE(campaign_id, contact_id),
    CONSTRAINT status_check CHECK (status IN ('pending', 'sent', 'opened', 'clicked', 'bounced', 'failed', 'unsubscribed'))
);

-- Index pour les performances
CREATE INDEX idx_campaign_contacts_campaign_id ON campaign_contacts(campaign_id);
CREATE INDEX idx_campaign_contacts_contact_id ON campaign_contacts(contact_id);
CREATE INDEX idx_campaign_contacts_status ON campaign_contacts(status);

-- =============================================================================
-- Table: templates
-- Description: Templates HTML pour les emails
-- =============================================================================
CREATE TABLE IF NOT EXISTS templates (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    
    -- Contenu
    html_content TEXT NOT NULL,
    text_content TEXT,
    
    -- Variables disponibles dans le template
    variables JSONB DEFAULT '{}',
    
    -- Catégorie/Type
    category VARCHAR(100),
    
    -- Statut
    is_active BOOLEAN DEFAULT true,
    
    -- Métadonnées
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Index
CREATE INDEX idx_templates_is_active ON templates(is_active);
CREATE INDEX idx_templates_category ON templates(category);

-- =============================================================================
-- Table: suppressions
-- Description: Liste de suppression (emails à ne jamais contacter)
-- =============================================================================
CREATE TABLE IF NOT EXISTS suppressions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) NOT NULL UNIQUE,
    reason VARCHAR(100),
    -- Options: unsubscribed, bounced, complaint, manual
    
    -- Métadonnées
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    CONSTRAINT reason_check CHECK (reason IN ('unsubscribed', 'bounced', 'complaint', 'manual'))
);

-- Index
CREATE INDEX idx_suppressions_email ON suppressions(email);
CREATE INDEX idx_suppressions_reason ON suppressions(reason);

-- =============================================================================
-- Table: email_events
-- Description: Logs des événements emails (tracking)
-- =============================================================================
CREATE TABLE IF NOT EXISTS email_events (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    campaign_contact_id UUID REFERENCES campaign_contacts(id) ON DELETE CASCADE,
    event_type VARCHAR(50) NOT NULL,
    -- Options: sent, delivered, opened, clicked, bounced, complained, unsubscribed
    
    -- Détails de l'événement
    event_data JSONB DEFAULT '{}',
    
    -- Métadonnées
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    CONSTRAINT event_type_check CHECK (event_type IN ('sent', 'delivered', 'opened', 'clicked', 'bounced', 'complained', 'unsubscribed'))
);

-- Index pour les performances
CREATE INDEX idx_email_events_campaign_contact_id ON email_events(campaign_contact_id);
CREATE INDEX idx_email_events_event_type ON email_events(event_type);
CREATE INDEX idx_email_events_created_at ON email_events(created_at DESC);

-- =============================================================================
-- Fonctions de trigger pour updated_at
-- =============================================================================
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Application des triggers
CREATE TRIGGER update_campaigns_updated_at BEFORE UPDATE ON campaigns
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_contacts_updated_at BEFORE UPDATE ON contacts
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_campaign_contacts_updated_at BEFORE UPDATE ON campaign_contacts
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_templates_updated_at BEFORE UPDATE ON templates
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- =============================================================================
-- Vues utiles
-- =============================================================================

-- Vue: Statistiques des campagnes
CREATE OR REPLACE VIEW campaign_stats AS
SELECT 
    c.id,
    c.name,
    c.status,
    c.total_recipients,
    COUNT(DISTINCT CASE WHEN cc.status = 'sent' THEN cc.id END) as sent,
    COUNT(DISTINCT CASE WHEN cc.status = 'opened' THEN cc.id END) as opened,
    COUNT(DISTINCT CASE WHEN cc.status = 'clicked' THEN cc.id END) as clicked,
    COUNT(DISTINCT CASE WHEN cc.status = 'bounced' THEN cc.id END) as bounced,
    COUNT(DISTINCT CASE WHEN cc.status = 'failed' THEN cc.id END) as failed,
    c.created_at,
    c.scheduled_at,
    c.completed_at
FROM campaigns c
LEFT JOIN campaign_contacts cc ON c.id = cc.campaign_id
GROUP BY c.id, c.name, c.status, c.total_recipients, c.created_at, c.scheduled_at, c.completed_at;

-- =============================================================================
-- Politique de sécurité RLS (Row Level Security)
-- =============================================================================
-- Note: Pour l'instant, nous désactivons RLS car il n'y a pas d'authentification utilisateur
-- Dans une version future avec authentification, activez RLS avec:
-- ALTER TABLE campaigns ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE contacts ENABLE ROW LEVEL SECURITY;
-- etc.

-- =============================================================================
-- Commentaires
-- =============================================================================
COMMENT ON TABLE campaigns IS 'Table principale pour gérer les campagnes d''emailing';
COMMENT ON TABLE contacts IS 'Liste de tous les contacts/destinataires';
COMMENT ON TABLE campaign_contacts IS 'Association entre campagnes et contacts avec statut d''envoi';
COMMENT ON TABLE templates IS 'Templates HTML pour les emails';
COMMENT ON TABLE suppressions IS 'Liste de suppression globale';
COMMENT ON TABLE email_events IS 'Historique des événements emails pour le tracking';
