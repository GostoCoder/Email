"""
Routage principal de l'application Flask.
Architecture MVVM Feature-First
"""

import os
from flask import Flask, jsonify, send_from_directory
from flask_cors import CORS
from app.core.config.settings import config


def create_app() -> Flask:
    """Factory pour créer l'application Flask."""
    # Chemin vers le frontend compilé
    frontend_dist = os.path.join(os.path.dirname(__file__), '..', 'frontend', 'dist')
    
    # Désactiver la route static par défaut pour contrôler manuellement le routing SPA
    app = Flask(__name__, static_folder=None)
    CORS(app)
    
    app.config['UPLOAD_FOLDER'] = str(config.upload_dir)
    app.config['MAX_CONTENT_LENGTH'] = config.max_file_size
    
    # =========================================================================
    # Routes de santé et statut (pour Docker health checks)
    # =========================================================================
    @app.route('/api/health', methods=['GET'])
    def health_check():
        """Endpoint de health check pour Docker/Kubernetes."""
        return jsonify({
            'status': 'healthy',
            'service': 'outil-emailing',
            'architecture': 'MVVM Feature-First'
        }), 200
    
    @app.route('/api/ready', methods=['GET'])
    def readiness_check():
        """Endpoint de readiness check."""
        return jsonify({
            'status': 'ready',
            'smtp_configured': bool(config.smtp.host and config.smtp.user)
        }), 200
    
    # =========================================================================
    # Enregistrement des blueprints des features MVVM
    # Chaque feature a sa propre structure: model/view/viewmodel/service
    # =========================================================================
    from app.features.campaign.view.campaign_routes import campaign_bp
    from app.features.dashboard.view.dashboard_routes import dashboard_bp
    from app.features.configuration.view.configuration_routes import configuration_bp
    from app.features.templates.view.templates_routes import templates_bp
    from app.features.suppression.view.suppression_routes import suppression_bp
    
    app.register_blueprint(campaign_bp, url_prefix='/api/campaign')
    app.register_blueprint(dashboard_bp, url_prefix='/api/dashboard')
    app.register_blueprint(configuration_bp, url_prefix='/api/configuration')
    app.register_blueprint(templates_bp, url_prefix='/api/templates')
    app.register_blueprint(suppression_bp, url_prefix='/api/suppression')
    
    # =========================================================================
    # Routes pour servir le frontend React
    # =========================================================================
    @app.route('/')
    def serve_frontend():
        """Sert la page principale du frontend React."""
        return send_from_directory(frontend_dist, 'index.html')
    
    @app.route('/<path:path>')
    def serve_static(path):
        """Sert les fichiers statiques ou redirige vers index.html pour le SPA."""
        # Si c'est un fichier statique qui existe, le servir
        full_path = os.path.join(frontend_dist, path)
        if os.path.isfile(full_path):
            return send_from_directory(frontend_dist, path)
        # Sinon, retourner index.html pour le routing SPA
        return send_from_directory(frontend_dist, 'index.html')
    
    return app
