# 📧 Email Campaign Platform - Enterprise Edition

Plateforme complète de gestion de campagnes email avec fonctionnalités avancées de niveau entreprise.

## 🚀 Nouveautés - Version 2.0

Cette version apporte **12 améliorations majeures** transformant l'application en une solution enterprise-ready:

✅ **A/B Testing** avec signification statistique  
✅ **Segmentation avancée** avec filtres dynamiques  
✅ **Analytics & Dashboards** complets  
✅ **Gestion automatique des bounces**  
✅ **Rate limiting** & protection anti-abus  
✅ **Observabilité** complète (logs, métriques, tracing)  
✅ **Optimisations de performance** (cache, pagination, bulk ops)  
✅ **Tests automatisés** (50+ tests)  
✅ **Queue Celery** pour traitement distribué  
✅ **Dark mode** & **i18n** (4 langues)  
✅ **Éditeur WYSIWYG** professionnel  
✅ **Sécurité renforcée** (secrets, headers, HTTPS)

## 📋 Stack Technique

**Backend:**
- FastAPI 0.104.1 + Python 3.11
- Supabase (PostgreSQL)
- Redis 7 (cache & message broker)
- Celery 5.3.4 (background tasks)
- Prometheus (métriques)

**Frontend:**
- React 18.2.0
- TypeScript 5.2.2
- Vite 5.0.8
- Dark mode & i18n intégrés

**Infrastructure:**
- Docker & Docker Compose
- nginx (reverse proxy)
- Traefik-ready

**Email Provider:**
- SMTP générique (unique provider)

## ⚡ Démarrage Rapide

### Prérequis

- Docker & Docker Compose
- Compte Supabase
- Un accès SMTP (hôte, port, identifiants)

### Installation en 5 minutes

```bash
# 1. Cloner et accéder au projet
cd Email

# 2. Copier et configurer l'environnement
cd backend
cp .env.example .env
# Éditer .env avec vos clés

# 3. Démarrer avec Docker (inclut Redis, Celery, etc.)
cd ..
docker-compose -f docker-compose.full.yml up -d

# 4. Appliquer les migrations Supabase
# Via SQL Editor sur https://app.supabase.com
# Exécuter: supabase/migrations/20241215000001_create_email_campaign_schema.sql
# Exécuter: supabase/migrations/20241216000001_add_abtesting_segmentation_tables.sql

# 5. Vérifier que tout fonctionne
curl http://localhost:8000/health
```

### Accès

- **Frontend**: http://localhost
- **API Backend**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **Flower (Celery monitoring)**: http://localhost:5555
- **Prometheus Metrics**: http://localhost:8000/metrics

## 📚 Documentation Complète

| Document | Description |
|----------|-------------|
| [QUICK_START_GUIDE.md](./QUICK_START_GUIDE.md) | Guide de démarrage détaillé avec exemples |
| [COMPLETE_IMPROVEMENTS.md](./COMPLETE_IMPROVEMENTS.md) | Documentation de toutes les améliorations |
| [DEPLOYMENT_CHECKLIST.md](./DEPLOYMENT_CHECKLIST.md) | Checklist de déploiement en production |
| [FINAL_REPORT.md](./FINAL_REPORT.md) | Rapport de projet complet |

## 🎯 Fonctionnalités Principales

### 1. Gestion de Campagnes Email

- Création/édition/suppression de campagnes
- Templates avec variables `{{name}}`, `{{email}}`, etc.
- Éditeur WYSIWYG intégré
- Upload CSV de destinataires
- Planification d'envoi
- Tracking (ouvertures, clics, unsubscribe)

### 2. A/B Testing

```bash
# Créer un test A/B
POST /v1/campaigns/{id}/ab-test
{
  "name": "Test sujet",
  "variants": [
    {"name": "A", "subject": "🎁 Offre spéciale"},
    {"name": "B", "subject": "Promotion limitée"}
  ],
  "traffic_split": {"A": 0.5, "B": 0.5},
  "auto_select_winner": true
}
```

- Tests A/B/n (plusieurs variantes)
- Distribution de trafic configurable
- Calcul de signification statistique (Z-test)
- Sélection automatique du gagnant
- Métriques: open_rate, click_rate, conversion_rate

### 3. Segmentation Avancée

```bash
# Créer un segment dynamique
POST /v1/segments
{
  "name": "Utilisateurs Gmail actifs",
  "segment_type": "dynamic",
  "filters": {
    "logic": "and",
    "conditions": [
      {"field": "email", "operator": "ends_with", "value": "@gmail.com"},
      {"field": "status", "operator": "equals", "value": "sent"}
    ]
  }
}
```

- Segments statiques (manuels) et dynamiques (filtres)
- 12+ opérateurs de filtrage
- Tags pour organisation
- Liste de suppression globale
- Filtrage automatique avant envoi

### 4. Analytics & Dashboards

```bash
# Consulter analytics
GET /v1/campaigns/{id}/analytics/domains
GET /v1/analytics/heatmap?start_date=2024-12-01
GET /v1/analytics/bounces
GET /v1/analytics/trends?period=7d
```

- Stats par domaine (Gmail, Outlook, etc.)
- Heatmap d'engagement (jour/heure)
- Analyse des bounces
- Tendances temporelles
- Score d'engagement par destinataire
- Comparaison de campagnes

### 5. Gestion des Bounces

- Classification automatique hard/soft
- Gestion des bounces via réponses SMTP + suppression automatique
- Suppression automatique après seuils
- Alertes administrateur
- Statistiques détaillées

### 6. Observabilité

- Logs structurés JSON
- Métriques Prometheus (requêtes, latence, etc.)
- Tracing distribué avec request_id
- Health checks détaillés
- Monitoring Celery via Flower

