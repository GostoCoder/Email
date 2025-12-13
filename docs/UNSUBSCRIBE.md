# Fonctionnalité de Désinscription (Unsubscribe)

## 📋 Vue d'ensemble

Cette fonctionnalité permet aux destinataires d'emails de se désinscrire de la liste de diffusion de manière sécurisée et conforme au RGPD.

## 🔧 Architecture

```
app/features/suppression/
├── model/
│   └── suppression_model.py    # Modèles: Unsubscribe, UnsubscribeLog, UnsubscribeRequest, UnsubscribeResult
├── service/
│   └── suppression_service.py  # Logique métier complète
├── view/
│   └── suppression_routes.py   # Routes API et pages HTML
└── viewmodel/
    └── suppression_viewmodel.py # Interface entre routes et service
```

## 🚦 Flux de désinscription

```
1. EMAIL ENVOYÉ
   └── Contient un lien: /api/suppression/page/{token}
        └── Token JWT contenant: email, contact_id, campaign_id, expiration

2. CLIC SUR LE LIEN
   └── Affiche une page de confirmation avec design moderne
        └── Champ optionnel pour la raison du désabonnement

3. CONFIRMATION
   └── POST /api/suppression/unsubscribe avec le token
        ├── Validation du token (signature + expiration)
        ├── Mise à jour de la table `contacts`:
        │   └── is_unsubscribed = true, is_active = false, unsubscribed_at = NOW()
        ├── Insertion dans `suppressions`:
        │   └── email, reason='unsubscribed'
        ├── Mise à jour de `campaign_contacts`:
        │   └── status = 'unsubscribed'
        ├── Incrémentation de `campaigns.unsubscribed_count`
        └── Log dans `unsubscribe_logs` (audit)

4. AFFICHAGE RÉSULTAT
   └── Page de succès ou d'erreur
```

## 🔐 Sécurité des Tokens

### Format du token enrichi
```
payload_base64.signature
```

### Contenu du payload
```json
{
  "email": "user@example.com",
  "contact_id": "uuid-1234",
  "campaign_id": "uuid-5678",
  "exp": 1735689600
}
```

### Caractéristiques
- **Signé HMAC-SHA256** avec `SECRET_KEY`
- **Expiration configurable** (défaut: 30 jours)
- **URL-safe Base64** encoding
- **Rétrocompatible** avec l'ancien format simple

## 📡 API Endpoints

### POST `/api/suppression/unsubscribe`
Désabonne un email via token.

**Request:**
```json
{
  "token": "eyJlbWFpbCI6InVzZXJAZXhh...",
  "reason": "Trop d'emails"
}
```

**Response (200):**
```json
{
  "success": true,
  "email": "user@example.com",
  "message": "Vous avez été désabonné·e avec succès."
}
```

### GET `/api/suppression/list`
Liste tous les emails désabonnés.

**Response:**
```json
{
  "success": true,
  "count": 42,
  "emails": ["user1@example.com", "user2@example.com"]
}
```

### GET `/api/suppression/logs`
Récupère les logs de désabonnements (audit).

**Query params:**
- `limit`: Nombre max (défaut: 100)
- `email`: Filtrer par email
- `campaign_id`: Filtrer par campagne

**Response:**
```json
{
  "success": true,
  "count": 5,
  "logs": [
    {
      "id": "uuid",
      "email": "user@example.com",
      "contact_id": "uuid",
      "campaign_id": "uuid",
      "source": "email",
      "ip_address": "192.168.1.1",
      "created_at": "2024-12-13T10:00:00Z"
    }
  ]
}
```

### POST `/api/suppression/add`
Ajoute manuellement un email (admin).

**Request:**
```json
{
  "email": "user@example.com",
  "reason": "Demande par téléphone"
}
```

### POST `/api/suppression/remove`
Retire un email de la liste de suppression.

**Request:**
```json
{
  "email": "user@example.com"
}
```

### GET `/api/suppression/check?email=user@example.com`
Vérifie si un email est désabonné.

### GET `/api/suppression/page/{token}`
Page HTML de confirmation de désabonnement.

### GET `/api/suppression/success`
Page de succès (accès direct).

### GET `/api/suppression/error`
Page d'erreur.

## 📊 Base de données

### Table `suppressions`
```sql
CREATE TABLE suppressions (
    id UUID PRIMARY KEY,
    email VARCHAR(255) NOT NULL UNIQUE,
    reason VARCHAR(100),  -- 'unsubscribed', 'bounced', 'complaint', 'manual'
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

### Table `unsubscribe_logs` (audit)
```sql
CREATE TABLE unsubscribe_logs (
    id UUID PRIMARY KEY,
    contact_id UUID REFERENCES contacts(id),
    campaign_id UUID REFERENCES campaigns(id),
    email VARCHAR(255) NOT NULL,
    source VARCHAR(50) NOT NULL,  -- 'email', 'manual', 'api', 'import'
    ip_address VARCHAR(45),
    user_agent TEXT,
    reason TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

## 🎨 Templates Email

Le template doit inclure la variable `{{unsubscribe_url}}` :

```html
<div class="footer">
    <p>
        Vous ne souhaitez plus recevoir nos emails ?<br>
        <a href="{{unsubscribe_url}}">Se désabonner</a>
    </p>
</div>
```

## 🛡️ Conformité RGPD

- ✅ Lien de désinscription dans chaque email
- ✅ Désinscription en 1 clic (confirmation optionnelle)
- ✅ Logs conservés pour preuve de consentement
- ✅ Pas de connexion requise
- ✅ Token sécurisé et signé
- ✅ Expiration des tokens configurable

## ⚙️ Configuration

Variables d'environnement :

```env
# Clé secrète pour signer les tokens (OBLIGATOIRE en production)
SECRET_KEY=your-super-secret-key-here

# URL de base pour les liens de désinscription
UNSUBSCRIBE_BASE_URL=https://votre-domaine.com
```

## 🧪 Tests

```bash
# Générer un token de test
curl -X POST http://localhost:5000/api/suppression/generate-token \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com"}'

# Tester le désabonnement
curl -X POST http://localhost:5000/api/suppression/unsubscribe \
  -H "Content-Type: application/json" \
  -d '{"token": "votre-token-ici"}'

# Vérifier la liste
curl http://localhost:5000/api/suppression/list
```

## 📝 Migration SQL

Exécuter la migration pour créer la table `unsubscribe_logs` :

```bash
# Avec Supabase CLI
supabase db push

# Ou manuellement
psql -f supabase/migrations/20241213000001_add_unsubscribe_logs.sql
```
