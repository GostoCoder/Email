#!/bin/bash
# =============================================================================
# Script de démarrage Docker pour Outil-Emailing
# Architecture MVVM Feature-First
# =============================================================================

set -e

# Couleurs pour les messages
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Répertoire du script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_DIR"

# Fonction d'aide
show_help() {
    echo -e "${BLUE}🐳 Outil-Emailing - Docker Helper${NC}"
    echo ""
    echo "Usage: $0 [command]"
    echo ""
    echo "Commands:"
    echo "  start       Démarrer l'application en production"
    echo "  dev         Démarrer en mode développement (hot-reload)"
    echo "  stop        Arrêter tous les containers"
    echo "  restart     Redémarrer l'application"
    echo "  logs        Afficher les logs en temps réel"
    echo "  build       Reconstruire les images"
    echo "  clean       Nettoyer les containers et volumes"
    echo "  status      Afficher le statut des containers"
    echo "  shell       Ouvrir un shell dans le container app"
    echo "  health      Vérifier la santé de l'application"
    echo ""
}

# Vérifier si .env existe
check_env() {
    if [ ! -f ".env" ]; then
        echo -e "${YELLOW}⚠️  Fichier .env non trouvé. Création depuis .env.example...${NC}"
        if [ -f ".env.example" ]; then
            cp .env.example .env
            echo -e "${GREEN}✅ Fichier .env créé. Veuillez le modifier avec vos configurations.${NC}"
        else
            echo -e "${RED}❌ Fichier .env.example non trouvé!${NC}"
            exit 1
        fi
    fi
}

# Commandes
case "${1:-help}" in
    start)
        check_env
        echo -e "${GREEN}🚀 Démarrage de l'application en production...${NC}"
        docker-compose up -d app
        echo -e "${GREEN}✅ Application démarrée sur http://localhost:5000${NC}"
        ;;
    dev)
        check_env
        echo -e "${BLUE}🔧 Démarrage en mode développement...${NC}"
        docker-compose --profile dev up dev
        ;;
    stop)
        echo -e "${YELLOW}⏹️  Arrêt des containers...${NC}"
        docker-compose down
        echo -e "${GREEN}✅ Containers arrêtés${NC}"
        ;;
    restart)
        echo -e "${YELLOW}🔄 Redémarrage de l'application...${NC}"
        docker-compose restart app
        echo -e "${GREEN}✅ Application redémarrée${NC}"
        ;;
    logs)
        echo -e "${BLUE}📋 Logs de l'application (Ctrl+C pour quitter)...${NC}"
        docker-compose logs -f app
        ;;
    build)
        echo -e "${BLUE}🏗️  Reconstruction des images...${NC}"
        docker-compose build --no-cache
        echo -e "${GREEN}✅ Images reconstruites${NC}"
        ;;
    clean)
        echo -e "${RED}🧹 Nettoyage complet...${NC}"
        docker-compose down -v
        docker system prune -f
        echo -e "${GREEN}✅ Nettoyage terminé${NC}"
        ;;
    status)
        echo -e "${BLUE}📊 Statut des containers:${NC}"
        docker-compose ps
        ;;
    shell)
        echo -e "${BLUE}🐚 Ouverture d'un shell dans le container...${NC}"
        docker-compose exec app sh
        ;;
    health)
        echo -e "${BLUE}🏥 Vérification de la santé...${NC}"
        response=$(curl -s http://localhost:5000/api/health 2>/dev/null || echo "")
        if [ -n "$response" ]; then
            echo -e "${GREEN}✅ Application saine${NC}"
            echo "$response" | python3 -m json.tool 2>/dev/null || echo "$response"
        else
            echo -e "${RED}❌ Application non accessible${NC}"
        fi
        ;;
    help|--help|-h)
        show_help
        ;;
    *)
        echo -e "${RED}❌ Commande inconnue: $1${NC}"
        show_help
        exit 1
        ;;
esac
