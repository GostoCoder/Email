#!/usr/bin/env python3
"""
Script de vérification de la configuration Supabase.
Vérifie que tous les services sont correctement configurés.
"""

import sys
from pathlib import Path

# Ajouter le répertoire parent au PYTHONPATH
sys.path.insert(0, str(Path(__file__).parent))

def check_imports():
    """Vérifie que tous les imports nécessaires fonctionnent."""
    print("🔍 Vérification des imports...")
    
    try:
        import supabase
        print("  ✅ supabase")
    except ImportError:
        print("  ❌ supabase - Installer avec: pip install supabase")
        return False
    
    return True

def check_config():
    """Vérifie la configuration."""
    print("\n📋 Vérification de la configuration...")
    
    try:
        from app.core.config.settings import config
        
        print(f"  ✅ Configuration chargée")
        print(f"     - SUPABASE_URL: {config.supabase.url}")
        print(f"     - SUPABASE_KEY: {'*' * 20}... (masqué)")
        
        return True
    except Exception as e:
        print(f"  ❌ Erreur configuration: {e}")
        return False

def check_database_service():
    """Vérifie le service de base de données."""
    print("\n🗄️  Vérification du service de base de données...")
    
    try:
        from app.core.shared.services.database_service import get_db
        
        db = get_db()
        print("  ✅ Service DatabaseService initialisé")
        
        # Test de connexion (si Supabase est démarré)
        try:
            if db.test_connection():
                print("  ✅ Connexion à la base de données réussie")
            else:
                print("  ⚠️  Connexion échouée - Supabase est-il démarré ?")
                print("     Lancer: supabase start")
        except Exception as e:
            print(f"  ⚠️  Impossible de tester la connexion: {e}")
            print("     Assurez-vous que Supabase est démarré: supabase start")
        
        return True
    except Exception as e:
        print(f"  ❌ Erreur service database: {e}")
        return False

def check_services():
    """Vérifie que tous les services utilisent Supabase."""
    print("\n🔧 Vérification des services...")
    
    services_to_check = [
        ('SuppressionService', 'app.features.suppression.service.suppression_service'),
        ('CampaignService', 'app.features.campaign.service.campaign_service'),
        ('TemplatesService', 'app.features.templates.service.templates_service'),
    ]
    
    all_ok = True
    
    for service_name, module_path in services_to_check:
        try:
            parts = module_path.split('.')
            module = __import__(module_path, fromlist=[parts[-1]])
            service_class = getattr(module, service_name)
            
            # Vérifier si le service a un attribut 'db'
            service_instance = service_class()
            if hasattr(service_instance, 'db'):
                print(f"  ✅ {service_name} - utilise Supabase")
            else:
                print(f"  ⚠️  {service_name} - pas d'attribut 'db' trouvé")
        except Exception as e:
            print(f"  ❌ {service_name} - Erreur: {e}")
            all_ok = False
    
    return all_ok

def check_migrations():
    """Vérifie que les fichiers de migration existent."""
    print("\n📁 Vérification des fichiers de migration...")
    
    files_to_check = [
        'supabase/config.toml',
        'supabase/migrations/20241212000001_initial_schema.sql',
        'supabase/seed.sql',
    ]
    
    all_exist = True
    
    for file_path in files_to_check:
        path = Path(file_path)
        if path.exists():
            print(f"  ✅ {file_path}")
        else:
            print(f"  ❌ {file_path} - MANQUANT")
            all_exist = False
    
    return all_exist

def main():
    """Fonction principale."""
    print("=" * 70)
    print("🚀 VÉRIFICATION DE LA CONFIGURATION SUPABASE")
    print("=" * 70)
    
    checks = [
        ("Imports Python", check_imports),
        ("Configuration", check_config),
        ("Service Database", check_database_service),
        ("Services métier", check_services),
        ("Fichiers de migration", check_migrations),
    ]
    
    results = []
    
    for check_name, check_func in checks:
        try:
            result = check_func()
            results.append((check_name, result))
        except Exception as e:
            print(f"\n❌ Erreur lors de {check_name}: {e}")
            results.append((check_name, False))
    
    print("\n" + "=" * 70)
    print("📊 RÉSUMÉ")
    print("=" * 70)
    
    all_ok = True
    for check_name, result in results:
        status = "✅" if result else "❌"
        print(f"{status} {check_name}")
        if not result:
            all_ok = False
    
    print("=" * 70)
    
    if all_ok:
        print("\n🎉 Tout est configuré correctement !")
        print("\n📝 Prochaines étapes:")
        print("   1. Démarrer Supabase: supabase start")
        print("   2. Installer les dépendances: pip install -r requirements.txt")
        print("   3. Démarrer l'application: python app/main.py")
        print("   4. Accéder à Supabase Studio: http://localhost:54323")
        return 0
    else:
        print("\n⚠️  Certains problèmes doivent être résolus")
        print("\n📝 Actions recommandées:")
        print("   1. Installer les dépendances: pip install -r requirements.txt")
        print("   2. Vérifier que Supabase est installé: supabase --version")
        print("   3. Démarrer Supabase: supabase start")
        return 1

if __name__ == '__main__':
    sys.exit(main())
