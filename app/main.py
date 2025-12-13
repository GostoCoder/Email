"""
Point d'entrée principal de l'application MVVM.
Architecture Feature-First pour Outil-Emailing.
"""

import os
from app.core.routing.app_router import create_app
from app.core.utils.logger import app_logger

# Créer l'instance de l'application (nécessaire pour Gunicorn)
app = create_app()


def main():
    """Démarrer l'application en mode développement."""
    debug = os.getenv('FLASK_DEBUG', '0') == '1'
    host = os.getenv('APP_HOST', '0.0.0.0')
    port = int(os.getenv('APP_PORT', '5000'))
    
    app_logger.info("🚀 Démarrage de l'application Outil-Emailing")
    app_logger.info("📁 Architecture: Feature-First MVVM")
    app_logger.info(f"🌐 API disponible sur: http://{host}:{port}")
    app_logger.info(f"🔧 Mode debug: {'Activé' if debug else 'Désactivé'}")
    
    app.run(debug=debug, host=host, port=port)


if __name__ == '__main__':
    main()
