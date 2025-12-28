# 🔧 Guide d'Installation des Améliorations

## Installation Backend

### 1. Installer les nouvelles dépendances Python

```bash
cd backend
pip install -r requirements.txt
```

**Nouvelles dépendances:**
- `apscheduler==3.10.4` - Scheduler pour les envois planifiés
- `dnspython==2.6.1` - Validation DNS (SPF/DKIM/DMARC)

### 2. Vérifier l'installation

```bash
python -c "import apscheduler; import dns.resolver; print('✅ All dependencies installed')"
```

### 3. Configuration (.env)

Ajouter/vérifier ces variables dans votre fichier `.env` :

```env
# API URLs
API_BASE_URL=http://localhost:8000
APP_BASE_URL=http://localhost:3000

# Email retry configuration
EMAIL_MAX_RETRY_ATTEMPTS=3
EMAIL_BATCH_SIZE=100
EMAIL_RATE_LIMIT_PER_SECOND=10

# JWT secret (pour les tokens de tracking)
JWT_SECRET=change-me-to-a-strong-secret-key

# Email provider (existant)
EMAIL_PROVIDER=smtp  # ou sendgrid, mailgun
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
```

### 4. Redémarrer le serveur

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

**Le scheduler se lance automatiquement au démarrage de l'application.**

---

## Installation Frontend

### Pas de nouvelles dépendances !

Les modifications frontend utilisent uniquement les dépendances existantes.

### Redémarrer le dev server

```bash
cd frontend
npm run dev
```

---

## 🧪 Tests de Validation

### Test 1: Tracking des Ouvertures

1. Créer une campagne
2. Importer un destinataire (votre email)
3. Envoyer en mode test
4. Ouvrir l'email reçu
5. Vérifier dans l'interface que `opened_count` = 1

**Test manuel de l'endpoint:**
```bash
# Le pixel de tracking est automatiquement ajouté aux emails
# URL format: /v1/track/open?c={campaign_id}&r={recipient_id}&t={token}
```

### Test 2: Tracking des Clics

1. Créer une campagne avec un lien HTML: `<a href="https://google.com">Cliquer ici</a>`
2. Envoyer en test
3. Ouvrir l'email et cliquer sur le lien
4. Vérifier la redirection vers Google
5. Vérifier dans l'interface que `clicked_count` = 1

### Test 3: Validation DNS

```bash
# Tester avec Gmail (devrait passer tous les tests)
curl http://localhost:8000/v1/validate-domain/gmail.com

# Tester avec votre propre domaine
curl http://localhost:8000/v1/validate-domain/yourdomain.com
```

**Réponse attendue:**
```json
{
  "domain": "gmail.com",
  "spf": {"configured": true, "status": "pass"},
  "dkim": [{"configured": true, "selector": "google"}],
  "dmarc": {"configured": true, "policy": "reject"},
  "mx": {"configured": true},
  "overall_status": "pass",
  "issues": [],
  "recommendation": "✅ Your domain is properly configured!"
}
```

### Test 4: Duplication de Campagne

1. Dans l'interface, ouvrir une campagne existante
2. Cliquer sur "📋 Dupliquer"
3. Vérifier qu'une nouvelle campagne "(Copy)" est créée
4. Vérifier que la nouvelle campagne est en status "draft" avec 0 destinataires

**Test API:**
```bash
curl -X POST http://localhost:8000/v1/campaigns/{campaign_id}/duplicate \
  -H "Authorization: Bearer {token}"
```

### Test 5: Export CSV

1. Ouvrir une campagne avec des statistiques
2. Cliquer sur "📥 Exporter CSV"
3. Vérifier le téléchargement du fichier CSV
4. Ouvrir le CSV et vérifier les colonnes

**Test API:**
```bash
curl http://localhost:8000/v1/campaigns/{campaign_id}/stats/export \
  -H "Authorization: Bearer {token}" \
  -o campaign_export.csv
```

### Test 6: Preview avec Données Réelles

1. Créer une campagne avec template: `Bonjour {{firstname}} {{lastname}},`
2. Importer des destinataires
3. Utiliser l'endpoint preview

**Test API:**
```bash
curl "http://localhost:8000/v1/campaigns/{campaign_id}/preview?recipient_email=test@example.com" \
  -H "Authorization: Bearer {token}"
```

**Réponse attendue:**
```json
{
  "html_content": "Bonjour John Doe,",
  "subject": "Test",
  "from": "Sender <sender@example.com>",
  "recipient_data": {
    "firstname": "John",
    "lastname": "Doe",
    ...
  }
}
```

### Test 7: Retry avec Backoff

Pour tester le système de retry:

1. Configurer un mauvais SMTP (pour forcer des erreurs)
2. Envoyer une campagne
3. Observer les logs

**Logs attendus:**
```
INFO: Temporary error detected, will retry: Connection timeout
INFO: Scheduled retry 1/3 for test@example.com in 1 minutes
```

**Après le délai:**
```
INFO: Scheduled retry 2/3 for test@example.com in 2 minutes
INFO: Scheduled retry 3/3 for test@example.com in 4 minutes
```

**Erreur permanente (pas de retry):**
```
INFO: Permanent error detected, not retrying: Domain does not exist
```

### Test 8: Webhooks

**Setup:**
1. Aller sur https://webhook.site
2. Copier l'URL unique
3. Créer/modifier une campagne avec webhooks:

```bash
curl -X PATCH http://localhost:8000/v1/campaigns/{campaign_id} \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer {token}" \
  -d '{
    "metadata": {
      "webhooks": {
        "enabled": true,
        "url": "https://webhook.site/YOUR_UNIQUE_ID",
        "secret": "test_secret"
      }
    }
  }'
```

