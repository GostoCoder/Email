#!/bin/bash
# =============================================================================
# Script de génération de clés secrètes pour la production
# =============================================================================

echo "🔐 Génération de clés secrètes pour la production"
echo ""

# Générer APP_SECRET_KEY
echo "📝 APP_SECRET_KEY (à copier dans votre .env) :"
python3 -c "import secrets; print(secrets.token_hex(32))"
echo ""

# Instructions
echo "📋 Instructions :"
echo "1. Copiez la clé générée ci-dessus"
echo "2. Ouvrez le fichier .env"
echo "3. Remplacez la valeur de APP_SECRET_KEY par cette nouvelle clé"
echo "4. Ne partagez JAMAIS cette clé"
echo "5. Utilisez une clé différente pour chaque environnement"
echo ""

# Vérifier si le .env existe
if [ -f .env ]; then
    if grep -q "CHANGE_ME_IN_PRODUCTION_USE_STRONG_SECRET_KEY" .env; then
        echo "⚠️  ATTENTION : Votre .env contient encore la valeur par défaut !"
        echo "   Mettez à jour APP_SECRET_KEY avant de déployer en production."
    fi
fi
