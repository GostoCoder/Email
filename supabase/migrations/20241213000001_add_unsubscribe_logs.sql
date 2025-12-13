-- =============================================================================
-- Migration: Ajout de la table unsubscribe_logs pour l'audit des désabonnements
-- =============================================================================

-- =============================================================================
-- Table: unsubscribe_logs
-- Description: Logs des désabonnements pour audit et support client
-- =============================================================================
CREATE TABLE IF NOT EXISTS unsubscribe_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    contact_id UUID REFERENCES contacts(id) ON DELETE SET NULL,
    campaign_id UUID REFERENCES campaigns(id) ON DELETE SET NULL,
    email VARCHAR(255) NOT NULL,
    source VARCHAR(50) NOT NULL DEFAULT 'email',
    -- Options: email (lien dans l'email), manual (admin), api (API externe)
    
    -- Informations supplémentaires
    ip_address VARCHAR(45),  -- IPv4 ou IPv6
    user_agent TEXT,
    reason TEXT,  -- Raison optionnelle fournie par l'utilisateur
    
    -- Métadonnées
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    CONSTRAINT source_check CHECK (source IN ('email', 'manual', 'api', 'import'))
);

-- Index pour les performances et recherches
CREATE INDEX idx_unsubscribe_logs_contact_id ON unsubscribe_logs(contact_id);
CREATE INDEX idx_unsubscribe_logs_campaign_id ON unsubscribe_logs(campaign_id);
CREATE INDEX idx_unsubscribe_logs_email ON unsubscribe_logs(email);
CREATE INDEX idx_unsubscribe_logs_created_at ON unsubscribe_logs(created_at DESC);
CREATE INDEX idx_unsubscribe_logs_source ON unsubscribe_logs(source);

-- =============================================================================
-- Ajouter la colonne is_active dans contacts si elle n'existe pas
-- =============================================================================
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'contacts' AND column_name = 'is_active'
    ) THEN
        ALTER TABLE contacts ADD COLUMN is_active BOOLEAN DEFAULT true;
    END IF;
END $$;

-- =============================================================================
-- Commentaires
-- =============================================================================
COMMENT ON TABLE unsubscribe_logs IS 'Historique des désabonnements pour audit et support client';
COMMENT ON COLUMN unsubscribe_logs.source IS 'Source du désabonnement: email (lien), manual (admin), api, import';
COMMENT ON COLUMN unsubscribe_logs.ip_address IS 'Adresse IP du demandeur (pour audit RGPD)';
COMMENT ON COLUMN unsubscribe_logs.user_agent IS 'User-Agent du navigateur (pour audit)';
