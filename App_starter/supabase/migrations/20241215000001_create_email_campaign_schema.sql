-- =============================================
-- Migration: Email Campaign Management System
-- Description: Tables pour gestion complète de campagnes d'emailing
-- =============================================

-- Table: campaigns
-- Gestion des campagnes d'emailing
CREATE TABLE IF NOT EXISTS campaigns (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    subject VARCHAR(500) NOT NULL,
    from_name VARCHAR(255) NOT NULL,
    from_email VARCHAR(255) NOT NULL,
    reply_to VARCHAR(255),
    template_id UUID,
    html_content TEXT NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'draft',
    -- Statuts: draft, scheduled, sending, paused, completed, failed
    scheduled_at TIMESTAMPTZ,
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    total_recipients INTEGER DEFAULT 0,
    sent_count INTEGER DEFAULT 0,
    failed_count INTEGER DEFAULT 0,
    opened_count INTEGER DEFAULT 0,
    clicked_count INTEGER DEFAULT 0,
    unsubscribed_count INTEGER DEFAULT 0,
    batch_size INTEGER DEFAULT 100,
    -- Nombre d'emails par batch
    rate_limit_per_second INTEGER DEFAULT 10,
    -- Limite d'envoi par seconde
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    created_by UUID,
    CONSTRAINT valid_status CHECK (status IN ('draft', 'scheduled', 'sending', 'paused', 'completed', 'failed', 'cancelled'))
);

-- Table: email_templates
-- Templates HTML réutilisables
CREATE TABLE IF NOT EXISTS email_templates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    html_content TEXT NOT NULL,
    variables JSONB DEFAULT '[]',
    -- Liste des variables disponibles: ["firstname", "lastname", "company"]
    thumbnail_url TEXT,
    is_default BOOLEAN DEFAULT FALSE,
    category VARCHAR(100),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    created_by UUID
);

-- Table: recipients
-- Destinataires associés à une campagne
CREATE TABLE IF NOT EXISTS recipients (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    campaign_id UUID NOT NULL REFERENCES campaigns(id) ON DELETE CASCADE,
    email VARCHAR(255) NOT NULL,
    first_name VARCHAR(255),
    last_name VARCHAR(255),
    company VARCHAR(255),
    custom_data JSONB DEFAULT '{}',
    -- Données additionnelles personnalisées
    status VARCHAR(50) NOT NULL DEFAULT 'pending',
    -- Statuts: pending, sending, sent, failed, bounced, unsubscribed
    sent_at TIMESTAMPTZ,
    opened_at TIMESTAMPTZ,
    clicked_at TIMESTAMPTZ,
    unsubscribed_at TIMESTAMPTZ,
    error_message TEXT,
    retry_count INTEGER DEFAULT 0,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    CONSTRAINT valid_recipient_status CHECK (status IN ('pending', 'sending', 'sent', 'failed', 'bounced', 'unsubscribed'))
);

-- Table: unsubscribe_list
-- Liste globale des désinscrits (respecte GDPR/CAN-SPAM)
CREATE TABLE IF NOT EXISTS unsubscribe_list (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) NOT NULL UNIQUE,
    reason TEXT,
    unsubscribed_at TIMESTAMPTZ DEFAULT NOW(),
    ip_address INET,
    user_agent TEXT,
    campaign_id UUID REFERENCES campaigns(id),
    -- Campagne à l'origine de la désinscription
    is_global BOOLEAN DEFAULT TRUE,
    -- Si true, désinscrit de toutes les futures campagnes
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Table: email_logs
-- Logs détaillés de chaque envoi
CREATE TABLE IF NOT EXISTS email_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    campaign_id UUID NOT NULL REFERENCES campaigns(id) ON DELETE CASCADE,
    recipient_id UUID NOT NULL REFERENCES recipients(id) ON DELETE CASCADE,
    email VARCHAR(255) NOT NULL,
    event_type VARCHAR(50) NOT NULL,
    -- Types: sent, delivered, opened, clicked, bounced, failed, unsubscribed
    event_data JSONB DEFAULT '{}',
    provider_message_id VARCHAR(255),
    -- ID du message chez le provider (SendGrid, Mailgun)
    error_code VARCHAR(100),
    error_message TEXT,
    timestamp TIMESTAMPTZ DEFAULT NOW(),
    metadata JSONB DEFAULT '{}',
    CONSTRAINT valid_event_type CHECK (event_type IN ('sent', 'delivered', 'opened', 'clicked', 'bounced', 'hard_bounce', 'soft_bounce', 'failed', 'unsubscribed', 'spam_report'))
);