4. Envoyer la campagne
5. Vérifier sur webhook.site que vous recevez les notifications

**Événements attendus:**
- `email.sent` pour chaque email envoyé
- `email.opened` quand un email est ouvert
- `email.clicked` quand un lien est cliqué
- `campaign.completed` quand la campagne est terminée

**Vérifier la signature:**
```python
import hmac
import hashlib
import json

payload = {...}  # Le payload reçu
secret = "test_secret"
expected_sig = "sha256=" + hmac.new(
    secret.encode(),
    json.dumps(payload, sort_keys=True).encode(),
    hashlib.sha256
).hexdigest()

# Comparer avec le header X-Webhook-Signature
```

### Test 9: Planification

**Via l'interface:**
1. Créer une campagne avec destinataires
2. Cocher "📅 Planifier l'envoi"
3. Choisir une date dans 2 minutes
4. Sauvegarder
5. Attendre et vérifier l'envoi automatique

**Via API:**
```bash
# Planifier pour dans 5 minutes
SCHEDULED_TIME=$(date -u -v+5M '+%Y-%m-%dT%H:%M:%SZ')

curl -X POST "http://localhost:8000/v1/campaigns/{campaign_id}/schedule" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer {token}" \
  -d "{\"scheduled_at\": \"$SCHEDULED_TIME\"}"
```

**Vérifier les logs du scheduler:**
```
INFO: Scheduler started
INFO: Added scheduled campaigns check job (every 60s)
...
INFO: Found 1 scheduled campaigns ready to send
INFO: Starting scheduled campaign: {campaign_id}
```

---

## 🐛 Dépannage

### Problème: "Import dns.resolver could not be resolved"

**Solution:**
```bash
pip install dnspython==2.6.1
```

### Problème: "Import apscheduler could not be resolved"

**Solution:**
```bash
pip install apscheduler==3.10.4
```

### Problème: Le scheduler ne démarre pas

**Vérifier les logs au démarrage:**
```
INFO: Scheduler started
INFO: Added scheduled campaigns check job (every 60s)
```

**Si absent, vérifier:**
1. Que `lifespan` est bien configuré dans `main.py`
2. Que FastAPI version >= 0.104.1 (supporte `lifespan`)

### Problème: Tracking ne fonctionne pas

**Vérifier:**
1. `API_BASE_URL` est correctement configuré dans `.env`
2. Le token JWT est généré correctement (vérifier `JWT_SECRET`)
3. Les URLs de tracking dans l'email pointent vers votre serveur

**Tester manuellement:**
```bash
# Générer un token de test
python -c "
import hashlib
campaign_id = 'YOUR_CAMPAIGN_ID'
recipient_id = 'YOUR_RECIPIENT_ID'
secret = 'YOUR_JWT_SECRET'
data = f'{campaign_id}:{recipient_id}:{secret}'
token = hashlib.sha256(data.encode()).hexdigest()[:32]
print(f'Token: {token}')
"

# Tester l'endpoint
curl "http://localhost:8000/v1/track/open?c=CAMPAIGN_ID&r=RECIPIENT_ID&t=TOKEN"
```

### Problème: Webhooks ne sont pas envoyés

**Vérifier:**
1. La campagne a bien `metadata.webhooks.enabled = true`
2. L'URL webhook est accessible (tester avec curl)
3. Les logs pour voir si des erreurs sont reportées

**Test manuel:**
```bash
# Vérifier les metadata
curl http://localhost:8000/v1/campaigns/{campaign_id} \
  -H "Authorization: Bearer {token}" | jq '.metadata.webhooks'
```

### Problème: DNS validation échoue

**Causes possibles:**
1. Pas de connexion Internet
2. DNS timeout (firewall?)
3. Domaine n'a vraiment pas de records SPF/DKIM/DMARC

**Test:**
```bash
# Tester avec dig ou nslookup
dig TXT example.com
dig TXT _dmarc.example.com
dig MX example.com
```

---

## 📊 Monitoring

### Vérifier que tout fonctionne

```bash
# Health check
curl http://localhost:8000/health

# Vérifier le scheduler (doit tourner en arrière-plan)
# Chercher dans les logs: "Scheduler started"

# Stats d'une campagne
curl http://localhost:8000/v1/campaigns/{campaign_id}/stats

# Logs d'une campagne
curl http://localhost:8000/v1/campaigns/{campaign_id}/progress
```

### Logs Importants

**Backend (uvicorn):**
```
INFO: Scheduler started
INFO: Added scheduled campaigns check job (every 60s)
INFO: Email opened: campaign=xxx, recipient=xxx
INFO: Email clicked: campaign=xxx, recipient=xxx
INFO: Webhook delivered: email.sent to https://...
INFO: Campaign xxx completed: 100 sent, 2 failed
```

---

## ✅ Checklist de Validation

- [ ] `pip install -r requirements.txt` réussi
- [ ] Backend démarre sans erreurs
- [ ] Frontend démarre sans erreurs
- [ ] Validation DNS fonctionne (test avec gmail.com)
- [ ] Duplication de campagne fonctionne
- [ ] Export CSV télécharge un fichier
- [ ] Preview affiche le bon contenu
- [ ] Planification crée une campagne "scheduled"
- [ ] Tracking ouverture incrémente `opened_count`
- [ ] Tracking clic incrémente `clicked_count`
- [ ] Webhooks envoient des notifications (test avec webhook.site)
- [ ] Retry programme les tentatives avec délai croissant

---

**Besoin d'aide ?** Consultez [IMPROVEMENTS.md](./IMPROVEMENTS.md) pour plus de détails sur chaque fonctionnalité.
