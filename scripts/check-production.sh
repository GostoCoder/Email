#!/bin/bash
# =============================================================================
# Script de vérification de la configuration de production
# =============================================================================

set -e

echo "🔍 Vérification de la configuration pour la production..."
echo ""

# Couleurs
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

ERRORS=0
WARNINGS=0

check_error() {
    echo -e "${RED}❌ ERREUR:${NC} $1"
    ERRORS=$((ERRORS + 1))
}

check_warning() {
    echo -e "${YELLOW}⚠️  ATTENTION:${NC} $1"
    WARNINGS=$((WARNINGS + 1))
}

check_ok() {
    echo -e "${GREEN}✅${NC} $1"
}

# Vérifier que .env existe
if [ ! -f .env ]; then
    check_error "Le fichier .env n'existe pas. Copiez .env.example vers .env"
    exit 1
fi

# Charger les variables
source .env

echo "1️⃣  Configuration Flask"
if [ "$FLASK_ENV" = "production" ]; then
    check_ok "FLASK_ENV=production"
else
    check_warning "FLASK_ENV n'est pas en 'production' (valeur: $FLASK_ENV)"
fi

if [ "$FLASK_DEBUG" = "0" ]; then
    check_ok "FLASK_DEBUG=0"
else
    check_error "FLASK_DEBUG doit être à 0 en production (valeur: $FLASK_DEBUG)"
fi

if [ -z "$APP_SECRET_KEY" ] || [ "$APP_SECRET_KEY" = "CHANGE_ME_IN_PRODUCTION_USE_STRONG_SECRET_KEY" ]; then
    check_error "APP_SECRET_KEY n'est pas configurée ou utilise la valeur par défaut"
    echo "   Générez une clé avec: ./scripts/generate-secret-key.sh"
else
    check_ok "APP_SECRET_KEY configurée"
fi

echo ""
echo "2️⃣  Configuration SMTP"
if [ -z "$SMTP_HOST" ]; then
    check_error "SMTP_HOST n'est pas configuré"
else
    check_ok "SMTP_HOST: $SMTP_HOST"
fi

if [ -z "$SMTP_USER" ] || [ "$SMTP_USER" = "CHANGE_ME_YOUR_EMAIL@gmail.com" ]; then
    check_error "SMTP_USER n'est pas configuré ou utilise la valeur par défaut"
else
    check_ok "SMTP_USER: $SMTP_USER"
fi

if [ -z "$SMTP_PASSWORD" ] || [ "$SMTP_PASSWORD" = "CHANGE_ME_YOUR_APP_PASSWORD" ]; then
    check_error "SMTP_PASSWORD n'est pas configuré ou utilise la valeur par défaut"
else
    check_ok "SMTP_PASSWORD configuré"
fi

echo ""
echo "3️⃣  Configuration Supabase"
if [ -z "$SUPABASE_URL" ] || [ "$SUPABASE_URL" = "CHANGE_ME_YOUR_SUPABASE_PROJECT_URL" ]; then
    check_error "SUPABASE_URL n'est pas configuré ou utilise la valeur par défaut"
else
    check_ok "SUPABASE_URL: $SUPABASE_URL"
fi

if [ -z "$SUPABASE_KEY" ] || [ "$SUPABASE_KEY" = "CHANGE_ME_YOUR_SUPABASE_ANON_KEY" ]; then
    check_error "SUPABASE_KEY n'est pas configuré ou utilise la valeur par défaut"
else
    check_ok "SUPABASE_KEY configurée"
fi

echo ""
echo "4️⃣  Sécurité"

# Vérifier que .env n'est pas commité
if git ls-files --error-unmatch .env 2>/dev/null; then
    check_error ".env est commité dans Git! Ajoutez-le au .gitignore"
else
    check_ok ".env n'est pas commité dans Git"
fi

# Vérifier que .gitignore existe et contient .env
if [ -f .gitignore ] && grep -q "^\.env$" .gitignore; then
    check_ok ".env est dans .gitignore"
else
    check_warning ".env devrait être dans .gitignore"
fi

echo ""
echo "5️⃣  Fichiers Docker"
if [ -f Dockerfile ]; then
    check_ok "Dockerfile existe"
else
    check_error "Dockerfile n'existe pas"
fi

if [ -f docker-compose.yml ]; then
    check_ok "docker-compose.yml existe"
else
    check_error "docker-compose.yml n'existe pas"
fi

if [ -f .dockerignore ]; then
    check_ok ".dockerignore existe"
else
    check_warning ".dockerignore n'existe pas (recommandé pour optimiser le build)"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📊 Résumé"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if [ $ERRORS -eq 0 ] && [ $WARNINGS -eq 0 ]; then
    echo -e "${GREEN}✅ Configuration prête pour la production!${NC}"
    echo ""
    echo "🚀 Vous pouvez maintenant déployer avec:"
    echo "   ./scripts/deploy-production.sh"
    exit 0
elif [ $ERRORS -eq 0 ]; then
    echo -e "${YELLOW}⚠️  $WARNINGS avertissement(s)${NC}"
    echo ""
    echo "La configuration est valide mais pourrait être améliorée."
    echo "Vous pouvez déployer avec: ./scripts/deploy-production.sh"
    exit 0
else
    echo -e "${RED}❌ $ERRORS erreur(s)${NC}"
    if [ $WARNINGS -gt 0 ]; then
        echo -e "${YELLOW}⚠️  $WARNINGS avertissement(s)${NC}"
    fi
    echo ""
    echo "Corrigez les erreurs avant de déployer en production."
    exit 1
fi