-- Table: campaign_files
-- Stockage des fichiers CSV importés
CREATE TABLE IF NOT EXISTS campaign_files (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    campaign_id UUID NOT NULL REFERENCES campaigns(id) ON DELETE CASCADE,
    file_name VARCHAR(500) NOT NULL,
    file_path TEXT NOT NULL,
    -- Chemin dans Supabase Storage
    file_size BIGINT,
    mime_type VARCHAR(100),
    total_rows INTEGER,
    valid_rows INTEGER,
    invalid_rows INTEGER,
    status VARCHAR(50) DEFAULT 'uploaded',
    -- uploaded, processing, completed, failed
    error_message TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    processed_at TIMESTAMPTZ
);

-- =============================================
-- Index pour optimiser les performances
-- =============================================

CREATE INDEX idx_campaigns_status ON campaigns(status);
CREATE INDEX idx_campaigns_created_at ON campaigns(created_at DESC);
CREATE INDEX idx_recipients_campaign_id ON recipients(campaign_id);
CREATE INDEX idx_recipients_email ON recipients(email);
CREATE INDEX idx_recipients_status ON recipients(status);
CREATE INDEX idx_recipients_campaign_status ON recipients(campaign_id, status);
CREATE INDEX idx_unsubscribe_email ON unsubscribe_list(email);
CREATE INDEX idx_unsubscribe_global ON unsubscribe_list(is_global) WHERE is_global = TRUE;
CREATE INDEX idx_email_logs_campaign ON email_logs(campaign_id);
CREATE INDEX idx_email_logs_recipient ON email_logs(recipient_id);
CREATE INDEX idx_email_logs_event_type ON email_logs(event_type);
CREATE INDEX idx_email_logs_timestamp ON email_logs(timestamp DESC);
CREATE INDEX idx_email_logs_provider_id ON email_logs(provider_message_id);
CREATE INDEX idx_campaign_files_campaign ON campaign_files(campaign_id);
CREATE INDEX idx_templates_category ON email_templates(category);

-- =============================================
-- Fonction: Mise à jour automatique du timestamp
-- =============================================

CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Triggers pour updated_at
CREATE TRIGGER update_campaigns_updated_at BEFORE UPDATE ON campaigns
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_email_templates_updated_at BEFORE UPDATE ON email_templates
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_recipients_updated_at BEFORE UPDATE ON recipients
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- =============================================
-- Fonction: Validation email
-- =============================================

CREATE OR REPLACE FUNCTION is_valid_email(email TEXT)
RETURNS BOOLEAN AS $$
BEGIN
    RETURN email ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$';
END;
$$ LANGUAGE plpgsql IMMUTABLE;

-- =============================================
-- Fonction: Vérifier si email est désinscrit
-- =============================================

CREATE OR REPLACE FUNCTION is_email_unsubscribed(check_email TEXT)
RETURNS BOOLEAN AS $$
BEGIN
    RETURN EXISTS(
        SELECT 1 FROM unsubscribe_list
        WHERE email = check_email AND is_global = TRUE
    );
END;
$$ LANGUAGE plpgsql;

-- =============================================
-- Fonction: Mise à jour automatique des compteurs de campagne
-- =============================================

CREATE OR REPLACE FUNCTION update_campaign_stats()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'INSERT' OR TG_OP = 'UPDATE' THEN
        UPDATE campaigns
        SET 
            sent_count = (SELECT COUNT(*) FROM recipients WHERE campaign_id = NEW.campaign_id AND status = 'sent'),
            failed_count = (SELECT COUNT(*) FROM recipients WHERE campaign_id = NEW.campaign_id AND status IN ('failed', 'bounced')),
            unsubscribed_count = (SELECT COUNT(*) FROM recipients WHERE campaign_id = NEW.campaign_id AND status = 'unsubscribed')
        WHERE id = NEW.campaign_id;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_campaign_stats_trigger
AFTER INSERT OR UPDATE ON recipients
FOR EACH ROW EXECUTE FUNCTION update_campaign_stats();

-- =============================================
-- Row Level Security (RLS)
-- =============================================

ALTER TABLE campaigns ENABLE ROW LEVEL SECURITY;
ALTER TABLE email_templates ENABLE ROW LEVEL SECURITY;
ALTER TABLE recipients ENABLE ROW LEVEL SECURITY;
ALTER TABLE unsubscribe_list ENABLE ROW LEVEL SECURITY;
ALTER TABLE email_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE campaign_files ENABLE ROW LEVEL SECURITY;

