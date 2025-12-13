"""
Routes Flask pour la configuration.
"""

from flask import Blueprint, jsonify, request
from app.features.configuration.viewmodel.configuration_viewmodel import ConfigurationViewModel

configuration_bp = Blueprint('configuration', __name__)
configuration_vm = ConfigurationViewModel()


@configuration_bp.route('/get', methods=['GET'])
def get_configuration():
    """Récupère la configuration actuelle."""
    result = configuration_vm.get_configuration_data()
    return jsonify(result), 200


@configuration_bp.route('/update', methods=['POST'])
def update_configuration():
    """Met à jour la configuration."""
    data = request.get_json()
    result = configuration_vm.update_configuration_command(data)
    
    if result['success']:
        return jsonify(result), 200
    else:
        return jsonify(result), 500


@configuration_bp.route('/test-smtp', methods=['POST'])
def test_smtp():
    """Teste la connexion SMTP."""
    data = request.get_json()
    result = configuration_vm.test_smtp_command(data)
    
    if result['success']:
        return jsonify(result), 200
    else:
        return jsonify(result), 400