## 🔧 Configuration

### Variables d'Environnement Principales

```bash
# Supabase
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_SERVICE_ROLE_KEY=xxx

# Email Provider (SMTP uniquement)
EMAIL_PROVIDER=smtp
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-smtp-username
SMTP_PASSWORD=your-smtp-password
SMTP_USE_TLS=true

# Redis
REDIS_URL=redis://localhost:6379/0

# Celery
CELERY_BROKER_URL=redis://localhost:6379/0

# Sécurité
RATE_LIMIT_ENABLED=true
SECRET_KEY=xxx

# Observabilité
ENABLE_METRICS=true
LOG_LEVEL=INFO
```

Voir [.env.example](./backend/.env.example) pour la liste complète.

## 🧪 Tests

```bash
cd backend

# Tous les tests
pytest tests/test_all.py -v

# Avec couverture
pytest tests/test_all.py --cov=backend --cov-report=html

# Tests spécifiques
pytest tests/test_all.py::TestABTestingStats -v
```

## 🚀 Déploiement

### Option 1: Docker Compose (Recommandé)

```bash
# Production avec tous les services
docker-compose -f docker-compose.full.yml up -d

# Services démarrés:
# - backend (API)
# - frontend (nginx)
# - redis (cache)
# - celery_worker (background tasks)
# - celery_beat (scheduler)
# - flower (monitoring)
```

### Option 2: Sans Docker

```bash
# Terminal 1: Redis
redis-server

# Terminal 2: Backend
cd backend
uvicorn main:app --host 0.0.0.0 --port 8000

# Terminal 3: Celery Worker
celery -A core.celery_tasks worker --loglevel=info

# Terminal 4: Celery Beat
celery -A core.celery_tasks beat --loglevel=info

# Terminal 5: Frontend
cd frontend
npm run dev
```

## 📊 Monitoring

### Prometheus Metrics

```bash
curl http://localhost:8000/metrics
```

Métriques disponibles:
- `http_requests_total` - Compteur de requêtes
- `http_request_duration_seconds` - Latence
- `http_requests_in_progress` - Requêtes actives

### Celery Monitoring (Flower)

Accéder à http://localhost:5555 pour:
- Voir les workers actifs
- Monitorer les queues
- Analyser les tâches
- Consulter l'historique

### Health Check

```bash
curl http://localhost:8000/health

# Retourne:
{
  "status": "healthy",
  "checks": {
    "supabase": {"healthy": true, "latency_ms": 45},
    "redis": {"healthy": true, "latency_ms": 2},
    "scheduler": {"healthy": true},
    "email": {"healthy": true}
  }
}
```

## 🌐 Frontend - Nouvelles Fonctionnalités

### Dark Mode

```tsx
import { ThemeProvider, ThemeToggle } from '@/hooks/useTheme';

<ThemeProvider>
  <ThemeToggle />
  <YourApp />
</ThemeProvider>
```

### Internationalisation (FR, EN, ES, DE)

```tsx
import { useTranslation } from '@/hooks/useTranslation';

const { t, changeLanguage } = useTranslation();
<h1>{t('campaigns.title')}</h1>
```

### Éditeur WYSIWYG

```tsx
import { EmailEditor } from '@/components/EmailEditor';

<EmailEditor
  value={content}
  onChange={setContent}
  onInsertVariable={(var) => console.log(var)}
/>
```

## 🔐 Sécurité

- Rate limiting (100 req/min par défaut)
- Protection anti-abus
- Headers de sécurité (CSP, HSTS, etc.)
- Validation des secrets au démarrage
- Webhook signature verification
- CORS configuré
- Row Level Security (Supabase)

## 🏗️ Architecture

```
┌─────────────┐
│  Frontend   │ ← React + Vite + TypeScript
│  (nginx)    │
└──────┬──────┘
       │
┌──────▼──────┐
│  Backend    │ ← FastAPI + Python
│  (API)      │
└──────┬──────┘
       │
┌──────▼──────────────────┐
│  Services               │
├─────────────────────────┤
│ Redis  │ Supabase      │
│ Celery │ Email Provider│
└─────────────────────────┘
```

## 📈 Performance

- Cache Redis pour requêtes fréquentes
- Pagination curseur pour grandes listes
- Opérations bulk (insert/update/delete)
- Traitement par batch asynchrone
- Compression gzip
- Indexes DB optimisés

## 🆘 Support & Troubleshooting

### Problèmes Courants

**Emails non envoyés?**
- Vérifier API key email provider
- Vérifier Celery worker actif: `docker-compose logs celery_worker`

**Webhooks non reçus?**
- Vérifier URL accessible publiquement
- Vérifier signature configurée

**Performance lente?**
- Vérifier cache Redis actif
- Analyser slow queries dans Supabase

Voir [DEPLOYMENT_CHECKLIST.md](./DEPLOYMENT_CHECKLIST.md) pour plus de détails.

## 🤝 Contribution

1. Fork le projet
2. Créer une branche (`git checkout -b feature/AmazingFeature`)
3. Commit (`git commit -m 'Add some AmazingFeature'`)
4. Push (`git push origin feature/AmazingFeature`)
5. Ouvrir une Pull Request

## 📝 License

Projet propriétaire - Tous droits réservés

## 🎉 Crédits

Développé avec ❤️ en utilisant:
- FastAPI
- React
- Supabase
- Celery
- Redis
- Et bien d'autres technologies open-source

---

**Version**: 2.0.0  
**Dernière mise à jour**: Décembre 2024

Pour plus d'informations, consultez la [documentation complète](./COMPLETE_IMPROVEMENTS.md).
