# 🚀 Guide de Démarrage Rapide - Nouvelles Fonctionnalités

Ce guide vous permet de démarrer rapidement avec toutes les nouvelles fonctionnalités implémentées.

## 📋 Prérequis

- Docker & Docker Compose
- Python 3.11+
- Node.js 18+
- Compte Supabase
- Redis (optionnel mais recommandé)

## ⚡ Démarrage Rapide

### 1. Installation des Dépendances

```bash
# Backend
cd backend
pip install -r requirements.txt

# Frontend
cd ../frontend
npm install
```

### 2. Configuration

Créer un fichier `.env` à la racine du backend:

```bash
# === CORE ===
DEBUG=true
APP_NAME="Email Campaign Platform"
ALLOWED_ORIGINS=http://localhost:5173,http://localhost:3000

# === SUPABASE ===
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-key
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key

# === EMAIL PROVIDER (choisir un) ===
EMAIL_PROVIDER=sendgrid
# SendGrid
SENDGRID_API_KEY=SG.xxxxx
SENDGRID_WEBHOOK_VERIFICATION_KEY=your-webhook-key

# Mailgun
# MAILGUN_API_KEY=key-xxxxx
# MAILGUN_DOMAIN=mg.yourdomain.com

# AWS SES
# AWS_ACCESS_KEY_ID=AKIA...
# AWS_SECRET_ACCESS_KEY=xxxxx
# AWS_REGION=us-east-1
# AWS_SES_CONFIGURATION_SET=email-campaign

# === REDIS (recommandé) ===
REDIS_URL=redis://localhost:6379/0

# === CELERY ===
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/1

# === RATE LIMITING ===
RATE_LIMIT_ENABLED=true
RATE_LIMIT_PER_MINUTE=100

# === OBSERVABILITY ===
ENABLE_METRICS=true
LOG_LEVEL=INFO
```

### 3. Appliquer la Migration

```bash
# Via Supabase CLI
supabase db push

# OU via l'interface Supabase
# 1. Aller sur https://app.supabase.com
# 2. Ouvrir SQL Editor
# 3. Copier/coller le contenu de:
#    supabase/migrations/20241216000001_add_abtesting_segmentation_tables.sql
# 4. Exécuter
```

### 4. Démarrer les Services

#### Option A: Avec Docker (Recommandé)

```bash
# Démarrer tous les services
docker-compose up -d

# Vérifier les logs
docker-compose logs -f backend
```

#### Option B: Sans Docker

```bash
# Terminal 1: Redis
redis-server

# Terminal 2: Backend API
cd backend
uvicorn main:app --reload --port 8000

# Terminal 3: Celery Worker
cd backend
celery -A core.celery_tasks worker --loglevel=info

# Terminal 4: Celery Beat (scheduler)
cd backend
celery -A core.celery_tasks beat --loglevel=info

# Terminal 5: Frontend
cd frontend
npm run dev
```

### 5. Vérifier le Démarrage

```bash
# Health check complet
curl http://localhost:8000/health

# Devrait retourner:
{
  "status": "healthy",
  "timestamp": "2024-12-16T...",
  "checks": {
    "supabase": {"healthy": true},
    "redis": {"healthy": true},
    "scheduler": {"healthy": true},
    "email": {"healthy": true}
  }
}
```

## 🎯 Tester les Nouvelles Fonctionnalités

### 1. Créer un Segment Dynamique

```bash
curl -X POST http://localhost:8000/v1/segments \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Gmail Users",
    "segment_type": "dynamic",
    "description": "All Gmail recipients",
    "filters": {
      "logic": "and",
      "conditions": [
        {
          "field": "email",
          "operator": "ends_with",
          "value": "@gmail.com"
        }
      ]
    }
  }'
```

### 2. Créer un Test A/B

```bash
# D'abord créer une campagne
CAMPAIGN_ID=$(curl -X POST http://localhost:8000/v1/campaigns \
  -H "Content-Type: application/json" \
  -d '{
    "name": "My Campaign",
    "subject": "Test",
    "content": "<h1>Hello</h1>"
  }' | jq -r '.id')

# Puis créer le test A/B
curl -X POST http://localhost:8000/v1/campaigns/$CAMPAIGN_ID/ab-test \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Subject Line Test",
    "variants": [
      {
        "name": "A",
        "subject": "🎁 Special Offer Inside",
        "content": "<h1>Variant A</h1>"
      },
      {
        "name": "B",
        "subject": "Limited Time Deal",
        "content": "<h1>Variant B</h1>"
      }
    ],
    "traffic_split": {"A": 0.5, "B": 0.5},
    "primary_metric": "open_rate",
    "auto_select_winner": true,
    "min_sample_size": 100,
    "confidence_level": 0.95
  }'
```

### 3. Ajouter des Emails à la Suppression List

```bash
curl -X POST http://localhost:8000/v1/suppression \
  -H "Content-Type: application/json" \
  -d '{
    "entries": [
      {
        "email": "bounce@example.com",
        "source": "manual",
        "reason": "Hard bounce"
      }
    ]
  }'
```

### 4. Consulter les Analytics

```bash
# Stats par domaine
curl http://localhost:8000/v1/campaigns/$CAMPAIGN_ID/analytics/domains

# Heatmap d'engagement
curl "http://localhost:8000/v1/analytics/heatmap?start_date=2024-12-01&end_date=2024-12-16"

# Analyse des bounces
curl http://localhost:8000/v1/analytics/bounces
```

