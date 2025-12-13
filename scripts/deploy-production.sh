#!/bin/bash
# =============================================================================
# Script de déploiement pour la production
# =============================================================================

set -e

echo "🚀 Démarrage du déploiement en production..."

# Couleurs pour les messages
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Fonction pour afficher les messages
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Vérifier que le fichier .env existe
if [ ! -f .env ]; then
    log_error "Le fichier .env n'existe pas!"
    log_info "Copiez .env.example vers .env et configurez les variables."
    exit 1
fi

# Vérifier les variables critiques
log_info "Vérification de la configuration..."
source .env

if [ "$APP_SECRET_KEY" = "CHANGE_ME_IN_PRODUCTION_USE_STRONG_SECRET_KEY" ]; then
    log_error "APP_SECRET_KEY n'est pas configurée!"
    log_info "Générez une clé avec: python -c \"import secrets; print(secrets.token_hex(32))\""
    exit 1
fi

if [ "$SMTP_USER" = "CHANGE_ME_YOUR_EMAIL@gmail.com" ]; then
    log_warn "SMTP_USER n'est pas configuré. L'envoi d'emails ne fonctionnera pas."
fi

if [ "$SUPABASE_URL" = "CHANGE_ME_YOUR_SUPABASE_PROJECT_URL" ]; then
    log_warn "SUPABASE_URL n'est pas configuré. La base de données ne fonctionnera pas."
fi

# Arrêter les conteneurs existants
log_info "Arrêt des conteneurs existants..."
docker-compose down

# Nettoyer les anciennes images
log_info "Nettoyage des anciennes images..."
docker image prune -f

# Build de la nouvelle image
log_info "Construction de l'image Docker..."
docker-compose build --no-cache app

# Démarrer l'application
log_info "Démarrage de l'application..."
docker-compose up -d app

# Attendre que l'application soit prête
log_info "Vérification du statut de l'application..."
sleep 5

# Health check
MAX_RETRIES=10
RETRY_COUNT=0
while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
    if curl -f http://localhost:${APP_PORT:-5000}/api/health > /dev/null 2>&1; then
        log_info "✅ Application démarrée avec succès!"
        echo ""
        log_info "🌐 Application disponible sur: http://localhost:${APP_PORT:-5000}"
        log_info "📊 Logs: docker-compose logs -f app"
        log_info "🛑 Arrêt: docker-compose down"
        exit 0
    fi
    RETRY_COUNT=$((RETRY_COUNT + 1))
    log_info "En attente du démarrage... ($RETRY_COUNT/$MAX_RETRIES)"
    sleep 3
done

log_error "L'application n'a pas démarré correctement!"
log_info "Vérifiez les logs avec: docker-compose logs app"
exit 1
