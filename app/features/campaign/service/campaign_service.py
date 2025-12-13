"""
Service de gestion des campagnes.
"""

import os
import uuid
from typing import List, Dict, Any, Optional
from datetime import datetime
from pathlib import Path

from app.features.campaign.model.campaign_model import Campaign
from app.core.shared.services.csv_service import CSVService
from app.core.shared.services.email_validation_service import EmailValidationService
from app.core.shared.services.email_service import email_service
from app.core.shared.services.database_service import get_db
from app.core.shared.services.token_service import TokenService
from app.core.shared.enums.status_enum import CampaignStatus, EmailStatus
from app.core.config.settings import config
from app.core.utils.logger import app_logger


class CampaignService:
    """Service pour gérer l'envoi de campagnes avec persistance Supabase."""
    
    def __init__(self):
        self.csv_service = CSVService()
        self.validation_service = EmailValidationService()
        self.token_service = TokenService(os.getenv('SECRET_KEY', 'default-secret-key'))
        self.unsubscribe_base_url = os.getenv('UNSUBSCRIBE_BASE_URL', 'http://localhost:5000')
        self.db = get_db()
        self.current_campaign: Campaign = None
    
    def create_campaign(
        self, 
        name: str, 
        subject: str, 
        template_name: str, 
        csv_file_path: str
    ) -> Campaign:
        """Crée une nouvelle campagne et la persiste dans Supabase."""
        # Lire le CSV pour compter les destinataires
        data = self.csv_service.read_file(Path(csv_file_path))
        emails = self.csv_service.extract_emails(data)
        valid_emails, _ = self.validation_service.validate_batch(emails)
        
        # Créer la campagne dans la base de données
        campaign_data = {
            'name': name,
            'subject': subject,
            'status': 'draft',
            'total_recipients': len(valid_emails)
        }
        
        # Chercher le template dans la DB
        templates = self.db.select('templates', filters={'name': template_name})
        if templates:
            campaign_data['template_id'] = templates[0]['id']
        
        result = self.db.insert('campaigns', campaign_data)
        
        if not result:
            raise Exception("Erreur lors de la création de la campagne")
        
        campaign_id = result[0]['id']
        
        # Créer ou récupérer les contacts et les lier à la campagne
        self._link_contacts_to_campaign(campaign_id, valid_emails)
        
        campaign = Campaign(
            name=name,
            subject=subject,
            template_name=template_name,
            csv_file_path=csv_file_path,
            total_recipients=len(valid_emails)
        )
        campaign.id = campaign_id
        
        app_logger.info(f"Campagne créée: {name} (ID: {campaign_id})")
        return campaign
    
    def _link_contacts_to_campaign(self, campaign_id: str, emails: List[str]):
        """Crée ou récupère les contacts et les lie à une campagne."""
        for email in emails:
            try:
                # Vérifier si le contact existe
                existing_contacts = self.db.select('contacts', filters={'email': email})
                
                if existing_contacts:
                    contact_id = existing_contacts[0]['id']
                else:
                    # Créer le contact
                    contact_result = self.db.insert('contacts', {'email': email})
                    contact_id = contact_result[0]['id']
                
                # Lier à la campagne
                self.db.insert('campaign_contacts', {
                    'campaign_id': campaign_id,
                    'contact_id': contact_id,
                    'status': 'pending'
                })
            except Exception as e:
                app_logger.error(f"Erreur liaison contact {email}: {e}")
    
    def get_campaign(self, campaign_id: str) -> Optional[Dict[str, Any]]:
        """Récupère une campagne depuis Supabase."""
        try:
            campaigns = self.db.select('campaigns', filters={'id': campaign_id})
            return campaigns[0] if campaigns else None
        except Exception as e:
            app_logger.error(f"Erreur récupération campagne: {e}")
            return None
    
    def list_campaigns(self, status: Optional[str] = None) -> List[Dict[str, Any]]:
        """Liste toutes les campagnes avec filtrage optionnel par statut."""
        try:
            filters = {'status': status} if status else None
            return self.db.select('campaigns', filters=filters)
        except Exception as e:
            app_logger.error(f"Erreur liste campagnes: {e}")
            return []
    
    def send_campaign(self, campaign_id: str) -> Dict[str, Any]:
        """Envoie une campagne d'emails depuis Supabase."""
        # Récupérer la campagne
        campaign_data = self.get_campaign(campaign_id)
        if not campaign_data:
            raise Exception("Campagne non trouvée")
        
        # Mettre à jour le statut
        self.db.update(
            'campaigns',
            {
                'status': 'in_progress',
                'started_at': datetime.now().isoformat()
            },
            {'id': campaign_id}
        )
        
        sent_count = 0
        failed_count = 0
        
        try:
            # Récupérer les destinataires via l'API Supabase
            recipients = self.db.client.rpc('get_campaign_recipients', {
                'p_campaign_id': campaign_id
            }).execute()
            
            # Si la fonction RPC n'existe pas, utiliser une requête avec select et join
            if not recipients.data:
                # Récupérer les campaign_contacts avec leurs contacts associés
                # Filtre: status=pending ET contact non désabonné (is_unsubscribed=false)
                campaign_contacts = self.db.client.table('campaign_contacts').select(
                    'id, contact_id, contacts(email, first_name, last_name, is_unsubscribed)'
                ).eq('campaign_id', campaign_id).eq('status', 'pending').execute()
                
                # Récupérer la liste de suppression pour double vérification
                suppressions = self.db.client.table('suppressions').select('email').execute()
                suppressed_emails = {s['email'].lower() for s in suppressions.data} if suppressions.data else set()
                
                # Transformer les données en excluant les désabonnés
                recipients_data = []
                for cc in campaign_contacts.data:
                    contact = cc.get('contacts', {})
                    email = contact.get('email', '').lower()
                    
                    # Exclure les contacts désabonnés ou dans la liste de suppression
                    if contact.get('is_unsubscribed', False) or email in suppressed_emails:
                        app_logger.info(f"Email {email} exclu - désabonné ou dans liste suppression")
                        continue
                    
                    recipients_data.append({
                        'campaign_contact_id': cc['id'],
                        'email': contact.get('email', ''),
                        'first_name': contact.get('first_name', ''),
                        'last_name': contact.get('last_name', ''),
                        'contact_id': cc.get('contact_id', '')
                    })
                recipients = type('obj', (object,), {'data': recipients_data})
            
            # Charger le template
            if campaign_data.get('template_id'):
                templates = self.db.select('templates', filters={'id': campaign_data['template_id']})
                template_content = {
                    'html': templates[0]['html_content'] if templates else '',
                    'text': templates[0].get('text_content', '') if templates else ''
                }
            else:
                # Fallback sur fichier template
                template_content = self._load_template(campaign_data.get('name', 'default'))
            
            # Envoyer à chaque destinataire via EmailService
            for recipient in recipients.data:
                try:
                    # Générer le token de désinscription enrichi (avec contact_id et campaign_id)
                    # Permet de tracer précisément d'où vient le désabonnement
                    unsubscribe_token = self.token_service.generate_unsubscribe_token(
                        email=recipient['email'],
                        contact_id=recipient.get('contact_id'),
                        campaign_id=campaign_id,
                        expiry_days=30
                    )
                    unsubscribe_url = f"{self.unsubscribe_base_url}/api/suppression/page/{unsubscribe_token}"
                    
                    # Préparer les données de personnalisation
                    personalization = {
                        'email': recipient.get('email', ''),
                        'first_name': recipient.get('first_name', ''),
                        'last_name': recipient.get('last_name', ''),
                        'unsubscribe_url': unsubscribe_url
                    }
                    
                    # Envoyer l'email
                    success = email_service.send_email(
                        to_email=recipient['email'],
                        subject=campaign_data['subject'],
                        html_content=template_content.get('html'),
                        text_content=template_content.get('text'),
                        from_name=config.smtp.sender_name,
                        reply_to=config.smtp.reply_to,
                        personalization_data=personalization
                    )
                    
                    if success:
                        # Mettre à jour le statut d'envoi
                        self.db.update(
                            'campaign_contacts',
                            {
                                'status': 'sent',
                                'sent_at': datetime.now().isoformat()
                            },
                            {'id': recipient['campaign_contact_id']}
                        )
                        
                        # Log événement
                        self.db.insert('email_events', {
                            'campaign_contact_id': recipient['campaign_contact_id'],
                            'event_type': 'sent'
                        })
                        
                        sent_count += 1
                        app_logger.info(f"Email envoyé à {recipient['email']}")
                    else:
                        raise Exception("Erreur lors de l'envoi via EmailService")
                        
                except Exception as e:
                    failed_count += 1
                    
                    # Mettre à jour avec l'erreur
                    self.db.update(
                        'campaign_contacts',
                        {
                            'status': 'failed',
                            'error_message': str(e)
                        },
                        {'id': recipient['campaign_contact_id']}
                    )
                    
                    app_logger.error(f"Erreur envoi à {recipient['email']}: {e}")
            
            # Mettre à jour la campagne
            self.db.update(
                'campaigns',
                {
                    'status': 'completed',
                    'sent_count': sent_count,
                    'completed_at': datetime.now().isoformat()
                },
                {'id': campaign_id}
            )
            
            status = 'completed'
            
        except Exception as e:
            status = 'failed'
            self.db.update(
                'campaigns',
                {'status': 'failed'},
                {'id': campaign_id}
            )
            app_logger.error(f"Erreur campagne: {e}")
        
        return {
            'status': status,
            'sent': sent_count,
            'failed': failed_count,
            'total': campaign_data['total_recipients']
        }
    
    def _load_template(self, template_name: str) -> Dict[str, str]:
        """Charge un template d'email depuis le système de fichiers (fallback)."""
        html_path = config.templates_dir / f"{template_name}.html"
        txt_path = config.templates_dir / f"{template_name}.txt"
        
        return {
            'html': html_path.read_text(encoding='utf-8') if html_path.exists() else '',
            'text': txt_path.read_text(encoding='utf-8') if txt_path.exists() else ''
        }


