# =============================================================================
# Dockerfile pour Outil-Emailing (Architecture MVVM Feature-First)
# =============================================================================

# -----------------------------------------------------------------------------
# Stage 1: Build du frontend React/Vite
# -----------------------------------------------------------------------------
FROM node:18-alpine AS frontend-builder

WORKDIR /app

# Copier les fichiers de configuration Node.js
COPY package*.json ./
COPY tsconfig*.json ./
COPY vite.config.ts ./

# Installer les dépendances Node.js
RUN npm ci --only=production=false

# Copier la structure MVVM du frontend
# - Core: composants partagés, styles, routing
# - Features: chaque feature avec son propre view/viewmodel
COPY app/core/frontend ./app/core/frontend
COPY app/core/shared/styles ./app/core/shared/styles
COPY app/core/shared/components ./app/core/shared/components
COPY app/features ./app/features

# Build le frontend pour la production
RUN npm run build

# -----------------------------------------------------------------------------
# Stage 2: Image de production Python/Flask
# -----------------------------------------------------------------------------
FROM python:3.11-slim AS production

WORKDIR /app

# Métadonnées de l'image
LABEL maintainer="Almadia Solutions"
LABEL description="Outil Emailing - Architecture MVVM Feature-First"
LABEL version="1.0.0"

# Installer les dépendances système nécessaires
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Copier et installer les dépendances Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt \
    && pip install --no-cache-dir gunicorn

# Copier la structure MVVM complète du backend
# ├── app/
# │   ├── core/           (Configuration, Routing, Utils partagés)
# │   │   ├── config/
# │   │   ├── routing/
# │   │   ├── shared/
# │   │   └── utils/
# │   └── features/       (Features MVVM: Model, View, ViewModel, Service)
# │       ├── campaign/
# │       ├── configuration/
# │       ├── dashboard/
# │       ├── suppression/
# │       └── templates/
COPY app ./app

# Copier les ressources statiques
COPY templates ./templates
COPY examples ./examples

# Copier les assets du frontend buildé depuis le stage précédent
COPY --from=frontend-builder /app/dist ./app/core/frontend/dist

# Créer les répertoires nécessaires pour les données
RUN mkdir -p /app/data/uploads /app/data/logs

# Créer un utilisateur non-root pour la sécurité
RUN useradd -m -u 1000 appuser \
    && chown -R appuser:appuser /app
USER appuser

# Exposer le port de l'application
EXPOSE 5000

# Variables d'environnement par défaut
ENV FLASK_ENV=production \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    APP_PORT=5000

# Health check pour les orchestrateurs
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:5000/api/health || exit 1

# Commande de démarrage avec Gunicorn pour la production
# Configuration optimisée:
# - workers: 4 (2 × CPU cores recommandé)
# - threads: 2 (pour gérer les I/O)
# - timeout: 120s (pour les opérations d'envoi d'emails)
# - worker-class: sync (par défaut, stable pour Flask)
# - access-logfile: - (stdout pour Docker)
# - error-logfile: - (stderr pour Docker)
CMD ["gunicorn", \
     "--bind", "0.0.0.0:5000", \
     "--workers", "4", \
     "--threads", "2", \
     "--timeout", "120", \
     "--access-logfile", "-", \
     "--error-logfile", "-", \
     "--log-level", "info", \
     "app.main:app"]
