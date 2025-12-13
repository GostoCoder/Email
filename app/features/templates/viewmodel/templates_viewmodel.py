"""
ViewModel pour les templates.
"""

from typing import Dict, Any, List
from app.features.templates.service.templates_service import TemplatesService
from app.features.templates.model.template_model import EmailTemplate


class TemplatesViewModel:
    """ViewModel pour gérer la présentation des templates."""
    
    def __init__(self):
        self.service = TemplatesService()
    
    def get_all_templates(self) -> Dict[str, Any]:
        """Récupère tous les templates."""
        templates = self.service.list_templates()
        
        return {
            'success': True,
            'templates': [self._serialize_template(t) for t in templates]
        }
    
    def get_template_by_name(self, name: str) -> Dict[str, Any]:
        """Récupère un template spécifique."""
        template = self.service.get_template(name)
        
        if template:
            return {
                'success': True,
                'template': self._serialize_template(template)
            }
        else:
            return {
                'success': False,
                'error': f'Template "{name}" introuvable'
            }
    
    def save_template_command(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Commande pour sauvegarder un template."""
        template = EmailTemplate(
            name=data['name'],
            subject=data.get('subject', ''),
            html_content=data['html_content'],
            text_content=data.get('text_content', '')
        )
        
        success = self.service.save_template(template)
        
        return {
            'success': success,
            'message': 'Template sauvegardé' if success else 'Erreur sauvegarde'
        }
    
    def _serialize_template(self, template: EmailTemplate) -> Dict[str, Any]:
        """Sérialise un template pour la vue."""
        return {
            'id': template.id,
            'name': template.name,
            'subject': template.subject,
            'html_content': template.html_content,
            'text_content': template.text_content,
            'created_at': template.created_at.isoformat()
        }
