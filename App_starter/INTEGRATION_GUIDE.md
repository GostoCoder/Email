# 🔗 Guide d'Intégration dans l'Application Existante

## Option 1 : Application Standalone (Recommandé)

L'application de campagnes d'emailing peut fonctionner **indépendamment** de l'App_starter existante.

### Démarrage Séparé

```bash
# Terminal 1 - Backend campagnes
cd backend
source venv/bin/activate
uvicorn main:app --reload --port 8000

# Terminal 2 - Frontend campagnes
cd frontend
npm run dev -- --port 3001
```

Accès : http://localhost:3001

---

## Option 2 : Intégration dans App.tsx Principal

Si vous souhaitez intégrer les campagnes dans votre application existante :

### 1. Installer les Dépendances Frontend

Les dépendances sont déjà dans `package.json`, mais assurez-vous d'avoir :

```json
{
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "react-router-dom": "^6.x"  // Si pas déjà installé
  }
}
```

### 2. Configurer le Routing

**Option A : Sans React Router (Simple)**

Modifiez `frontend/src/App.tsx` :

```tsx
import { useState } from 'react';
import { CampaignManager, UnsubscribePage } from './components/campaigns';
import './styles/campaigns.css';

function App() {
  const [currentPage, setCurrentPage] = useState<'home' | 'campaigns' | 'unsubscribe'>('home');

  if (currentPage === 'campaigns') {
    return (
      <div>
        <button onClick={() => setCurrentPage('home')}>← Retour</button>
        <CampaignManager />
      </div>
    );
  }

  if (currentPage === 'unsubscribe') {
    return <UnsubscribePage />;
  }

  return (
    <div className="page">
      <header className="header">
        <h1>Hub-Almadia</h1>
        <button onClick={() => setCurrentPage('campaigns')} className="btn-primary">
          📧 Gestion Campagnes Email
        </button>
      </header>
      {/* Votre contenu existant */}
    </div>
  );
}

export default App;
```

**Option B : Avec React Router (Avancé)**

```bash
npm install react-router-dom
```

Modifiez `frontend/src/main.tsx` :

```tsx
import React from 'react';
import ReactDOM from 'react-dom/client';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import App from './App';
import { CampaignManager, UnsubscribePage } from './components/campaigns';
import './styles/index.css';
import './styles/campaigns.css';

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<App />} />
        <Route path="/campaigns/*" element={<CampaignManager />} />
        <Route path="/unsubscribe" element={<UnsubscribePage />} />
      </Routes>
    </BrowserRouter>
  </React.StrictMode>
);
```

### 3. Importer les Styles

Ajoutez dans `frontend/src/main.tsx` ou `App.tsx` :

```tsx
import './styles/campaigns.css';
```

### 4. Menu de Navigation

Créez un composant `Navigation.tsx` :

```tsx
import { Link } from 'react-router-dom';

export function Navigation() {
  return (
    <nav className="main-nav">
      <Link to="/">🏠 Accueil</Link>
      <Link to="/campaigns">📧 Campagnes Email</Link>
    </nav>
  );
}
```

---

## Option 3 : Application Séparée avec Reverse Proxy

Architecture microservices avec Traefik/Nginx.

### Nginx Configuration

```nginx
server {
    listen 80;
    server_name yourdomain.com;

    # Application principale
    location / {
        proxy_pass http://localhost:3000;
    }

    # Application campagnes
    location /campaigns/ {
        proxy_pass http://localhost:3001/;
    }

    # API Backend
    location /api/ {
        proxy_pass http://localhost:8000/;
    }
}
```

### Docker Compose Multi-App

```yaml
version: '3.9'

services:
  # App principale
  main-frontend:
    build: ./App_starter/frontend
    ports:
      - "3000:80"

  # App campagnes
  campaigns-frontend:
    build: ./App_starter/frontend
    ports:
      - "3001:80"
    environment:
      - VITE_API_URL=http://localhost:8000

  # Backend unique
  backend:
    build: ./App_starter/backend
    ports:
      - "8000:8000"
```

---

## Gestion des Permissions

### Option A : Sans Authentification (Simple)

L'application fonctionne sans auth, idéal pour :
- Usage interne
- Environnement protégé
- MVP/Prototype

### Option B : Avec Supabase Auth (Recommandé)

**1. Activer l'authentification dans le backend**