-- Politique: Lecture publique pour unsubscribe_list (nécessaire pour page de désinscription)
CREATE POLICY "Allow public read on unsubscribe_list" ON unsubscribe_list
    FOR SELECT USING (TRUE);

-- Politique: Insertion publique pour unsubscribe_list (page de désinscription)
CREATE POLICY "Allow public insert on unsubscribe_list" ON unsubscribe_list
    FOR INSERT WITH CHECK (TRUE);

-- Politique: Authentification requise pour le reste (à ajuster selon votre auth)
CREATE POLICY "Authenticated users can read campaigns" ON campaigns
    FOR SELECT USING (auth.role() = 'authenticated' OR auth.role() = 'service_role');

CREATE POLICY "Authenticated users can manage campaigns" ON campaigns
    FOR ALL USING (auth.role() = 'authenticated' OR auth.role() = 'service_role');

CREATE POLICY "Authenticated users can manage templates" ON email_templates
    FOR ALL USING (auth.role() = 'authenticated' OR auth.role() = 'service_role');

CREATE POLICY "Authenticated users can manage recipients" ON recipients
    FOR ALL USING (auth.role() = 'authenticated' OR auth.role() = 'service_role');

CREATE POLICY "Service role can manage email_logs" ON email_logs
    FOR ALL USING (auth.role() = 'service_role');

CREATE POLICY "Authenticated users can read email_logs" ON email_logs
    FOR SELECT USING (auth.role() = 'authenticated' OR auth.role() = 'service_role');

CREATE POLICY "Authenticated users can manage campaign_files" ON campaign_files
    FOR ALL USING (auth.role() = 'authenticated' OR auth.role() = 'service_role');

-- =============================================
-- Données de seed: Template par défaut
-- =============================================

INSERT INTO email_templates (name, description, html_content, variables, is_default, category)
VALUES (
    'Template Simple',
    'Template basique pour campagnes marketing',
    '<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{subject}}</title>
</head>
<body style="margin: 0; padding: 0; font-family: Arial, sans-serif; background-color: #f4f4f4;">
    <table role="presentation" style="width: 100%; border-collapse: collapse;">
        <tr>
            <td align="center" style="padding: 40px 0;">
                <table role="presentation" style="width: 600px; border-collapse: collapse; background-color: #ffffff; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
                    <tr>
                        <td style="padding: 40px 30px; text-align: center; background-color: #4F46E5;">
                            <h1 style="margin: 0; color: #ffffff; font-size: 28px;">{{company}}</h1>
                        </td>
                    </tr>
                    <tr>
                        <td style="padding: 40px 30px;">
                            <p style="margin: 0 0 20px 0; font-size: 16px; line-height: 24px; color: #333333;">
                                Bonjour {{firstname}} {{lastname}},
                            </p>
                            <p style="margin: 0 0 20px 0; font-size: 16px; line-height: 24px; color: #333333;">
                                {{content}}
                            </p>
                        </td>
                    </tr>
                    <tr>
                        <td style="padding: 30px; background-color: #f8f9fa; text-align: center; border-top: 1px solid #e9ecef;">
                            <p style="margin: 0 0 10px 0; font-size: 12px; color: #6c757d;">
                                Vous recevez cet email car vous êtes inscrit à notre liste de diffusion.
                            </p>
                            <p style="margin: 0; font-size: 12px; color: #6c757d;">
                                <a href="{{unsubscribe_url}}" style="color: #4F46E5; text-decoration: underline;">Se désinscrire</a>
                            </p>
                        </td>
                    </tr>
                </table>
            </td>
        </tr>
    </table>
</body>
</html>',
    '["firstname", "lastname", "company", "content", "subject", "unsubscribe_url"]'::jsonb,
    TRUE,
    'marketing'
);

-- =============================================
-- Commentaires pour documentation
-- =============================================

COMMENT ON TABLE campaigns IS 'Campagnes d''emailing avec statuts et métriques';
COMMENT ON TABLE email_templates IS 'Templates HTML réutilisables avec variables dynamiques';
COMMENT ON TABLE recipients IS 'Destinataires des campagnes avec statuts d''envoi individuels';
COMMENT ON TABLE unsubscribe_list IS 'Liste globale des désinscrits (GDPR/CAN-SPAM compliant)';
COMMENT ON TABLE email_logs IS 'Logs détaillés de tous les événements emails';
COMMENT ON TABLE campaign_files IS 'Fichiers CSV importés pour les campagnes';
