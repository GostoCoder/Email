# Supabase Configuration

Ce dossier contient la configuration Supabase pour l'application Outil-Emailing.

## 📁 Structure

```
supabase/
├── config.toml           # Configuration Supabase (ports, services, etc.)
├── seed.sql              # Données initiales pour le développement
├── migrations/           # Migrations SQL
│   └── 20241212000001_initial_schema.sql
└── .gitignore
```

## 🚀 Démarrage Rapide

### 1. Démarrer Supabase

```bash
supabase start
```

Cette commande démarre tous les services :
- PostgreSQL (port 54322)
- PostgREST API (port 54321)
- Supabase Studio (port 54323)
- Inbucket pour les emails (port 54324)

### 2. Accéder à Supabase Studio

Ouvrez votre navigateur : http://localhost:54323

### 3. Appliquer les migrations

Les migrations sont automatiquement appliquées au démarrage.

Pour les réappliquer manuellement :
```bash
supabase db reset
```

## 📊 Schéma de Base de Données

La migration initiale crée les tables suivantes :

- **campaigns** - Gestion des campagnes d'emailing
- **contacts** - Liste des contacts/destinataires
- **campaign_contacts** - Relation many-to-many entre campaigns et contacts
- **templates** - Templates HTML pour les emails
- **suppressions** - Liste de suppression (emails bloqués)
- **email_events** - Logs des événements emails (tracking)

## 🎯 Commandes Utiles

```bash
# Voir le statut
supabase status

# Arrêter
supabase stop

# Reset complet de la DB
supabase db reset

# Créer une nouvelle migration
supabase migration new nom_migration

# Accéder au shell PostgreSQL
supabase db shell
```

## 📚 Documentation Complète

Consultez [docs/SUPABASE_SETUP.md](../docs/SUPABASE_SETUP.md) pour la documentation complète.

## 🔗 URLs Locales

| Service | URL |
|---------|-----|
| Studio | http://localhost:54323 |
| API | http://localhost:54321 |
| DB | postgresql://postgres:postgres@localhost:54322/postgres |
| Email Testing | http://localhost:54324 |
