# 📧 Application de Campagnes d'Emailing

Une application professionnelle de gestion de campagnes d'emailing à grande échelle, conforme GDPR/CAN-SPAM/CASL.

## 🚀 Fonctionnalités

### ✅ Gestion des Campagnes
- Création et édition de campagnes d'emailing
- Templates HTML personnalisables avec variables dynamiques
- Gestion du cycle de vie : brouillon → planifiée → envoi → terminée
- Pause et reprise des campagnes en cours

### 📊 Import de Contacts
- Import CSV avec validation automatique
- Détection des doublons et emails invalides
- Prévisualisation avant importation
- Mapping automatique des colonnes

### 🎨 Personnalisation
- Variables dynamiques : `{{firstname}}`, `{{lastname}}`, `{{company}}`
- Templates HTML réutilisables
- Prévisualisation en temps réel
- Validation du rendu email

### 📈 Suivi en Temps Réel
- Barre de progression pendant l'envoi
- Statistiques détaillées (envoyés, ouvertures, clics)
- Logs d'erreurs avec détails
- Taux de délivrabilité et engagement

### 🔐 Conformité Légale
- **Lien de désinscription obligatoire** dans chaque email
- Headers `List-Unsubscribe` pour clients email natifs
- Page de désinscription publique simple et claire
- Respect GDPR, CAN-SPAM, CASL
- Blacklist globale des désinscrits

### ⚡ Performance
- Envoi asynchrone en batch
- Rate limiting configurable
- Retry automatique en cas d'échec
- Scalable à grande échelle

## 🏗️ Architecture

### Stack Technique

**Frontend:**
- React 18 + TypeScript
- Vite
- CSS moderne avec variables

**Backend:**
- Python 3.11+
- FastAPI (API REST asynchrone)
- Pydantic pour validation

**Base de données:**
- PostgreSQL via Supabase
- Row Level Security (RLS)
- Triggers et fonctions SQL