### 5. Créer des Tags

```bash
# Créer un tag
curl -X POST http://localhost:8000/v1/tags \
  -H "Content-Type: application/json" \
  -d '{
    "name": "VIP",
    "color": "#FFD700",
    "description": "VIP customers"
  }'

# Assigner des tags à des recipients
curl -X POST http://localhost:8000/v1/tags/assign \
  -H "Content-Type: application/json" \
  -d '{
    "recipient_ids": ["uuid1", "uuid2"],
    "tags": ["VIP", "Active"]
  }'
```

## 🧪 Lancer les Tests

```bash
cd backend

# Tous les tests
pytest tests/test_all.py -v

# Avec couverture
pytest tests/test_all.py --cov=backend --cov-report=html

# Tests spécifiques
pytest tests/test_all.py::TestABTestingStats -v
pytest tests/test_all.py::TestSegmentationFilters -v
```

## 📊 Monitoring

### Métriques Prometheus

```bash
# Endpoint métriques
curl http://localhost:8000/metrics

# Exemple de sortie:
# http_requests_total{method="GET",path="/health",status="200"} 42
# http_request_duration_seconds_count 100
# http_requests_in_progress 2
```

### Logs Structurés

Les logs en production sont en format JSON:

```json
{
  "timestamp": "2024-12-16T10:30:00.123Z",
  "level": "INFO",
  "logger": "app.main",
  "message": "Campaign started",
  "request_id": "abc-123",
  "campaign_id": "uuid",
  "recipient_count": 1000
}
```

## 🎨 Frontend - Nouvelles Fonctionnalités

### Dark Mode

```tsx
import { ThemeProvider, ThemeToggle } from '@/hooks/useTheme';

function App() {
  return (
    <ThemeProvider>
      <header>
        <ThemeToggle />
      </header>
      <YourApp />
    </ThemeProvider>
  );
}
```

### Internationalisation

```tsx
import { useTranslation } from '@/hooks/useTranslation';

function Component() {
  const { t, changeLanguage } = useTranslation();
  
  return (
    <div>
      <h1>{t('campaigns.title')}</h1>
      <button onClick={() => changeLanguage('en')}>
        English
      </button>
    </div>
  );
}
```

### Éditeur WYSIWYG

```tsx
import { EmailEditor } from '@/components/EmailEditor';

function CampaignForm() {
  const [content, setContent] = useState('');
  
  return (
    <EmailEditor
      value={content}
      onChange={setContent}
      onInsertVariable={(variable) => {
        setContent(prev => prev + `{{${variable}}}`);
      }}
    />
  );
}
```

## 🔧 Configuration Webhooks

### SendGrid

1. Aller sur https://app.sendgrid.com/settings/mail_settings
2. Créer un webhook Event Webhook
3. URL: `https://your-domain.com/v1/webhooks/sendgrid`
4. Sélectionner les événements: Bounced, Dropped, Spam Report, Delivered, Open, Click
5. Copier la clé de vérification dans `.env`

### Mailgun

1. Aller sur https://app.mailgun.com/app/webhooks
2. Créer un nouveau webhook
3. URL: `https://your-domain.com/v1/webhooks/mailgun`
4. Sélectionner les événements
5. La clé de signature est votre API key

### AWS SES

1. Créer un topic SNS
2. Souscrire avec: `https://your-domain.com/v1/webhooks/ses`
3. Confirmer la souscription
4. Configurer SES pour publier dans le topic

## 🐛 Dépannage

### Redis non accessible

L'application fonctionne sans Redis mais avec performances réduites:
- Rate limiting: fallback en mémoire
- Cache: désactivé
- Celery: ne fonctionnera pas

### Erreur de migration

```bash
# Reset la migration (ATTENTION: perte de données)
supabase db reset

# Ou appliquer manuellement
supabase db push --dry-run  # Preview
supabase db push            # Apply
```

### Rate limiting trop restrictif

Modifier dans `.env`:
```bash
RATE_LIMIT_PER_MINUTE=1000
```

Ou désactiver temporairement:
```bash
RATE_LIMIT_ENABLED=false
```

## 📚 Documentation Complète

- [COMPLETE_IMPROVEMENTS.md](./COMPLETE_IMPROVEMENTS.md) - Toutes les améliorations détaillées
- [FINAL_REPORT.md](./FINAL_REPORT.md) - Rapport de projet
- API Docs: http://localhost:8000/docs (en mode DEBUG)

## 🆘 Support

En cas de problème:

1. Vérifier les logs: `docker-compose logs backend`
2. Vérifier le health check: `curl http://localhost:8000/health`
3. Vérifier la documentation: `/docs`
4. Consulter les tests pour des exemples: `backend/tests/test_all.py`

## 🎉 Prêt à Démarrer!

Votre plateforme Email Campaign est maintenant configurée avec:

✅ A/B Testing  
✅ Segmentation avancée  
✅ Analytics & dashboards  
✅ Gestion des bounces  
✅ Rate limiting  
✅ Observabilité complète  
✅ Dark mode & i18n  
✅ Éditeur WYSIWYG  

**Bon envoi d'emails!** 📧🚀
