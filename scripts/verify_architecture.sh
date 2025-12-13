#!/bin/bash

# 🧪 Script de vérification de l'architecture MVVM

echo "🧪 Vérification de l'architecture MVVM"
echo "======================================"
echo ""

errors=0
warnings=0

# Vérifier que les anciens dossiers n'existent plus
echo "🗑️  Vérification de la purge..."
if [ -d "src" ]; then
    echo "❌ ERREUR: Le dossier 'src/' existe encore"
    errors=$((errors + 1))
else
    echo "✅ Le dossier 'src/' a bien été supprimé"
fi

if [ -d "backend" ]; then
    echo "❌ ERREUR: Le dossier 'backend/' existe encore"
    errors=$((errors + 1))
else
    echo "✅ Le dossier 'backend/' a bien été supprimé"
fi

echo ""

# Vérifier la nouvelle structure
echo "📁 Vérification de la nouvelle structure..."

required_dirs=(
    "app"
    "app/core"
    "app/shared"
    "app/features"
    "app/features/campaign"
    "app/features/dashboard"
    "app/features/templates"
    "app/features/suppression"
    "app/features/configuration"
)

for dir in "${required_dirs[@]}"; do
    if [ -d "$dir" ]; then
        echo "✅ $dir"
    else
        echo "❌ ERREUR: $dir manquant"
        errors=$((errors + 1))
    fi
done

echo ""

# Vérifier les fichiers importants
echo "📄 Vérification des fichiers importants..."

required_files=(
    "app/main.py"
    "app/requirements.txt"
    "start_mvvm.sh"
    "README.md"
    "ARCHITECTURE_MVVM.md"
    "INDEX.md"
)

for file in "${required_files[@]}"; do
    if [ -f "$file" ]; then
        echo "✅ $file"
    else
        echo "❌ ERREUR: $file manquant"
        errors=$((errors + 1))
    fi
done

echo ""

# Vérifier que chaque feature a la structure MVVM
echo "🏗️  Vérification de la structure MVVM des features..."

features=("campaign" "dashboard" "templates" "suppression" "configuration")

for feature in "${features[@]}"; do
    echo "Checking $feature..."
    
    if [ -d "app/features/$feature/model" ] && \
       [ -d "app/features/$feature/view" ] && \
       [ -d "app/features/$feature/viewmodel" ] && \
       [ -d "app/features/$feature/service" ]; then
        echo "  ✅ $feature a la structure MVVM complète"
    else
        echo "  ⚠️  WARNING: $feature n'a pas la structure MVVM complète"
        warnings=$((warnings + 1))
    fi
done

echo ""

# Vérifier les services partagés
echo "🔄 Vérification des services partagés..."

if [ -d "app/shared/services" ]; then
    service_count=$(find app/shared/services -name "*.py" ! -name "__init__.py" | wc -l)
    echo "✅ $service_count services partagés trouvés"
else
    echo "❌ ERREUR: Dossier shared/services manquant"
    errors=$((errors + 1))
fi

echo ""

# Vérifier .env
echo "⚙️  Vérification de la configuration..."

if [ -f ".env" ]; then
    echo "✅ Fichier .env présent"
else
    echo "⚠️  WARNING: Fichier .env manquant (à créer)"
    warnings=$((warnings + 1))
fi

echo ""

# Résumé
echo "📊 RÉSUMÉ"
echo "========="
echo "❌ Erreurs: $errors"
echo "⚠️  Warnings: $warnings"
echo ""

if [ $errors -eq 0 ] && [ $warnings -eq 0 ]; then
    echo "╔════════════════════════════════════════════════════════════════╗"
    echo "║  🎉 TOUT EST OK ! L'architecture MVVM est correcte !          ║"
    echo "╚════════════════════════════════════════════════════════════════╝"
    exit 0
elif [ $errors -eq 0 ]; then
    echo "✅ Architecture valide (quelques warnings mineurs)"
    exit 0
else
    echo "❌ Des erreurs ont été détectées, veuillez les corriger"
    exit 1
fi
