"""
Routes Flask pour les templates.
"""

from flask import Blueprint, jsonify, request
from app.features.templates.viewmodel.templates_viewmodel import TemplatesViewModel

templates_bp = Blueprint('templates', __name__)
templates_vm = TemplatesViewModel()


@templates_bp.route('/list', methods=['GET'])
def list_templates():
    """Liste tous les templates."""
    result = templates_vm.get_all_templates()
    return jsonify(result), 200


@templates_bp.route('/<name>', methods=['GET'])
def get_template(name: str):
    """Récupère un template spécifique."""
    result = templates_vm.get_template_by_name(name)
    
    if result['success']:
        return jsonify(result), 200
    else:
        return jsonify(result), 404


@templates_bp.route('/save', methods=['POST'])
def save_template():
    """Sauvegarde un template."""
    data = request.get_json()
    result = templates_vm.save_template_command(data)
    
    if result['success']:
        return jsonify(result), 200
    else:
        return jsonify(result), 500