**Services Externes:**
- SendGrid / Mailgun / AWS SES (envoi d'emails)
- Supabase Storage (fichiers CSV)

## 📋 Prérequis

- Python 3.11+
- Node.js 18+
- PostgreSQL (ou compte Supabase)
- Compte SendGrid ou Mailgun

## 🔧 Installation

### 1. Cloner le repository

```bash
git clone <repo-url>
cd App_starter
```

### 2. Configuration Backend

```bash
cd backend

# Créer un environnement virtuel
python -m venv venv
source venv/bin/activate  # Sur Windows: venv\Scripts\activate

# Installer les dépendances
pip install -r requirements.txt

# Créer le fichier .env
cp .env.example .env
```

**Configuration `.env`:**

```env
# Application
APP_NAME=email-campaign-manager
APP_ENV=development
ALLOWED_ORIGINS=["http://localhost:3000"]

# Supabase
SUPABASE_URL=https://xxxxx.supabase.co
SUPABASE_ANON_KEY=your-anon-key
SUPABASE_SERVICE_ROLE_KEY=your-service-key

# Email Provider (choisir un)
EMAIL_PROVIDER=sendgrid  # ou mailgun, ses

# SendGrid
SENDGRID_API_KEY=SG.xxxxx

# Mailgun (alternative)
MAILGUN_API_KEY=key-xxxxx
MAILGUN_DOMAIN=mg.yourdomain.com

# Configuration d'envoi
EMAIL_BATCH_SIZE=100
EMAIL_RATE_LIMIT_PER_SECOND=10
EMAIL_MAX_RETRY_ATTEMPTS=3

# URLs
APP_BASE_URL=http://localhost:3000
API_BASE_URL=http://localhost:8000
```

### 3. Configuration Frontend

```bash
cd frontend

# Installer les dépendances
npm install

# Créer le fichier .env
cp .env.example .env
```

**Configuration `.env`:**

```env
VITE_API_URL=http://localhost:8000
VITE_SUPABASE_URL=https://xxxxx.supabase.co
VITE_SUPABASE_ANON_KEY=your-anon-key
```

### 4. Base de données

```bash
# Appliquer la migration SQL
psql -U postgres -d your_database -f supabase/migrations/20241215000001_create_email_campaign_schema.sql

# Ou via Supabase Dashboard:
# 1. Ouvrir SQL Editor
# 2. Copier/coller le contenu de la migration
# 3. Exécuter
```

## 🚀 Démarrage

### Backend

```bash
cd backend
source venv/bin/activate
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

API disponible sur : http://localhost:8000

Documentation interactive : http://localhost:8000/docs

### Frontend

```bash
cd frontend
npm run dev
```

Application disponible sur : http://localhost:3000

## 📚 Utilisation

### 1. Créer une Campagne

1. Cliquer sur **"Nouvelle campagne"**
2. Remplir les informations :
   - Nom de la campagne
   - Sujet de l'email
   - Informations expéditeur
   - Contenu HTML avec variables
3. Enregistrer comme brouillon

### 2. Importer des Destinataires

1. Ouvrir la campagne créée
2. Cliquer sur **"Importer CSV"**
3. Sélectionner votre fichier CSV
4. Vérifier l'aperçu et le mapping des colonnes
5. Confirmer l'importation

**Format CSV attendu:**

```csv
email,first_name,last_name,company
jean.dupont@example.com,Jean,Dupont,Acme Corp
marie.martin@example.com,Marie,Martin,Tech Inc
```

### 3. Variables dans le Template

Utilisez les variables suivantes dans votre HTML :

- `{{firstname}}` - Prénom du destinataire
- `{{lastname}}` - Nom du destinataire
- `{{company}}` - Nom de la société
- `{{subject}}` - Sujet de l'email
- `{{unsubscribe_url}}` - **Obligatoire** - Lien de désinscription

**Exemple de template:**

```html
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>{{subject}}</title>
</head>
<body>
    <h1>Bonjour {{firstname}} {{lastname}},</h1>
    
    <p>Nous sommes ravis de vous contacter...</p>
    
    <footer>
        <p>
            <a href="{{unsubscribe_url}}">Se désinscrire</a>
        </p>
    </footer>
</body>
</html>
```

### 4. Envoyer un Test

Avant de lancer la campagne complète :

1. Dans les détails de la campagne
2. Saisir votre email dans "Envoyer un test"
3. Vérifier la réception et le rendu

### 5. Lancer la Campagne

1. Vérifier que tous les destinataires sont importés
2. Cliquer sur **"Lancer la campagne"**
3. Suivre la progression en temps réel
4. Consulter les statistiques après l'envoi

## 🔐 Conformité et Désinscription

### Lien de Désinscription

**Chaque email DOIT contenir** un lien de désinscription visible :

```html
<footer style="text-align: center; padding: 20px; color: #666;">
    <p>Vous recevez cet email car vous êtes inscrit à notre liste.</p>
    <p>
        <a href="{{unsubscribe_url}}" style="color: #4F46E5;">
            Se désinscrire
        </a>
    </p>
</footer>
```

### Headers Techniques

L'application ajoute automatiquement les headers suivants :

```
List-Unsubscribe: <https://app.com/unsubscribe?email=...>, <mailto:contact@example.com?subject=unsubscribe>
List-Unsubscribe-Post: List-Unsubscribe=One-Click
```

Ces headers activent le bouton "Se désinscrire" natif dans Gmail, Outlook, etc.

### Page de Désinscription

URL publique : `/unsubscribe?email={email}&campaign_id={id}`

Accessible sans authentification, processus en un clic.

## 📊 API Endpoints

### Campagnes

```
POST   /v1/campaigns              # Créer une campagne
GET    /v1/campaigns              # Lister les campagnes
GET    /v1/campaigns/{id}         # Détails d'une campagne
PATCH  /v1/campaigns/{id}         # Modifier une campagne
DELETE /v1/campaigns/{id}         # Supprimer une campagne
GET    /v1/campaigns/{id}/stats   # Statistiques
GET    /v1/campaigns/{id}/progress # Progression en temps réel
POST   /v1/campaigns/{id}/send    # Lancer l'envoi
POST   /v1/campaigns/{id}/pause   # Mettre en pause
```

### Import CSV

```
POST   /v1/campaigns/{id}/import-csv/preview  # Prévisualiser CSV
POST   /v1/campaigns/{id}/import-csv          # Importer CSV
```

### Destinataires

```
GET    /v1/campaigns/{id}/recipients   # Liste des destinataires
POST   /v1/campaigns/{id}/recipients   # Ajouter un destinataire
GET    /v1/recipients/{id}             # Détails destinataire
PATCH  /v1/recipients/{id}             # Modifier destinataire
DELETE /v1/recipients/{id}             # Supprimer destinataire
```

### Templates

```
POST   /v1/templates           # Créer un template
GET    /v1/templates           # Lister les templates
GET    /v1/templates/{id}      # Détails template
PATCH  /v1/templates/{id}      # Modifier template
DELETE /v1/templates/{id}      # Supprimer template
POST   /v1/templates/render    # Prévisualiser rendu
```

### Désinscription (Public)

```
POST   /v1/unsubscribe                  # Se désinscrire
GET    /v1/unsubscribe/check/{email}    # Vérifier statut
```

## 🔒 Sécurité

### Row Level Security (RLS)

Les politiques RLS Supabase protègent les données :

- Les campagnes sont accessibles uniquement aux utilisateurs authentifiés
- La désinscription est publique (lecture/écriture)
- Les logs sont en lecture seule pour les utilisateurs

### Validation

- Validation Pydantic côté backend
- Validation des emails (RFC 5322)
- Protection contre les injections SQL
- Rate limiting sur les API

### Bonnes Pratiques

- Ne jamais exposer les clés API en frontend
- Utiliser HTTPS en production
- Activer CORS uniquement pour domaines autorisés
- Logger tous les événements sensibles

## 🧪 Tests

```bash
# Backend
cd backend
pytest

# Frontend
cd frontend
npm run test
```

## 🚢 Déploiement

### Backend (exemple avec Docker)

```bash
cd backend
docker build -t email-campaign-api .
docker run -p 8000:8000 --env-file .env email-campaign-api
```

### Frontend (exemple avec Vercel)

```bash
cd frontend
npm run build
# Déployer le dossier dist/
```

### Variables d'environnement Production

Assurez-vous de configurer :

- URLs de production (APP_BASE_URL, API_BASE_URL)
- Clés API réelles (SendGrid/Mailgun)
- CORS avec domaines de production uniquement
- HTTPS activé

## 📈 Monitoring

### Métriques à surveiller

- Taux de délivrabilité (> 95%)
- Taux d'ouverture (15-25% selon l'industrie)
- Taux de clic (2-5%)
- Taux de désinscription (< 0.5%)
- Taux de bounce (< 2%)
- Temps de traitement des campagnes

### Logs

Les logs d'événements sont stockés dans la table `email_logs` :

- sent
- delivered
- opened
- clicked
- bounced (hard/soft)
- failed
- unsubscribed
- spam_report

## 🤝 Contribution

Les contributions sont bienvenues !

1. Fork le projet
2. Créer une branche feature (`git checkout -b feature/AmazingFeature`)
3. Commit (`git commit -m 'Add AmazingFeature'`)
4. Push (`git push origin feature/AmazingFeature`)
5. Ouvrir une Pull Request

## 📝 Licence

MIT License - voir le fichier LICENSE

## 🆘 Support

Pour toute question ou problème :

- Ouvrir une issue sur GitHub
- Consulter la documentation API : `/docs`
- Email : support@example.com

## 🎯 Roadmap

- [ ] A/B Testing de campagnes
- [ ] Segmentation avancée des destinataires
- [ ] Éditeur WYSIWYG pour templates
- [ ] Webhooks pour événements temps réel
- [ ] Intégration CRM (Salesforce, HubSpot)
- [ ] Analytics avancées avec graphiques
- [ ] Planification automatique (récurrence)
- [ ] Multi-tenancy pour SaaS

---

**Fait avec ❤️ pour respecter la vie privée et les bonnes pratiques d'emailing**
