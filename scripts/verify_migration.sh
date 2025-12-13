#!/bin/bash

# Script de vérification de la migration MVVM Feature-First
# Vérifie que tous les fichiers frontend ont été correctement migrés

echo "🔍 Vérification de la migration frontend → MVVM Feature-First"
echo "================================================================"
echo ""

# Couleurs
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

errors=0
warnings=0

# 1. Vérifier la présence des composants React
echo "📦 1. Vérification des composants React"
components=(
    "app/features/campaign/view/Campaign.tsx"
    "app/features/dashboard/view/Dashboard.tsx"
    "app/features/configuration/view/Configuration.tsx"
    "app/features/suppression/view/Suppression.tsx"
    "app/features/templates/view/Templates.tsx"
    "app/core/frontend/App.tsx"
    "app/core/frontend/main.tsx"
)

for component in "${components[@]}"; do
    if [ -f "$component" ]; then
        echo -e "  ${GREEN}✓${NC} $component"
    else
        echo -e "  ${RED}✗${NC} $component (MANQUANT)"
        ((errors++))
    fi
done
echo ""

# 2. Vérifier la présence des services API
echo "🔄 2. Vérification des services API"
services=(
    "app/features/campaign/viewmodel/campaign_api.service.ts"
    "app/features/dashboard/viewmodel/dashboard_api.service.ts"
    "app/features/configuration/viewmodel/configuration_api.service.ts"
    "app/features/suppression/viewmodel/suppression_api.service.ts"
    "app/features/templates/viewmodel/templates_api.service.ts"
)

for service in "${services[@]}"; do
    if [ -f "$service" ]; then
        echo -e "  ${GREEN}✓${NC} $service"
    else
        echo -e "  ${RED}✗${NC} $service (MANQUANT)"
        ((errors++))
    fi
done
echo ""

# 3. Vérifier la présence des types TypeScript
echo "📋 3. Vérification des types TypeScript"
types=(
    "app/features/campaign/model/campaign_types.ts"
    "app/features/dashboard/model/dashboard_types.ts"
    "app/features/configuration/model/configuration_types.ts"
    "app/features/suppression/model/suppression_types.ts"
    "app/features/templates/model/templates_types.ts"
)

for type in "${types[@]}"; do
    if [ -f "$type" ]; then
        echo -e "  ${GREEN}✓${NC} $type"
    else
        echo -e "  ${RED}✗${NC} $type (MANQUANT)"
        ((errors++))
    fi
done
echo ""

# 4. Vérifier la présence des styles
echo "🎨 4. Vérification des styles CSS"
styles=(
    "app/core/shared/styles/App.css"
    "app/core/shared/styles/index.css"
)

for style in "${styles[@]}"; do
    if [ -f "$style" ]; then
        echo -e "  ${GREEN}✓${NC} $style"
    else
        echo -e "  ${RED}✗${NC} $style (MANQUANT)"
        ((errors++))
    fi
done
echo ""

# 5. Vérifier les fichiers de configuration
echo "⚙️  5. Vérification des fichiers de configuration"
configs=(
    "package.json"
    "tsconfig.json"
    "vite.config.ts"
    "index.html"
    ".env.example"
)

for config in "${configs[@]}"; do
    if [ -f "$config" ]; then
        echo -e "  ${GREEN}✓${NC} $config"
    else
        echo -e "  ${RED}✗${NC} $config (MANQUANT)"
        ((errors++))
    fi
done
echo ""

# 6. Vérifier que l'ancien dossier frontend existe encore
echo "🗑️  6. Vérification de l'ancien dossier frontend"
if [ -d "frontend" ]; then
    echo -e "  ${YELLOW}⚠${NC} Le dossier 'frontend/' existe encore"
    echo "     → Prêt à être supprimé avec: rm -rf frontend/"
    ((warnings++))
else
    echo -e "  ${GREEN}✓${NC} Le dossier 'frontend/' a été supprimé"
fi
echo ""

# 7. Compter les fichiers migrés
echo "📊 7. Statistiques de migration"
tsx_files=$(find app -type f -name "*.tsx" | wc -l | tr -d ' ')
ts_files=$(find app -type f -name "*.ts" | wc -l | tr -d ' ')
css_files=$(find app -type f -name "*.css" | wc -l | tr -d ' ')

echo "  • Composants React (.tsx) : $tsx_files"
echo "  • Services TypeScript (.ts) : $ts_files"
echo "  • Fichiers CSS : $css_files"
echo ""

# Résumé final
echo "================================================================"
if [ $errors -eq 0 ]; then
    echo -e "${GREEN}✅ Migration complète !${NC} Tous les fichiers sont présents."
    if [ $warnings -gt 0 ]; then
        echo -e "${YELLOW}⚠️  $warnings avertissement(s)${NC}"
    fi
    echo ""
    echo "🎉 Prochaines étapes :"
    echo "   1. npm install (si nécessaire)"
    echo "   2. npm run dev (pour tester)"
    echo "   3. rm -rf frontend/ (pour purger l'ancien dossier)"
else
    echo -e "${RED}❌ Erreurs détectées : $errors fichier(s) manquant(s)${NC}"
    exit 1
fi
echo "================================================================"
