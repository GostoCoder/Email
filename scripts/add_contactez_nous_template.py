#!/usr/bin/env python3
"""
Script pour ajouter le template "Contactez-nous" à la base de données.
"""

import os
import sys
from pathlib import Path

# Ajouter le répertoire parent au path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.shared.services.database_service import get_db
from app.core.utils.logger import app_logger

def add_contactez_nous_template():
    """Ajoute le template Contactez-nous à Supabase."""
    
    templates_dir = Path(__file__).parent.parent / "templates"
    html_file = templates_dir / "contactez-nous.html"
    txt_file = templates_dir / "contactez-nous.txt"
    
    if not html_file.exists():
        print(f"❌ Fichier HTML introuvable: {html_file}")
        return False
    
    print(f"📄 Lecture du template depuis {html_file}...")
    html_content = html_file.read_text(encoding='utf-8')
    text_content = txt_file.read_text(encoding='utf-8') if txt_file.exists() else ""
    
    db = get_db()
    
    try:
        # Vérifier si le template existe déjà
        existing = db.select('templates', filters={'name': 'contactez-nous'})
        
        if existing:
            print("⚠️  Le template 'contactez-nous' existe déjà. Mise à jour...")
            db.update(
                'templates',
                {
                    'html_content': html_content,
                    'text_content': text_content,
                    'description': 'Template de présentation OSD_Corp',
                    'is_active': True
                },
                {'name': 'contactez-nous'}
            )
            print("✅ Template 'contactez-nous' mis à jour avec succès!")
        else:
            print("📝 Création du nouveau template 'contactez-nous'...")
            db.insert('templates', {
                'name': 'contactez-nous',
                'html_content': html_content,
                'text_content': text_content,
                'description': 'Template de présentation OSD_Corp',
                'is_active': True
            })
            print("✅ Template 'contactez-nous' créé avec succès!")
        
        # Vérifier que le template est bien en base
        templates = db.select('templates', filters={'is_active': True})
        print(f"\n📋 Templates disponibles ({len(templates)}):")
        for t in templates:
            print(f"  - {t['name']}: {t.get('description', 'N/A')}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors de l'ajout du template: {e}")
        app_logger.error(f"Erreur ajout template contactez-nous: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Ajout du template 'Contactez-nous' à la base de données...\n")
    success = add_contactez_nous_template()
    sys.exit(0 if success else 1)
