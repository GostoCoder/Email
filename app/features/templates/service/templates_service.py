"""
Service de gestion des templates.
"""

from typing import List, Optional
from pathlib import Path
from app.features.templates.model.template_model import EmailTemplate
from app.core.shared.services.database_service import get_db
from app.core.config.settings import config
from app.core.utils.logger import app_logger


class TemplatesService:
    """Service pour gérer les templates d'emails via Supabase."""
    
    def __init__(self):
        self.db = get_db()
        self.templates_dir = config.templates_dir  # Fallback pour les templates fichiers
    
    def list_templates(self) -> List[EmailTemplate]:
        """Liste tous les templates depuis Supabase."""
        try:
            templates_data = self.db.select('templates', filters={'is_active': True})
            templates = []
            
            for data in templates_data:
                template = EmailTemplate(
                    name=data['name'],
                    subject=data.get('description', f"Template {data['name']}"),
                    html_content=data['html_content'],
                    text_content=data.get('text_content', '')
                )
                templates.append(template)
            
            # Fallback : si aucun template en DB, charger depuis fichiers
            if not templates:
                app_logger.warning("Aucun template en DB, chargement depuis fichiers...")
                templates = self._list_templates_from_files()
            
            return templates
        except Exception as e:
            app_logger.error(f"Erreur liste templates: {e}")
            # Fallback sur fichiers en cas d'erreur
            return self._list_templates_from_files()
    
    def _list_templates_from_files(self) -> List[EmailTemplate]:
        """Liste les templates depuis les fichiers (fallback)."""
        templates = []
        
        for html_file in self.templates_dir.glob("*.html"):
            template_name = html_file.stem
            txt_file = self.templates_dir / f"{template_name}.txt"
            
            try:
                html_content = html_file.read_text(encoding='utf-8')
                text_content = txt_file.read_text(encoding='utf-8') if txt_file.exists() else ""
                
                template = EmailTemplate(
                    name=template_name,
                    subject=f"Template {template_name}",
                    html_content=html_content,
                    text_content=text_content
                )
                templates.append(template)
            except Exception as e:
                app_logger.error(f"Erreur chargement template fichier {template_name}: {e}")
        
        return templates
    
    def get_template(self, name: str) -> Optional[EmailTemplate]:
        """Récupère un template depuis Supabase."""
        try:
            templates = self.db.select('templates', filters={'name': name, 'is_active': True})
            
            if templates:
                data = templates[0]
                return EmailTemplate(
                    name=data['name'],
                    subject=data.get('description', f"Template {data['name']}"),
                    html_content=data['html_content'],
                    text_content=data.get('text_content', '')
                )
            
            # Fallback sur fichier si non trouvé en DB
            return self._get_template_from_file(name)
            
        except Exception as e:
            app_logger.error(f"Erreur récupération template {name}: {e}")
            return self._get_template_from_file(name)
    
    def _get_template_from_file(self, name: str) -> Optional[EmailTemplate]:
        """Récupère un template depuis un fichier (fallback)."""
        html_file = self.templates_dir / f"{name}.html"
        txt_file = self.templates_dir / f"{name}.txt"
        
        if not html_file.exists():
            return None
        
        try:
            return EmailTemplate(
                name=name,
                subject=f"Template {name}",
                html_content=html_file.read_text(encoding='utf-8'),
                text_content=txt_file.read_text(encoding='utf-8') if txt_file.exists() else ""
            )
        except Exception as e:
            app_logger.error(f"Erreur lecture template fichier {name}: {e}")
            return None
    
    def save_template(self, template: EmailTemplate) -> bool:
        """Enregistre un template dans Supabase."""
        try:
            # Vérifier si le template existe déjà
            existing = self.db.select('templates', filters={'name': template.name})
            
            if existing:
                # Mettre à jour
                self.db.update(
                    'templates',
                    {
                        'html_content': template.html_content,
                        'text_content': template.text_content,
                        'description': template.subject
                    },
                    {'name': template.name}
                )
                app_logger.info(f"Template {template.name} mis à jour")
            else:
                # Créer nouveau
                self.db.insert('templates', {
                    'name': template.name,
                    'html_content': template.html_content,
                    'text_content': template.text_content,
                    'description': template.subject,
                    'is_active': True
                })
                app_logger.info(f"Template {template.name} créé")
            
            return True
            
        except Exception as e:
            app_logger.error(f"Erreur sauvegarde template {template.name}: {e}")
            return False
    
    def create_template(self, name: str, html_content: str, text_content: str = "", description: str = "") -> bool:
        """Crée un nouveau template dans Supabase."""
        try:
            self.db.insert('templates', {
                'name': name,
                'html_content': html_content,
                'text_content': text_content,
                'description': description or f"Template {name}",
                'is_active': True
            })
            app_logger.info(f"Template {name} créé avec succès")
            return True
        except Exception as e:
            app_logger.error(f"Erreur création template {name}: {e}")
            return False
    
    def delete_template(self, name: str) -> bool:
        """Désactive un template (soft delete)."""
        try:
            self.db.update(
                'templates',
                {'is_active': False},
                {'name': name}
            )
            app_logger.info(f"Template {name} désactivé")
            return True
        except Exception as e:
            app_logger.error(f"Erreur suppression template {name}: {e}")
            return False

