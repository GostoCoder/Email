# 📡 API Reference - Email Campaign Platform

Documentation complète de tous les endpoints API disponibles.

**Base URL**: `http://localhost:8000/v1`

**Authentication**: Les endpoints requièrent généralement un token d'authentification (sauf webhooks).

---

## 📋 Table des Matières

1. [Health & Status](#health--status)
2. [Campaigns](#campaigns)
3. [A/B Testing](#ab-testing)
4. [Analytics](#analytics)
5. [Segmentation](#segmentation)
6. [Tags](#tags)
7. [Suppression List](#suppression-list)
8. [Bounces & Webhooks](#bounces--webhooks)

---

## Health & Status

### GET /health

Health check complet de l'application.

**Response 200**:
```json
{
  "status": "healthy",
  "timestamp": "2024-12-16T10:30:00Z",
  "version": "0.1.0",
  "checks": {
    "supabase": {
      "healthy": true,
      "latency_ms": 45.23,
      "message": "Connected"
    },
    "redis": {
      "healthy": true,
      "latency_ms": 2.15,
      "message": "Connected"
    },
    "scheduler": {
      "healthy": true,
      "message": "Running with 3 jobs"
    },
    "email": {
      "healthy": true,
      "message": "Using sendgrid"
    }
  }
}
```

### GET /health/live

Liveness probe (Kubernetes).

### GET /health/ready

Readiness probe (Kubernetes).

### GET /metrics

Prometheus metrics endpoint.

**Response**: Format Prometheus
```
http_requests_total{method="GET",path="/health",status="200"} 42
http_request_duration_seconds_count 100
```

---

## Campaigns

### POST /v1/campaigns

Créer une nouvelle campagne.

**Request Body**:
```json
{
  "name": "Newsletter Q4",
  "subject": "Our latest updates",
  "content": "<h1>Hello {{name}}</h1>",
  "from_email": "news@company.com",
  "from_name": "Company Newsletter",
  "reply_to": "support@company.com",
  "scheduled_at": "2024-12-20T10:00:00Z"
}
```

**Response 201**:
```json
{
  "id": "uuid",
  "name": "Newsletter Q4",
  "status": "draft",
  "created_at": "2024-12-16T10:00:00Z"
}
```

### GET /v1/campaigns

Lister toutes les campagnes.

**Query Parameters**:
- `status` (optional): `draft`, `scheduled`, `running`, `completed`
- `limit` (optional): Nombre de résultats (défaut: 50)
- `offset` (optional): Pagination

### GET /v1/campaigns/{id}

Obtenir les détails d'une campagne.

### PATCH /v1/campaigns/{id}

Mettre à jour une campagne.

### DELETE /v1/campaigns/{id}

Supprimer une campagne.

### POST /v1/campaigns/{id}/start

Démarrer l'envoi d'une campagne.

### POST /v1/campaigns/{id}/recipients/import

Importer des destinataires via CSV.

**Request**:
- Content-Type: `multipart/form-data`
- Field: `file` (CSV avec colonnes: email, name, custom_fields...)

---

## A/B Testing

### POST /v1/campaigns/{id}/ab-test

Créer un test A/B pour une campagne.

**Request Body**:
```json
{
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
  "traffic_split": {
    "A": 0.5,
    "B": 0.5
  },
  "primary_metric": "open_rate",
  "auto_select_winner": true,
  "min_sample_size": 100,
  "confidence_level": 0.95
}
```

**Response 201**:
```json
{
  "id": "uuid",
  "campaign_id": "uuid",
  "name": "Subject Line Test",
  "status": "running",
  "variants": [...],
  "created_at": "2024-12-16T10:00:00Z"
}
```

### GET /v1/ab-tests/{id}

Obtenir les détails d'un test A/B.

### GET /v1/ab-tests/{id}/results

Obtenir les résultats statistiques d'un test A/B.

**Response 200**:
```json
{
  "test_id": "uuid",
  "status": "running",
  "variants": [
    {
      "name": "A",
      "recipients": 500,
      "opens": 150,
      "clicks": 45,
      "open_rate": 0.30,
      "click_rate": 0.09,
      "is_significant": true,
      "p_value": 0.03
    },
    {
      "name": "B",
      "recipients": 500,
      "opens": 175,
      "clicks": 60,
      "open_rate": 0.35,
      "click_rate": 0.12,
      "is_significant": true,
      "p_value": 0.03
    }
  ],
  "winner": "B",
  "confidence_level": 0.95
}
```

### POST /v1/ab-tests/{id}/select-winner

Sélectionner manuellement le gagnant (ou confirmer la sélection auto).

**Request Body**:
```json
{
  "winner_variant": "B"
}
```

### GET /v1/campaigns/{id}/ab-tests

Lister tous les tests A/B d'une campagne.

---

## Analytics

### GET /v1/campaigns/{id}/analytics/domains

Statistiques par domaine email.

**Response 200**:
```json
{
  "campaign_id": "uuid",
  "domains": [
    {
      "domain": "gmail.com",
      "recipients": 5000,
      "opens": 1500,
      "clicks": 450,
      "bounces": 50,
      "open_rate": 0.30,
      "click_rate": 0.09,
      "bounce_rate": 0.01
    },
    {
      "domain": "outlook.com",
      "recipients": 3000,
      "opens": 900,
      "clicks": 270,
      "bounces": 30,
      "open_rate": 0.30,
      "click_rate": 0.09,
      "bounce_rate": 0.01
    }
  ]
}
```

### GET /v1/analytics/heatmap

Heatmap d'engagement (jour de semaine × heure).

**Query Parameters**:
- `start_date`: Date de début (ISO 8601)
- `end_date`: Date de fin (ISO 8601)
- `campaign_id` (optional): Filtrer par campagne

**Response 200**:
```json
{
  "heatmap": {
    "Monday": {
      "00:00": 0.15,
      "01:00": 0.10,
      ...
      "23:00": 0.12
    },
    "Tuesday": {...},
    ...
  }
}
```

### GET /v1/analytics/bounces

Analyse des bounces.

**Response 200**:
```json
{
  "total_bounces": 150,
  "hard_bounces": 100,
  "soft_bounces": 50,
  "by_reason": {
    "mailbox_full": 30,
    "mailbox_not_found": 70,
    "blocked": 20,
    "other": 30
  },
  "bounce_rate": 0.015
}
```

### GET /v1/analytics/trends

Tendances de campagnes dans le temps.

**Query Parameters**:
- `period`: `7d`, `30d`, `90d`
- `metric`: `open_rate`, `click_rate`, `bounce_rate`

### GET /v1/analytics/engagement/{email}

Score d'engagement pour un destinataire.

**Response 200**:
```json
{
  "email": "user@example.com",
  "engagement_score": 85,
  "total_sent": 50,
  "total_opens": 40,
  "total_clicks": 25,
  "last_activity": "2024-12-15T14:30:00Z",
  "segments": ["Active Users", "VIP"]
}
```

### POST /v1/analytics/compare

Comparer plusieurs campagnes.

**Request Body**:
```json
{
  "campaign_ids": ["uuid1", "uuid2", "uuid3"]
}
```

**Response 200**:
```json
{
  "campaigns": [
    {
      "id": "uuid1",
      "name": "Campaign A",
      "sent": 10000,
      "open_rate": 0.25,
      "click_rate": 0.08,
      "bounce_rate": 0.02
    },
    ...
  ]
}
```

---

## Segmentation

### POST /v1/segments

Créer un segment.

**Request Body**:
```json
{
  "name": "Active Gmail Users",
  "segment_type": "dynamic",
  "description": "Users with Gmail who opened last campaign",
  "filters": {
    "logic": "and",
    "conditions": [
      {
        "field": "email",
        "operator": "ends_with",
        "value": "@gmail.com"
      },
      {
        "field": "last_open",
        "operator": "greater_than",
        "value": "2024-12-01"
      }
    ]
  },
  "tags": ["active", "gmail"]
}
```

**Operators disponibles**:
- `equals`, `not_equals`
- `contains`, `not_contains`
- `starts_with`, `ends_with`
- `in_list`, `not_in_list`
- `greater_than`, `less_than`
- `is_null`, `is_not_null`
- `regex`

**Response 201**:
```json
{
  "id": "uuid",
  "name": "Active Gmail Users",
  "segment_type": "dynamic",
  "recipient_count": 1234,
  "created_at": "2024-12-16T10:00:00Z"
}
```

### GET /v1/segments

Lister tous les segments.

**Query Parameters**:
- `segment_type`: `static` ou `dynamic`
- `tag`: Filtrer par tag

### GET /v1/segments/{id}

Obtenir les détails d'un segment.

### PATCH /v1/segments/{id}

Mettre à jour un segment.

### DELETE /v1/segments/{id}

Supprimer un segment.

### POST /v1/segments/{id}/refresh

Rafraîchir le compteur de destinataires (segments dynamiques).

### GET /v1/segments/{id}/recipients

Obtenir les destinataires d'un segment.

**Query Parameters**:
- `limit`: Nombre de résultats (défaut: 100)
- `offset`: Pagination

---

## Tags

### POST /v1/tags

Créer un tag.

**Request Body**:
```json
{
  "name": "VIP",
  "color": "#FFD700",
  "description": "VIP customers"
}
```

### GET /v1/tags

Lister tous les tags avec compteurs d'utilisation.

### POST /v1/tags/assign

Assigner des tags à des destinataires.

**Request Body**:
```json
{
  "recipient_ids": ["uuid1", "uuid2"],
  "tags": ["VIP", "Active"]
}
```

### POST /v1/tags/remove

Retirer des tags de destinataires.

### GET /v1/tags/{tag}/recipients

Obtenir tous les destinataires avec un tag spécifique.

---

## Suppression List

### POST /v1/suppression

Ajouter des emails à la liste de suppression.

**Request Body**:
```json
{
  "entries": [
    {
      "email": "bounce@example.com",
      "source": "manual",
      "reason": "Hard bounce"
    },
    {
      "email": "spam@example.com",
      "source": "complaint",
      "reason": "Spam report"
    }
  ]
}
```

**Response 200**:
```json
{
  "added": 2,
  "already_suppressed": 0,
  "errors": []
}
```

### DELETE /v1/suppression/{email}

Retirer un email de la liste de suppression.

### GET /v1/suppression/check/{email}

Vérifier si un email est supprimé.

**Response 200**:
```json
{
  "email": "test@example.com",
  "is_suppressed": false
}
```

### POST /v1/suppression/filter

Filtrer une liste d'emails (retirer les supprimés).

**Request Body**:
```json
{
  "emails": ["user1@example.com", "suppressed@example.com", "user2@example.com"]
}
```

**Response 200**:
```json
{
  "original_count": 3,
  "allowed_count": 2,
  "suppressed_count": 1,
  "allowed_emails": ["user1@example.com", "user2@example.com"]
}
```

### GET /v1/suppression

Lister les entrées de suppression.

**Query Parameters**:
- `source`: `manual`, `bounce`, `complaint`, etc.
- `limit`, `offset`: Pagination

### GET /v1/suppression/stats

Statistiques de la liste de suppression.

**Response 200**:
```json
{
  "total": 1500,
  "by_source": {
    "bounce": 800,
    "complaint": 200,
    "manual": 500
  },
  "by_reason": {
    "hard_bounce": 600,
    "spam_report": 200,
    "unsubscribe": 700
  }
}
```

---

## Bounces & Webhooks

### POST /v1/webhooks/sendgrid

Webhook pour SendGrid (événements email).

**Headers**:
- `X-Twilio-Email-Event-Webhook-Signature`
- `X-Twilio-Email-Event-Webhook-Timestamp`

**Événements traités**:
- bounce, dropped (hard/soft bounces)
- spam_report (plaintes)
- delivered
- open, click
- unsubscribe

### POST /v1/webhooks/mailgun

Webhook pour Mailgun.

**Événements traités**:
- bounced, failed, rejected
- complained
- delivered
- opened, clicked
- unsubscribed

### POST /v1/webhooks/ses

Webhook pour AWS SES (via SNS).

**Types de notifications**:
- Bounce
- Complaint
- Delivery

### GET /v1/bounces/stats

Statistiques des bounces.

**Query Parameters**:
- `days`: Période (défaut: 30)

**Response 200**:
```json
{
  "period_days": 30,
  "total_bounces": 150,
  "hard_bounces": 100,
  "soft_bounces": 50,
  "by_domain": {
    "gmail.com": 50,
    "outlook.com": 30
  },
  "by_type": {
    "hard": 100,
    "soft": 50
  }
}
```

### GET /v1/bounces/suppressed

Liste des emails supprimés suite à bounces.

### POST /v1/bounces/test

(DEBUG only) Simuler un bounce pour tests.

**Request Body**:
```json
{
  "email": "test@example.com",
  "bounce_type": "hard"
}
```

---

## Rate Limiting

Toutes les requêtes sont soumises au rate limiting:

- **Général**: 100 requêtes/minute
- **Auth**: 10 requêtes/minute
- **Upload**: 20 requêtes/minute

**Headers de réponse**:
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1702731600
```

**Response 429** (trop de requêtes):
```json
{
  "detail": "Rate limit exceeded. Try again in 30 seconds."
}
```

---

## Codes d'Erreur

| Code | Description |
|------|-------------|
| 200 | Succès |
| 201 | Créé |
| 204 | Pas de contenu (suppression réussie) |
| 400 | Requête invalide |
| 401 | Non authentifié |
| 403 | Accès refusé |
| 404 | Ressource non trouvée |
| 422 | Validation échouée |
| 429 | Rate limit dépassé |
| 500 | Erreur serveur |
| 503 | Service indisponible |

---

## Pagination

Pour les endpoints qui retournent des listes:

**Query Parameters**:
- `limit`: Nombre de résultats (défaut: 50, max: 1000)
- `offset`: Position de départ
- `cursor`: Pour pagination curseur (recommandé)

**Response**:
```json
{
  "items": [...],
  "total": 1234,
  "limit": 50,
  "offset": 0,
  "next_cursor": "eyJpZCI6MTIzfQ=="
}
```

---

## Exemples cURL

### Créer une campagne

```bash
curl -X POST http://localhost:8000/v1/campaigns \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test Campaign",
    "subject": "Hello",
    "content": "<h1>Hi {{name}}</h1>"
  }'
```

### Créer un test A/B

```bash
curl -X POST http://localhost:8000/v1/campaigns/{campaign_id}/ab-test \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Subject Test",
    "variants": [
      {"name": "A", "subject": "Offer A"},
      {"name": "B", "subject": "Offer B"}
    ],
    "traffic_split": {"A": 0.5, "B": 0.5},
    "auto_select_winner": true
  }'
```

### Vérifier la santé

```bash
curl http://localhost:8000/health
```

---

## Webhooks - Configuration

### SendGrid

1. Dashboard → Settings → Mail Settings → Event Webhook
2. URL: `https://yourdomain.com/v1/webhooks/sendgrid`
3. Événements: Bounced, Dropped, Spam Reports, Delivered, Opened, Clicked

### Mailgun

1. Dashboard → Webhooks
2. URL: `https://yourdomain.com/v1/webhooks/mailgun`
3. Événements: Permanent Failure, Temporary Failure, Complained, Delivered, Opened, Clicked

### AWS SES

1. Créer un SNS topic
2. Configurer SES pour publier dans le topic
3. Souscrire avec: `https://yourdomain.com/v1/webhooks/ses`

---

## Documentation Interactive

Accéder à la documentation Swagger interactive:

**URL**: http://localhost:8000/docs (en mode DEBUG)

Permet de tester tous les endpoints directement dans le navigateur.

---

**Version API**: 1.0  
**Dernière mise à jour**: Décembre 2024

Pour plus de détails, voir [COMPLETE_IMPROVEMENTS.md](./COMPLETE_IMPROVEMENTS.md)
