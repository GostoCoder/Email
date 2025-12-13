# 📧 Outil d'Emailing Professionnel - Architecture MVVM

Application professionnelle d'envoi d'emails en masse avec **architecture MVVM Feature-First**.

**🏗️ Architecture:** MVVM Feature-First | **🚀 Version:** 2.0.0 | **🐍 Python 3.x** | **⚛️ React + TypeScript**

---

## 🎯 Nouvelle Architecture MVVM

Ce projet a été restructuré avec une **architecture MVVM (Model-View-ViewModel)** professionnelle et une approche **"feature-first"**. Chaque fonctionnalité est complètement isolée avec sa propre structure MVVM.

📖 **Documentation complète:** [ARCHITECTURE_MVVM.md](./ARCHITECTURE_MVVM.md)

### 📂 Structure du projet

```
app/                              # 🎯 Backend MVVM
├── core/                         # Configuration & utils
├── shared/                       # Composants réutilisables
└── features/                     # Features MVVM
    ├── campaign/                 # Campagnes d'emailing
    ├── dashboard/                # Statistiques
    ├── templates/                # Gestion templates
    ├── suppression/              # Désabonnements
    └── configuration/            # Config SMTP

frontend/                         # ⚛️ Frontend React
templates/                        # 📄 Templates emails
data/                            # 💾 Données
```

---

## 🚀 Démarrage rapide

### Option 1 : 🐳 Avec Docker (Recommandé)

```bash
# Cloner le projet
git clone <votre-repo>
cd Outil-Emailing

# Configurer les variables d'environnement
cp .env.example .env
# Modifier .env avec vos paramètres SMTP

# Lancer l'application
docker-compose up -d

# Voir les logs
docker-compose logs -f
```

📘 **[Documentation Docker complète](./DOCKER.md)**

L'application sera accessible sur **http://localhost:5000**

### Option 2 : Installation locale

```bash
# Cloner le projet
git clone <votre-repo>
cd Outil-Emailing

# Créer l'environnement virtuel
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# ou venv\Scripts\activate  # Windows

# Installer les dépendances
pip install -r app/requirements.txt
```

### 2️⃣ Configuration

Créer un fichier `.env` à la racine :

```env
# Configuration SMTP
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=votre.email@gmail.com
SMTP_PASSWORD=votre_mot_de_passe
SMTP_USE_TLS=true

# Expéditeur
SENDER_NAME=Votre Nom
SENDER_EMAIL=votre.email@gmail.com

# Sécurité
SECRET_KEY=votre_cle_secrete_ici
```

### 3️⃣ Lancer l'application

```bash
# Méthode 1 : Script automatique
./start_mvvm.sh

# Méthode 2 : Directement
python app/main.py
```

L'API sera accessible sur **http://localhost:5000**

---

## 🎨 Frontend React

```bash
cd frontend
npm install
npm run dev
```

Le frontend sera accessible sur **http://localhost:5173**

---

## 📡 API REST (Endpoints)

### Campaign (Campagnes)
- `POST /api/campaign/create` - Créer une campagne
- `POST /api/campaign/start` - Démarrer l'envoi
- `GET /api/campaign/status` - Statut de la campagne
- `POST /api/campaign/upload-csv` - Upload CSV

### Dashboard (Statistiques)
- `GET /api/dashboard/stats` - Statistiques globales

### Templates (Gestion des templates)
- `GET /api/templates/list` - Lister les templates
- `GET /api/templates/<name>` - Récupérer un template
- `POST /api/templates/save` - Sauvegarder un template

### Suppression (Désabonnements)
- `POST /api/suppression/unsubscribe` - Désabonner un email
- `GET /api/suppression/list` - Liste des désabonnés
- `POST /api/suppression/remove` - Retirer un désabonné
- `GET /api/suppression/page/<token>` - Page de désabonnement

### Configuration (Paramètres SMTP)
- `GET /api/configuration/get` - Récupérer la configuration
- `POST /api/configuration/update` - Mettre à jour
- `POST /api/configuration/test-smtp` - Tester la connexion SMTP

---

## ✨ Fonctionnalités

### Backend
- ✅ **Architecture MVVM** - Séparation claire des responsabilités
- ✅ **Feature-First** - Features isolées et maintenables
- ✅ **API REST Flask** - Endpoints organisés par feature
- ✅ **Validation d'emails** - Service de validation robuste
- ✅ **Gestion des tokens** - Tokens sécurisés pour désabonnements
- ✅ **Service CSV** - Lecture/écriture de fichiers CSV
- ✅ **Logging centralisé** - Système de logs structuré
- ✅ **Configuration flexible** - Gestion via .env

