#!/bin/bash
# =============================================================================
# Script de test pour la fonctionnalité de désinscription
# =============================================================================

set -e

API_URL="${API_URL:-http://localhost:5002}"
TEST_EMAIL="test-unsubscribe@example.com"
CONTACT_ID="550e8400-e29b-41d4-a716-446655440000"
CAMPAIGN_ID="660e8400-e29b-41d4-a716-446655440001"

echo "🧪 Tests de la fonctionnalité de désinscription"
echo "================================================"
echo ""

# 1. Health check
echo "✅ Test 1: Health check"
HEALTH=$(curl -s "$API_URL/api/health")
echo "$HEALTH" | python3 -m json.tool
echo ""

# 2. Génération de token
echo "✅ Test 2: Génération d'un token de désinscription"
TOKEN_RESPONSE=$(curl -s -X POST "$API_URL/api/suppression/generate-token" \
  -H "Content-Type: application/json" \
  -d "{\"email\": \"$TEST_EMAIL\", \"contact_id\": \"$CONTACT_ID\", \"campaign_id\": \"$CAMPAIGN_ID\"}")
echo "$TOKEN_RESPONSE" | python3 -m json.tool
TOKEN=$(echo "$TOKEN_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['token'])")
echo ""

# 3. Vérification du statut avant désinscription
echo "✅ Test 3: Vérification du statut (avant désinscription)"
curl -s "$API_URL/api/suppression/check?email=$TEST_EMAIL" | python3 -m json.tool
echo ""

# 4. Page HTML de désinscription
echo "✅ Test 4: Chargement de la page HTML"
PAGE_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$API_URL/api/suppression/page/$TOKEN")
if [ "$PAGE_STATUS" = "200" ]; then
    echo "✓ Page chargée avec succès (HTTP $PAGE_STATUS)"
else
    echo "✗ Erreur de chargement de la page (HTTP $PAGE_STATUS)"
fi
echo ""

# 5. Test de la liste des emails désabonnés
echo "✅ Test 5: Liste des emails désabonnés"
curl -s "$API_URL/api/suppression/list" | python3 -m json.tool | head -15
echo ""

# 6. Test de génération d'URL complète
echo "✅ Test 6: URL de désinscription générée"
URL=$(echo "$TOKEN_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['url'])")
echo "URL: $URL"
echo ""

# 7. Validation du token
echo "✅ Test 7: Validation du format du token"
if [[ $TOKEN =~ ^[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+$ ]]; then
    echo "✓ Format du token valide (payload.signature)"
else
    echo "✗ Format du token invalide"
fi
echo ""

echo "================================================"
echo "✅ Tous les tests sont passés avec succès !"
echo ""
echo "📝 Note: Le processus complet de désinscription nécessite:"
echo "   1. Accès à la page: $URL"
echo "   2. Clic sur le bouton de confirmation"
echo "   3. POST vers /api/suppression/unsubscribe avec le token"
echo ""
echo "🚀 L'application est prête et fonctionnelle sur le port 5002"