`backend/core/dependencies.py` :

```python
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from core.config import get_settings

security = HTTPBearer()
settings = get_settings()

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Verify JWT token from Supabase"""
    try:
        token = credentials.credentials
        payload = jwt.decode(
            token,
            settings.jwt_secret,
            algorithms=["HS256"],
            options={"verify_aud": False}
        )
        user_id = payload.get("sub")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials"
            )
        return user_id
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials"
        )
```

**2. Protéger les routes**

```python
from core.dependencies import get_current_user

@router.post("/campaigns", response_model=CampaignResponse)
async def create_campaign(
    campaign: CampaignCreate,
    current_user: str = Depends(get_current_user)
):
    # Ajouter created_by
    campaign_data = campaign.model_dump()
    campaign_data["created_by"] = current_user
    # ... reste du code
```

**3. Frontend avec Auth**

```tsx
import { supabase } from './lib/supabase';

function CampaignManagerAuth() {
  const [session, setSession] = useState(null);

  useEffect(() => {
    supabase.auth.getSession().then(({ data: { session } }) => {
      setSession(session);
    });
  }, []);

  if (!session) {
    return <LoginPage />;
  }

  return <CampaignManager />;
}
```

---

## Variables d'Environnement

### Backend `.env`

```env
# Ajoutez à votre .env existant
EMAIL_PROVIDER=sendgrid
SENDGRID_API_KEY=SG.xxx
EMAIL_BATCH_SIZE=100
EMAIL_RATE_LIMIT_PER_SECOND=10
APP_BASE_URL=http://localhost:3000
```

### Frontend `.env`

Aucune modification nécessaire si vous utilisez les mêmes variables.

---

## Tests de l'Intégration

### 1. Vérifier que le Backend Répond

```bash
curl http://localhost:8000/v1/campaigns
# Doit retourner : []
```

### 2. Vérifier l'Accès Frontend

Ouvrir http://localhost:3000/campaigns

### 3. Tester un Flow Complet

1. Créer une campagne
2. Importer un CSV
3. Envoyer un test
4. Vérifier les logs

---

## Migration des Données

Si vous avez déjà des données d'emails :

### Script de Migration

```python
# scripts/migrate_contacts.py
import csv
from supabase import create_client

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def migrate_contacts(csv_file, campaign_id):
    with open(csv_file) as f:
        reader = csv.DictReader(f)
        recipients = []
        for row in reader:
            recipients.append({
                "campaign_id": campaign_id,
                "email": row["email"],
                "first_name": row.get("first_name"),
                "last_name": row.get("last_name"),
                "company": row.get("company"),
                "status": "pending"
            })
        
        # Insert en batch de 100
        for i in range(0, len(recipients), 100):
            batch = recipients[i:i+100]
            supabase.table("recipients").insert(batch).execute()

# Usage
migrate_contacts("old_contacts.csv", "campaign-uuid-here")
```

---

## Troubleshooting

### Problème : CORS Errors

**Solution :** Ajouter dans `backend/.env` :

```env
ALLOWED_ORIGINS=["http://localhost:3000", "http://localhost:3001"]
```

### Problème : Routes Conflicts

Si vous avez déjà une route `/campaigns` :

**Solution :** Changer le prefix dans `main.py` :

```python
app.include_router(campaigns_router, prefix="/v1/email-campaigns", tags=["campaigns"])
```

### Problème : Styles qui se Chevauchent

**Solution :** Préfixer tous les styles dans `campaigns.css` :

```css
/* Avant */
.campaign-manager { ... }

/* Après */
.email-campaign-manager { ... }
```

---

## Checklist d'Intégration

- [ ] Migration SQL exécutée
- [ ] Variables d'environnement configurées
- [ ] Backend démarre sans erreur
- [ ] Frontend compile sans erreur
- [ ] API accessible depuis le frontend
- [ ] Import CSS OK
- [ ] Routes configurées
- [ ] Tests manuels passent
- [ ] Désinscription publique accessible
- [ ] Email de test reçu

---

## Support

Pour toute question sur l'intégration :

1. Consulter les logs backend : `backend/logs/`
2. Vérifier la console navigateur (F12)
3. Tester les endpoints API directement : http://localhost:8000/docs
4. Vérifier les données Supabase : Dashboard > Table Editor

---

**🚀 L'intégration devrait prendre 15-30 minutes maximum !**