### Frontend
- ✅ **React + TypeScript** - Interface moderne et typée
- ✅ **Vite** - Build rapide et HMR
- ✅ **React Router** - Navigation SPA
- ✅ **Lucide Icons** - Icônes modernes
- ✅ **Design responsive** - Interface adaptative

### Emailing
- ✅ **Envoi SMTP sécurisé** - TLS/SSL
- ✅ **Templates HTML/Texte** - Support multipart
- ✅ **Gestion des désabonnements** - Conforme RGPD
- ✅ **Statistiques en temps réel** - Suivi des campagnes
- ✅ **Upload CSV** - Import de contacts

---

## 🧠 Architecture MVVM

Chaque feature suit le pattern MVVM :

```
feature/
├── model/              # 📊 Données & entités
├── view/               # 🌐 Routes Flask (API)
├── viewmodel/          # 🎨 Logique de présentation
└── service/            # 🔧 Logique métier
```

### Flux de données

```
Frontend → View → ViewModel → Service → Model → Ressources
```

### Avantages

✅ **Séparation des responsabilités** - Chaque couche a un rôle clair  
✅ **Testabilité** - Tests unitaires faciles  
✅ **Scalabilité** - Ajout de features sans impact  
✅ **Maintenabilité** - Code organisé et lisible  
✅ **Réutilisabilité** - Services partagés  
✅ **Travail en équipe** - Features isolées  

---

## 📚 Documentation

- [📖 Architecture MVVM](./ARCHITECTURE_MVVM.md) - Documentation complète de l'architecture
- [🚀 Quick Start](./QUICKSTART.md) - Guide de démarrage rapide
- [📝 Commandes](./COMMANDES.md) - Liste des commandes disponibles

---

## 🛠️ Technologies

### Backend
- **Python 3.x**
- **Flask** - Framework web
- **Flask-CORS** - Gestion CORS
- **python-dotenv** - Variables d'environnement
- **smtplib** - Envoi d'emails

### Frontend
- **React 18**
- **TypeScript**
- **Vite**
- **React Router**
- **Lucide Icons**

### DevOps
- **Docker** - Conteneurisation
- **Docker Compose** - Orchestration
- **Multi-stage builds** - Optimisation des images

---

## 📦 Structure des dossiers

```
Outil-Emailing/
├── app/                          # Backend MVVM
│   ├── core/                     # Configuration & utils
│   ├── shared/                   # Composants partagés
│   ├── features/                 # Features MVVM
│   ├── main.py                   # Point d'entrée
│   └── requirements.txt          # Dépendances Python
│
├── frontend/                     # Frontend React
│   ├── src/
│   │   ├── pages/               # Composants de pages
│   │   ├── services/            # Services API
│   │   └── types/               # Types TypeScript
│   └── package.json
│
├── templates/                    # Templates d'emails
├── data/                        # Données (CSV, logs)
├── .env                         # Configuration (à créer)
└── start_mvvm.sh                # Script de démarrage
```

---

## 🧪 Tests

```bash
# Tests backend (à venir)
pytest

# Tests frontend
cd frontend
npm test
```

---

## 📝 Exemple d'utilisation

### 1. Créer une campagne

```bash
curl -X POST http://localhost:5000/api/campaign/create \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Newsletter Janvier",
    "subject": "Découvrez nos nouveautés",
    "template_name": "newsletter",
    "csv_file_path": "data/uploads/contacts.csv"
  }'
```

### 2. Démarrer l'envoi

```bash
curl -X POST http://localhost:5000/api/campaign/start
```

### 3. Vérifier le statut

```bash
curl http://localhost:5000/api/campaign/status
```

---

## 🔒 Sécurité

- ✅ Variables sensibles dans `.env`
- ✅ Tokens sécurisés avec HMAC-SHA256
- ✅ Validation stricte des emails
- ✅ Respect du RGPD (désabonnements)
- ✅ Connexions SMTP sécurisées (TLS)

---

## 🤝 Contribution

Les contributions sont les bienvenues ! Suivez l'architecture MVVM existante.

1. Fork le projet
2. Créer une branche (`git checkout -b feature/nouvelle-feature`)
3. Commit (`git commit -m 'Ajout nouvelle feature'`)
4. Push (`git push origin feature/nouvelle-feature`)
5. Ouvrir une Pull Request

---

## 📄 Licence

Ce projet est sous licence MIT.

---

## 👨‍💻 Auteur

**Almadia Solutions**

---

## 🆘 Support

Pour toute question ou problème :
- Ouvrir une issue sur GitHub
- Consulter la [documentation](./ARCHITECTURE_MVVM.md)

---

**🎉 Bon emailing !**
