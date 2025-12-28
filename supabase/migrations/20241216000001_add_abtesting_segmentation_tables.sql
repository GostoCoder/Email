-- Migration: Add A/B Testing, Segmentation, and Suppression Tables
-- Created: 2024-12-16
-- Description: Adds tables for A/B testing, segments, tags, and suppression list

-- ==========================================
-- A/B Testing Tables
-- ==========================================

-- A/B Tests table
CREATE TABLE IF NOT EXISTS ab_tests (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    campaign_id UUID NOT NULL REFERENCES email_campaigns(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    
    -- Test configuration
    variants JSONB NOT NULL DEFAULT '[]'::jsonb,
    traffic_split JSONB NOT NULL DEFAULT '{}'::jsonb,
    
    -- Metrics to track
    primary_metric VARCHAR(50) DEFAULT 'open_rate',
    
    -- Test status
    status VARCHAR(50) DEFAULT 'draft',
    winner_variant VARCHAR(50),
    
    -- Auto-winner settings
    auto_select_winner BOOLEAN DEFAULT false,
    min_sample_size INTEGER DEFAULT 100,
    confidence_level FLOAT DEFAULT 0.95,
    
    -- Timestamps
    started_at TIMESTAMPTZ,
    ended_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- A/B Test Assignments (which variant a recipient got)
CREATE TABLE IF NOT EXISTS ab_test_assignments (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    ab_test_id UUID NOT NULL REFERENCES ab_tests(id) ON DELETE CASCADE,
    recipient_id UUID NOT NULL REFERENCES email_recipients(id) ON DELETE CASCADE,
    variant VARCHAR(50) NOT NULL,
    assigned_at TIMESTAMPTZ DEFAULT NOW(),
    
    UNIQUE(ab_test_id, recipient_id)
);

-- ==========================================
-- Segmentation Tables
-- ==========================================

-- Segments table
CREATE TABLE IF NOT EXISTS segments (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    
    -- Segment type: static (manual) or dynamic (filter-based)
    segment_type VARCHAR(50) DEFAULT 'dynamic',
    
    -- Filter rules for dynamic segments
    filters JSONB,
    
    -- Tags for organization
    tags TEXT[] DEFAULT '{}',
    
    -- Cached recipient count
    recipient_count INTEGER DEFAULT 0,
    
    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Static segment members (for static segments)
CREATE TABLE IF NOT EXISTS segment_members (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    segment_id UUID NOT NULL REFERENCES segments(id) ON DELETE CASCADE,
    email VARCHAR(255) NOT NULL,
    added_at TIMESTAMPTZ DEFAULT NOW(),
    
    UNIQUE(segment_id, email)
);

-- Tags table
CREATE TABLE IF NOT EXISTS tags (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    color VARCHAR(7) DEFAULT '#6B7280',
    description TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Recipient tags (many-to-many)
CREATE TABLE IF NOT EXISTS recipient_tags (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    recipient_id UUID NOT NULL REFERENCES email_recipients(id) ON DELETE CASCADE,
    tag_id UUID NOT NULL REFERENCES tags(id) ON DELETE CASCADE,
    added_at TIMESTAMPTZ DEFAULT NOW(),
    
    UNIQUE(recipient_id, tag_id)
);

-- ==========================================
-- Suppression List Table
-- ==========================================

CREATE TABLE IF NOT EXISTS suppression_list (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    email VARCHAR(255) NOT NULL UNIQUE,
    
    -- Source of suppression
    source VARCHAR(100) NOT NULL,
    
    -- Reason for suppression
    reason VARCHAR(255),
    
    -- Related campaign (if applicable)
    campaign_id UUID REFERENCES email_campaigns(id) ON DELETE SET NULL,
    
    -- Timestamps
    suppressed_at TIMESTAMPTZ DEFAULT NOW(),
    
    -- Optional expiry (for temporary suppression)
    expires_at TIMESTAMPTZ
);

-- ==========================================
-- Bounce Tracking Table
-- ==========================================

CREATE TABLE IF NOT EXISTS bounce_events (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    email VARCHAR(255) NOT NULL,
    
    -- Bounce classification
    bounce_type VARCHAR(50) NOT NULL,
    bounce_subtype VARCHAR(100),
    
    -- Message info
    message_id VARCHAR(255),
    campaign_id UUID REFERENCES email_campaigns(id) ON DELETE SET NULL,
    
    -- Provider info
    provider VARCHAR(50),
    raw_event JSONB,
    
    -- Timestamps
    bounced_at TIMESTAMPTZ DEFAULT NOW()
);

-- Email opens tracking (for webhook-reported opens)
CREATE TABLE IF NOT EXISTS email_opens (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    email VARCHAR(255) NOT NULL,
    campaign_id UUID REFERENCES email_campaigns(id) ON DELETE SET NULL,
    
    -- Tracking info
    user_agent TEXT,
    ip_address INET,
    
    -- Timestamps
    opened_at TIMESTAMPTZ DEFAULT NOW()
);

-- Email clicks tracking (for webhook-reported clicks)
CREATE TABLE IF NOT EXISTS email_clicks (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    email VARCHAR(255) NOT NULL,
    url TEXT NOT NULL,
    campaign_id UUID REFERENCES email_campaigns(id) ON DELETE SET NULL,
    
    -- Tracking info
    user_agent TEXT,
    ip_address INET,
    
    -- Timestamps
    clicked_at TIMESTAMPTZ DEFAULT NOW()
);

-- ==========================================
-- Indexes for Performance
-- ==========================================

-- A/B Testing indexes
CREATE INDEX IF NOT EXISTS idx_ab_tests_campaign ON ab_tests(campaign_id);
CREATE INDEX IF NOT EXISTS idx_ab_tests_status ON ab_tests(status);
CREATE INDEX IF NOT EXISTS idx_ab_test_assignments_test ON ab_test_assignments(ab_test_id);
CREATE INDEX IF NOT EXISTS idx_ab_test_assignments_recipient ON ab_test_assignments(recipient_id);
CREATE INDEX IF NOT EXISTS idx_ab_test_assignments_variant ON ab_test_assignments(variant);

-- Segmentation indexes
CREATE INDEX IF NOT EXISTS idx_segments_type ON segments(segment_type);
CREATE INDEX IF NOT EXISTS idx_segments_tags ON segments USING GIN(tags);
CREATE INDEX IF NOT EXISTS idx_segment_members_segment ON segment_members(segment_id);
CREATE INDEX IF NOT EXISTS idx_segment_members_email ON segment_members(email);
CREATE INDEX IF NOT EXISTS idx_recipient_tags_recipient ON recipient_tags(recipient_id);
CREATE INDEX IF NOT EXISTS idx_recipient_tags_tag ON recipient_tags(tag_id);

-- Suppression list indexes
CREATE INDEX IF NOT EXISTS idx_suppression_email ON suppression_list(email);
CREATE INDEX IF NOT EXISTS idx_suppression_source ON suppression_list(source);
CREATE INDEX IF NOT EXISTS idx_suppression_expires ON suppression_list(expires_at) WHERE expires_at IS NOT NULL;

-- Bounce events indexes
CREATE INDEX IF NOT EXISTS idx_bounce_events_email ON bounce_events(email);
CREATE INDEX IF NOT EXISTS idx_bounce_events_campaign ON bounce_events(campaign_id);
CREATE INDEX IF NOT EXISTS idx_bounce_events_type ON bounce_events(bounce_type);
CREATE INDEX IF NOT EXISTS idx_bounce_events_bounced_at ON bounce_events(bounced_at);

-- Email tracking indexes
CREATE INDEX IF NOT EXISTS idx_email_opens_email ON email_opens(email);
CREATE INDEX IF NOT EXISTS idx_email_opens_campaign ON email_opens(campaign_id);
CREATE INDEX IF NOT EXISTS idx_email_opens_opened_at ON email_opens(opened_at);
CREATE INDEX IF NOT EXISTS idx_email_clicks_email ON email_clicks(email);
CREATE INDEX IF NOT EXISTS idx_email_clicks_campaign ON email_clicks(campaign_id);
CREATE INDEX IF NOT EXISTS idx_email_clicks_url ON email_clicks(url);

-- ==========================================
-- Row Level Security (RLS)
-- ==========================================

-- Enable RLS on new tables
ALTER TABLE ab_tests ENABLE ROW LEVEL SECURITY;
ALTER TABLE ab_test_assignments ENABLE ROW LEVEL SECURITY;
ALTER TABLE segments ENABLE ROW LEVEL SECURITY;
ALTER TABLE segment_members ENABLE ROW LEVEL SECURITY;
ALTER TABLE tags ENABLE ROW LEVEL SECURITY;
ALTER TABLE recipient_tags ENABLE ROW LEVEL SECURITY;
ALTER TABLE suppression_list ENABLE ROW LEVEL SECURITY;
ALTER TABLE bounce_events ENABLE ROW LEVEL SECURITY;
ALTER TABLE email_opens ENABLE ROW LEVEL SECURITY;
ALTER TABLE email_clicks ENABLE ROW LEVEL SECURITY;

-- Create policies for service role access
CREATE POLICY "Service role can manage ab_tests" ON ab_tests
    FOR ALL USING (true) WITH CHECK (true);

CREATE POLICY "Service role can manage ab_test_assignments" ON ab_test_assignments
    FOR ALL USING (true) WITH CHECK (true);

CREATE POLICY "Service role can manage segments" ON segments
    FOR ALL USING (true) WITH CHECK (true);

CREATE POLICY "Service role can manage segment_members" ON segment_members
    FOR ALL USING (true) WITH CHECK (true);

CREATE POLICY "Service role can manage tags" ON tags
    FOR ALL USING (true) WITH CHECK (true);

CREATE POLICY "Service role can manage recipient_tags" ON recipient_tags
    FOR ALL USING (true) WITH CHECK (true);

CREATE POLICY "Service role can manage suppression_list" ON suppression_list
    FOR ALL USING (true) WITH CHECK (true);

CREATE POLICY "Service role can manage bounce_events" ON bounce_events
    FOR ALL USING (true) WITH CHECK (true);

CREATE POLICY "Service role can manage email_opens" ON email_opens
    FOR ALL USING (true) WITH CHECK (true);

CREATE POLICY "Service role can manage email_clicks" ON email_clicks
    FOR ALL USING (true) WITH CHECK (true);

-- ==========================================
-- Functions
-- ==========================================

-- Function to update segment recipient count
CREATE OR REPLACE FUNCTION update_segment_count()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'INSERT' OR TG_OP = 'DELETE' THEN
        UPDATE segments 
        SET 
            recipient_count = (
                SELECT COUNT(*) FROM segment_members 
                WHERE segment_id = COALESCE(NEW.segment_id, OLD.segment_id)
            ),
            updated_at = NOW()
        WHERE id = COALESCE(NEW.segment_id, OLD.segment_id);
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger to auto-update segment count
DROP TRIGGER IF EXISTS trigger_update_segment_count ON segment_members;
CREATE TRIGGER trigger_update_segment_count
AFTER INSERT OR DELETE ON segment_members
FOR EACH ROW EXECUTE FUNCTION update_segment_count();

-- Function to check suppression before sending
CREATE OR REPLACE FUNCTION is_email_suppressed(check_email VARCHAR)
RETURNS BOOLEAN AS $$
BEGIN
    RETURN EXISTS (
        SELECT 1 FROM suppression_list 
        WHERE email = check_email 
        AND (expires_at IS NULL OR expires_at > NOW())
    );
END;
$$ LANGUAGE plpgsql;

-- Function to get bounce count for email
CREATE OR REPLACE FUNCTION get_bounce_count(check_email VARCHAR, days INTEGER DEFAULT 30)
RETURNS INTEGER AS $$
BEGIN
    RETURN (
        SELECT COUNT(*) FROM bounce_events 
        WHERE email = check_email 
        AND bounced_at > NOW() - (days || ' days')::INTERVAL
    );
END;
$$ LANGUAGE plpgsql;
