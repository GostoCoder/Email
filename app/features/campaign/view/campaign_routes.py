"""
Routes Flask pour la feature Campaign.
"""

from flask import Blueprint, request, jsonify
from werkzeug.utils import secure_filename
from pathlib import Path
from app.features.campaign.viewmodel.campaign_viewmodel import CampaignViewModel
from app.core.config.settings import config

campaign_bp = Blueprint('campaign', __name__)
campaign_vm = CampaignViewModel()


@campaign_bp.route('/create', methods=['POST'])
def create_campaign():
    """Crée une nouvelle campagne."""
    data = request.get_json()
    
    result = campaign_vm.create_campaign_command(
        name=data.get('name'),
        subject=data.get('subject'),
        template_name=data.get('template_name'),
        csv_file_path=data.get('csv_file_path')
    )
    
    if result['success']:
        return jsonify(result), 201
    else:
        return jsonify(result), 400


@campaign_bp.route('/start', methods=['POST'])
def start_campaign():
    """Démarre l'envoi d'une campagne."""
    result = campaign_vm.start_campaign_command()
    
    if result['success']:
        return jsonify(result), 200
    else:
        return jsonify(result), 400


@campaign_bp.route('/status', methods=['GET'])
def get_status():
    """Récupère le statut de la campagne actuelle."""
    result = campaign_vm.get_campaign_status()
    return jsonify(result), 200


@campaign_bp.route('/upload-csv', methods=['POST'])
def upload_csv():
    """Upload un fichier CSV."""
    if 'file' not in request.files:
        return jsonify({'error': 'Aucun fichier fourni'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'Nom de fichier vide'}), 400
    
    if file and file.filename.endswith('.csv'):
        filename = secure_filename(file.filename)
        filepath = config.upload_dir / filename
        file.save(str(filepath))
        
        return jsonify({
            'success': True,
            'filepath': str(filepath),
            'filename': filename
        }), 200
    
    return jsonify({'error': 'Format de fichier invalide'}), 400
