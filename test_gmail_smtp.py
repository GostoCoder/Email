#!/usr/bin/env python3
"""
Script de test pour vérifier la configuration Gmail SMTP
"""

import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()

def test_gmail_smtp():
    """Test la connexion Gmail SMTP"""
    
    # Récupérer les informations de configuration
    smtp_host = os.getenv('SMTP_HOST', 'smtp.gmail.com')
    smtp_port = int(os.getenv('SMTP_PORT', '587'))
    smtp_username = os.getenv('SMTP_USERNAME')
    smtp_password = os.getenv('SMTP_PASSWORD')
    smtp_use_tls = os.getenv('SMTP_USE_TLS', 'true').lower() == 'true'
    
    print("=" * 60)
    print("TEST DE CONFIGURATION GMAIL SMTP")
    print("=" * 60)
    print(f"Hôte SMTP: {smtp_host}")
    print(f"Port SMTP: {smtp_port}")
    print(f"Nom d'utilisateur: {smtp_username}")
    print(f"TLS activé: {smtp_use_tls}")
    print(f"Mot de passe: {'✓ Configuré' if smtp_password else '✗ Non configuré'}")
    print("=" * 60)
    
    if not smtp_username or not smtp_password:
        print("\n❌ ERREUR: SMTP_USERNAME ou SMTP_PASSWORD non configuré dans .env")
        print("\nVeuillez configurer:")
        print("1. SMTP_USERNAME=votre.email@gmail.com")
        print("2. SMTP_PASSWORD=votre-mot-de-passe-application")
        return False
    
    try:
        print("\n📧 Test de connexion au serveur SMTP...")
        server = smtplib.SMTP(smtp_host, smtp_port, timeout=10)
        
        if smtp_use_tls:
            print("🔒 Activation TLS...")
            server.starttls()
        
        print("🔑 Authentification...")
        server.login(smtp_username, smtp_password)
        
        print("\n✅ SUCCÈS: Connexion SMTP établie avec succès!")
        print(f"✅ Authentification réussie pour: {smtp_username}")
        
        # Test d'envoi d'un email de test (optionnel)
        send_test = input("\nVoulez-vous envoyer un email de test? (o/n): ").lower().strip()
        
        if send_test == 'o':
            to_email = input("Adresse email de destination: ").strip()
            
            if to_email:
                msg = MIMEMultipart('alternative')
                msg['Subject'] = "Test Email Campaign Platform"
                msg['From'] = f"Email Campaign Platform <{smtp_username}>"
                msg['To'] = to_email
                
                html = """
                <html>
                <body>
                    <h2>🎉 Test réussi!</h2>
                    <p>Votre configuration Gmail SMTP fonctionne correctement.</p>
                    <p><strong>Email Campaign Platform</strong> est prêt à envoyer des campagnes.</p>
                    <hr>
                    <p style="color: #666; font-size: 12px;">
                        Ceci est un email de test automatique.
                    </p>
                </body>
                </html>
                """
                
                msg.attach(MIMEText(html, 'html'))
                
                print(f"\n📤 Envoi de l'email de test à {to_email}...")
                server.sendmail(smtp_username, to_email, msg.as_string())
                print("✅ Email de test envoyé avec succès!")
                print(f"📬 Vérifiez la boîte de réception de {to_email}")
        
        server.quit()
        
        print("\n" + "=" * 60)
        print("✅ CONFIGURATION GMAIL SMTP VALIDÉE")
        print("=" * 60)
        print("\nVous pouvez maintenant:")
        print("1. Démarrer l'application: docker compose up -d backend frontend redis")
        print("2. Accéder à l'interface: http://localhost:3000")
        print("3. Créer et gérer vos campagnes email")
        
        print("\n⚠️  LIMITES GMAIL:")
        print("   - Comptes Gmail gratuits: 500 emails/jour")
        print("   - Google Workspace: 2000 emails/jour")
        
        return True
        
    except smtplib.SMTPAuthenticationError as e:
        print("\n❌ ERREUR D'AUTHENTIFICATION")
        print(f"Détails: {str(e)}")
        print("\nVérifiez que:")
        print("1. Vous avez activé la validation en 2 étapes sur Gmail")
        print("2. Vous utilisez un MOT DE PASSE D'APPLICATION (pas votre mot de passe Gmail)")
        print("3. Le mot de passe d'application est correct (16 caractères sans espaces)")
        print("\nPour générer un mot de passe d'application:")
        print("👉 https://myaccount.google.com/apppasswords")
        return False
        
    except smtplib.SMTPException as e:
        print(f"\n❌ ERREUR SMTP: {str(e)}")
        return False
        
    except Exception as e:
        print(f"\n❌ ERREUR: {str(e)}")
        return False

if __name__ == "__main__":
    success = test_gmail_smtp()
    exit(0 if success else 1)
