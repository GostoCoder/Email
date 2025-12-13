#!/bin/bash

# 📊 Affichage de la structure du projet MVVM

echo "📁 Structure de l'Outil Emailing (Architecture MVVM)"
echo "===================================================="
echo ""

# Vérifier si tree est installé
if ! command -v tree &> /dev/null; then
    echo "⚠️  'tree' n'est pas installé. Utilisation de 'find' à la place."
    echo ""
    echo "📂 app/ (Backend MVVM)"
    find app -type f -name "*.py" | head -20
    echo ""
    echo "📂 frontend/ (Frontend React)"
    find frontend/src -type f \( -name "*.tsx" -o -name "*.ts" \) 2>/dev/null | head -10
else
    echo "📂 app/ (Backend MVVM)"
    tree -L 3 app/ -I '__pycache__|*.pyc'
    echo ""
    echo "📂 frontend/ (Frontend React)"
    tree -L 2 frontend/src/ -I 'node_modules|dist'
fi

echo ""
echo "📊 Statistiques"
echo "==============="

# Compter les fichiers Python
py_files=$(find app -name "*.py" | wc -l)
echo "✅ Fichiers Python: $py_files"

# Compter les features
features=$(ls -d app/features/*/ 2>/dev/null | wc -l)
echo "✅ Features MVVM: $features"

# Compter les services partagés
services=$(find app/shared/services -name "*.py" 2>/dev/null | wc -l)
echo "✅ Services partagés: $services"

# Compter les modèles
models=$(find app -path "*/model/*.py" 2>/dev/null | wc -l)
echo "✅ Modèles: $models"

# Compter les routes
routes=$(find app -path "*/view/*_routes.py" 2>/dev/null | wc -l)
echo "✅ Routes (API): $routes"

echo ""
echo "🚀 Pour démarrer l'application:"
echo "   ./start_mvvm.sh"
echo ""
echo "📖 Documentation:"
echo "   - README.md"
echo "   - ARCHITECTURE_MVVM.md"
echo "   - MIGRATION_NOTES.md"
