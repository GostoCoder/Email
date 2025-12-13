-- =============================================================================
-- Seed Data - Données initiales pour tests et développement
-- =============================================================================

-- =============================================================================
-- Templates d'emails
-- =============================================================================
INSERT INTO templates (id, name, description, html_content, text_content, category, variables) VALUES
(
    '00000000-0000-0000-0000-000000000001',
    'Newsletter Simple',
    'Template basique pour newsletter',
    '<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>{{subject}}</title>
</head>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
    <div style="background-color: #f4f4f4; padding: 20px; text-align: center;">
        <h1 style="color: #2c3e50;">{{company_name}}</h1>
    </div>
    <div style="padding: 20px; background-color: white;">
        <p>Bonjour {{first_name}},</p>
        <div style="margin: 20px 0;">
            {{content}}
        </div>
        <p>Cordialement,<br>L''équipe {{company_name}}</p>
    </div>
    <div style="background-color: #f4f4f4; padding: 20px; text-align: center; font-size: 12px; color: #666;">
        <p>Vous recevez cet email car vous êtes inscrit à notre newsletter.</p>
        <p><a href="{{unsubscribe_url}}" style="color: #3498db;">Se désabonner</a></p>
    </div>
</body>
</html>',
    'Bonjour {{first_name}},

{{content}}

Cordialement,
L''équipe {{company_name}}

---
Se désabonner: {{unsubscribe_url}}',
    'newsletter',
    '{"first_name": "Prénom du destinataire", "company_name": "Nom de l''entreprise", "subject": "Sujet de l''email", "content": "Contenu principal", "unsubscribe_url": "Lien de désinscription"}'::jsonb
),
(
    '00000000-0000-0000-0000-000000000002',
    'Promotion',
    'Template pour emails promotionnels',
    '<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>{{subject}}</title>
</head>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
    <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 40px; text-align: center; color: white;">
        <h1 style="margin: 0; font-size: 32px;">{{title}}</h1>
        <p style="font-size: 18px; margin: 10px 0;">{{subtitle}}</p>
    </div>
    <div style="padding: 30px; background-color: white;">
        <p>Bonjour {{first_name}},</p>
        <div style="margin: 20px 0; font-size: 16px;">
            {{content}}
        </div>
        <div style="text-align: center; margin: 30px 0;">
            <a href="{{cta_url}}" style="background-color: #667eea; color: white; padding: 15px 40px; text-decoration: none; border-radius: 5px; font-weight: bold; display: inline-block;">
                {{cta_text}}
            </a>
        </div>
    </div>
    <div style="background-color: #f4f4f4; padding: 20px; text-align: center; font-size: 12px; color: #666;">
        <p><a href="{{unsubscribe_url}}" style="color: #3498db;">Se désabonner</a></p>
    </div>
</body>
</html>',
    'Bonjour {{first_name}},

{{title}}
{{subtitle}}

{{content}}

{{cta_text}}: {{cta_url}}

---
Se désabonner: {{unsubscribe_url}}',
    'promo',
    '{"first_name": "Prénom", "title": "Titre principal", "subtitle": "Sous-titre", "content": "Contenu", "cta_text": "Texte du bouton", "cta_url": "URL du bouton", "unsubscribe_url": "Lien de désinscription"}'::jsonb
);

-- =============================================================================
-- Contacts de test
-- =============================================================================
INSERT INTO contacts (email, first_name, last_name, tags, custom_fields) VALUES
('john.doe@example.com', 'John', 'Doe', ARRAY['client', 'premium'], '{"company": "Acme Corp", "interest": "technology"}'::jsonb),
('jane.smith@example.com', 'Jane', 'Smith', ARRAY['prospect'], '{"company": "Tech Inc", "interest": "marketing"}'::jsonb),
('bob.wilson@example.com', 'Bob', 'Wilson', ARRAY['client'], '{"company": "Design Studio", "interest": "design"}'::jsonb),
('alice.brown@example.com', 'Alice', 'Brown', ARRAY['client', 'vip'], '{"company": "Finance Corp", "interest": "finance"}'::jsonb),
('charlie.davis@example.com', 'Charlie', 'Davis', ARRAY['prospect'], '{"company": "Startup XYZ", "interest": "innovation"}'::jsonb);

-- =============================================================================
-- Campagne de test
-- =============================================================================
INSERT INTO campaigns (id, name, subject, template_id, status, total_recipients, scheduled_at) VALUES
(
    '00000000-0000-0000-0000-000000000101',
    'Newsletter Décembre 2024',
    'Découvrez nos nouveautés de fin d''année',
    '00000000-0000-0000-0000-000000000001',
    'draft',
    5,
    NOW() + INTERVAL '1 day'
);

-- =============================================================================
-- Association campagne-contacts pour la campagne de test
-- =============================================================================
INSERT INTO campaign_contacts (campaign_id, contact_id, status)
SELECT 
    '00000000-0000-0000-0000-000000000101',
    c.id,
    'pending'
FROM contacts c
LIMIT 5;

-- =============================================================================
-- Commentaire
-- =============================================================================
COMMENT ON TABLE templates IS 'Templates inclus: Newsletter Simple et Promotion';
COMMENT ON TABLE contacts IS '5 contacts de test ajoutés pour développement';
COMMENT ON TABLE campaigns IS '1 campagne de test en statut draft';
