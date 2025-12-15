# 🚀 Guide de Démarrage Rapide

## Installation en 5 minutes

### 1. Prérequis

Vérifiez que vous avez installé :

```bash
python --version  # Python 3.11+
node --version    # Node.js 18+
```

### 2. Configuration Supabase

1. Créer un compte sur [supabase.com](https://supabase.com)
2. Créer un nouveau projet
3. Aller dans `SQL Editor`
4. Copier/coller le contenu de `supabase/migrations/20241215000001_create_email_campaign_schema.sql`
5. Exécuter la migration
6. Récupérer vos clés dans `Settings > API`

### 3. Configuration SendGrid

1. Créer un compte sur [sendgrid.com](https://sendgrid.com)
2. Créer une API Key : `Settings > API Keys > Create API Key`
3. Donner les permissions `Mail Send`
4. Copier la clé (elle ne sera visible qu'une fois)

### 4. Installation Backend

```bash
cd backend

# Créer environnement virtuel
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Installer dépendances
pip install -r requirements.txt

# Configurer .env
cp .env.example .env
# Éditer .env avec vos clés
```

**Éditer `backend/.env` :**

```env
SUPABASE_URL=https://xxxxx.supabase.co
SUPABASE_SERVICE_ROLE_KEY=eyJxxxx...
SENDGRID_API_KEY=SG.xxxx...
APP_BASE_URL=http://localhost:3000
```

### 5. Installation Frontend

```bash
cd frontend

# Installer dépendances
npm install

# Configurer .env
cp .env.example .env
# Éditer .env avec vos clés
```

**Éditer `frontend/.env` :**

```env
VITE_API_URL=http://localhost:8000
VITE_SUPABASE_URL=https://xxxxx.supabase.co
VITE_SUPABASE_ANON_KEY=eyJxxxx...
```

### 6. Lancer l'application

**Terminal 1 - Backend :**

```bash
cd backend
source venv/bin/activate
uvicorn main:app --reload
```

✅ Backend prêt : http://localhost:8000

**Terminal 2 - Frontend :**

```bash
cd frontend
npm run dev
```

✅ Frontend prêt : http://localhost:3000

### 7. Tester l'application

1. Ouvrir http://localhost:3000
2. Cliquer sur "Nouvelle campagne"
3. Remplir le formulaire
4. Créer un fichier CSV de test :

```csv
email,first_name,last_name,company
test@example.com,John,Doe,Acme Corp
```

5. Importer le CSV
6. Envoyer un email de test à votre adresse
7. Lancer la campagne !

## ✅ Vérification

### Backend fonctionne ?

```bash
curl http://localhost:8000/health
# Doit retourner: {"status": "healthy"}
```

### Base de données OK ?

```bash
curl http://localhost:8000/v1/campaigns
# Doit retourner: []
```

### Frontend connecté ?

Ouvrir http://localhost:3000 et vérifier qu'il n'y a pas d'erreurs dans la console.

## 🐛 Problèmes fréquents

### Erreur CORS

**Symptôme :** Erreur CORS dans la console du navigateur

**Solution :** Vérifier que `ALLOWED_ORIGINS` dans `backend/.env` contient `http://localhost:3000`

### Erreur Supabase

**Symptôme :** "Failed to connect to Supabase"

**Solution :** 
1. Vérifier que les URLs et clés sont correctes
2. Vérifier que la migration SQL a été exécutée
3. Vérifier que RLS est bien configuré

### Emails ne s'envoient pas

**Symptôme :** Campagne reste en "sending" indéfiniment

**Solution :**
1. Vérifier la clé API SendGrid dans `.env`
2. Vérifier les logs backend : erreurs d'authentification ?
3. Vérifier que l'adresse expéditeur est vérifiée dans SendGrid

### Import CSV échoue

**Symptôme :** "Failed to import CSV"

**Solution :**
1. Vérifier que le CSV est encodé en UTF-8
2. Vérifier que la colonne `email` existe
3. Vérifier les logs pour voir les lignes en erreur

## 📚 Prochaines étapes

1. Lire le [CAMPAIGN_README.md](./CAMPAIGN_README.md) complet
2. Consulter la documentation API : http://localhost:8000/docs
3. Créer vos propres templates email
4. Configurer votre domaine d'envoi
5. Tester en production !

## 🆘 Besoin d'aide ?

- Consulter la [documentation complète](./CAMPAIGN_README.md)
- Vérifier les [issues GitHub](https://github.com/...)
- Consulter les logs : `backend/logs/` et console navigateur

---

**Temps estimé d'installation : 5-10 minutes** ⏱️
