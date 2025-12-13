"""
Service d'envoi d'emails avec support pour Proton Mail via SMTP.

Ce service gère l'envoi d'emails via SMTP, optimisé pour Proton Mail mais compatible
avec d'autres fournisseurs SMTP.

Méthodes supportées:
- SMTP avec STARTTLS (recommandé pour Proton Mail)
- SMTP avec SSL
- Authentification PLAIN/LOGIN

Configuration Proton Mail:
- Serveur: smtp.protonmail.ch
- Port: 587 (STARTTLS)
- Authentification: Jeton SMTP généré depuis les paramètres Proton Mail
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, Any, Optional, List
from datetime import datetime

from app.core.config.settings import config
from app.core.utils.logger import app_logger


class EmailService:
    """Service pour l'envoi d'emails via SMTP (optimisé pour Proton Mail)."""
    
    def __init__(self):
        """Initialise le service email avec la configuration SMTP."""
        self.smtp_host = config.smtp.host
        self.smtp_port = config.smtp.port
        self.smtp_user = config.smtp.user
        self.smtp_password = config.smtp.password
        self.use_tls = config.smtp.use_tls
        self.use_ssl = config.smtp.use_ssl
        
        # Validation de la configuration
        if not all([self.smtp_host, self.smtp_port, self.smtp_user, self.smtp_password]):
            app_logger.warning(
                "Configuration SMTP incomplète. "
                "Assurez-vous d'avoir défini SMTP_HOST, SMTP_PORT, SMTP_USER et SMTP_PASSWORD."
            )
    
    def send_email(
        self,
        to_email: str,
        subject: str,
        html_content: Optional[str] = None,
        text_content: Optional[str] = None,
        from_name: Optional[str] = None,
        reply_to: Optional[str] = None,
        personalization_data: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Envoie un email via SMTP.
        
        Args:
            to_email: Adresse email du destinataire
            subject: Sujet de l'email
            html_content: Contenu HTML de l'email (optionnel)
            text_content: Contenu texte brut de l'email (optionnel)
            from_name: Nom de l'expéditeur (optionnel, utilise smtp_user par défaut)
            reply_to: Adresse de réponse (optionnel)
            personalization_data: Données pour personnaliser le contenu (ex: {first_name: "John"})
            
        Returns:
            True si l'envoi a réussi, False sinon
        """
        try:
            # Personnalisation du contenu
            if personalization_data:
                if html_content:
                    html_content = self._personalize_content(html_content, personalization_data)
                if text_content:
                    text_content = self._personalize_content(text_content, personalization_data)
                subject = self._personalize_content(subject, personalization_data)
            
            # Création du message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = f'"{from_name}" <{self.smtp_user}>' if from_name else self.smtp_user
            msg['To'] = to_email
            
            if reply_to:
                msg['Reply-To'] = reply_to
            
            # Ajouter les contenus
            if text_content:
                msg.attach(MIMEText(text_content, 'plain'))
            
            if html_content:
                msg.attach(MIMEText(html_content, 'html'))
            
            # Envoi via SMTP
            if self.use_ssl:
                # Connexion SSL (port 465)
                with smtplib.SMTP_SSL(self.smtp_host, self.smtp_port) as server:
                    server.login(self.smtp_user, self.smtp_password)
                    server.send_message(msg)
            else:
                # Connexion STARTTLS (port 587, recommandé pour Proton Mail)
                with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                    server.ehlo()
                    if self.use_tls:
                        server.starttls()
                        server.ehlo()
                    server.login(self.smtp_user, self.smtp_password)
                    server.send_message(msg)
            
            app_logger.info(f"Email envoyé avec succès à {to_email}")
            return True
            
        except smtplib.SMTPAuthenticationError as e:
            app_logger.error(
                f"Erreur d'authentification SMTP pour {to_email}: {e}. "
                "Vérifiez votre jeton SMTP Proton Mail ou vos identifiants."
            )
            return False
        except smtplib.SMTPException as e:
            app_logger.error(f"Erreur SMTP lors de l'envoi à {to_email}: {e}")
            return False
        except Exception as e:
            app_logger.error(f"Erreur inattendue lors de l'envoi à {to_email}: {e}")
            return False
    
    def send_bulk_emails(
        self,
        recipients: List[Dict[str, Any]],
        subject: str,
        html_content: Optional[str] = None,
        text_content: Optional[str] = None,
        from_name: Optional[str] = None,
        reply_to: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Envoie des emails en masse avec personnalisation pour chaque destinataire.
        
        Args:
            recipients: Liste de dictionnaires avec 'email' et autres champs pour personnalisation
            subject: Sujet de l'email (peut contenir des variables de personnalisation)
            html_content: Contenu HTML (peut contenir des variables de personnalisation)
            text_content: Contenu texte (peut contenir des variables de personnalisation)
            from_name: Nom de l'expéditeur
            reply_to: Adresse de réponse
            
        Returns:
            Dictionnaire avec les statistiques d'envoi {sent: int, failed: int, total: int}
        """
        sent_count = 0
        failed_count = 0
        failed_emails = []
        
        app_logger.info(f"Début d'envoi groupé de {len(recipients)} emails")
        
        for recipient in recipients:
            email = recipient.get('email')
            if not email:
                app_logger.warning(f"Destinataire sans email: {recipient}")
                failed_count += 1
                continue
            
            # Préparer les données de personnalisation
            personalization_data = {k: v for k, v in recipient.items() if k != 'email'}
            
            # Envoyer l'email
            success = self.send_email(
                to_email=email,
                subject=subject,
                html_content=html_content,
                text_content=text_content,
                from_name=from_name,
                reply_to=reply_to,
                personalization_data=personalization_data
            )
            
            if success:
                sent_count += 1
            else:
                failed_count += 1
                failed_emails.append(email)
        
        result = {
            'sent': sent_count,
            'failed': failed_count,
            'total': len(recipients),
            'failed_emails': failed_emails
        }
        
        app_logger.info(
            f"Envoi groupé terminé: {sent_count} réussis, "
            f"{failed_count} échoués sur {len(recipients)}"
        )
        
        return result
    
    def test_connection(self) -> bool:
        """
        Teste la connexion SMTP.
        
        Returns:
            True si la connexion réussit, False sinon
        """
        try:
            if self.use_ssl:
                with smtplib.SMTP_SSL(self.smtp_host, self.smtp_port) as server:
                    server.login(self.smtp_user, self.smtp_password)
            else:
                with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                    server.ehlo()
                    if self.use_tls:
                        server.starttls()
                        server.ehlo()
                    server.login(self.smtp_user, self.smtp_password)
            
            app_logger.info("Test de connexion SMTP réussi")
            return True
        except Exception as e:
            app_logger.error(f"Échec du test de connexion SMTP: {e}")
            return False
    
    @staticmethod
    def _personalize_content(content: str, data: Dict[str, Any]) -> str:
        """
        Personnalise le contenu en remplaçant les variables.
        
        Supporte les formats:
        - {{variable}} : remplacé par data['variable']
        - {variable} : remplacé par data['variable']
        
        Args:
            content: Contenu à personnaliser
            data: Dictionnaire de données pour la personnalisation
            
        Returns:
            Contenu personnalisé
        """
        if not content or not data:
            return content
        
        result = content
        for key, value in data.items():
            # Format double accolade {{key}}
            result = result.replace(f'{{{{{key}}}}}', str(value))
            # Format simple accolade {key}
            result = result.replace(f'{{{key}}}', str(value))
        
        return result


# Instance globale du service
email_service = EmailService()
