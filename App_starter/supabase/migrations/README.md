# Supabase – Migrations (Starter)

Guide succinct pour appliquer les migrations Supabase de la base App_starter. Adaptez les fichiers SQL à vos besoins applicatifs.

## Prérequis
- Projet Supabase créé et accessible (URL + clés)
- Supabase CLI installée (`npm i -g supabase`) ou accès au SQL Editor
- Variables d’environnement renseignées dans `.env` (SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY, SUPABASE_ANON_KEY)

## Structure des fichiers
```
supabase/
  migrations/
    YYYYMMDDHHMMSS_initial_schema.sql
    YYYYMMDDHHMMSS_auth_trigger.sql
    YYYYMMDDHHMMSS_performance.sql (optionnel)
```
Convention : `YYYYMMDDHHMMSS_description.sql` (ordre chronologique obligatoire).

## Application des migrations

### Option A — Supabase CLI (recommandé en CI)
```bash
supabase db reset
```

### Option B — SQL Editor (manuel)
1) Ouvrir Supabase Dashboard > SQL Editor
2) Exécuter les fichiers dans l’ordre (copier-coller le contenu ou utiliser `\i` si disponible)

## Vérifications rapides
```sql
-- Tables attendues (exemple): users, apps, access
SELECT tablename FROM pg_tables WHERE schemaname = 'public';

-- Index minimum sur FK et colonnes de recherche
SELECT COUNT(*) FROM pg_indexes WHERE schemaname = 'public';

-- Triggers (ex: sync_user_profile)
SELECT tgname FROM pg_trigger WHERE tgname LIKE 'on_auth_user_%';
```

## Sécurité / RLS
- Activez les politiques RLS sur les tables contenant des données utilisateur.
- Ne jamais exposer la service role key côté frontend.
- Conservez les migrations idempotentes (`IF NOT EXISTS`) quand c’est pertinent.

## Bonnes pratiques
- Pinner les versions d’extensions (pg_trgm, pg_cron) si utilisées.
- Toujours inclure `created_at` / `updated_at`, clés UUID et index sur FK.
- Tester localement (Supabase CLI) avant de pousser en prod.

## Rollback
Prévoir un fichier de rollback par migration critique (`YYYY..._rollback.sql`). À n’utiliser qu’en urgence et à tester en pré-prod.

## Notes
- Ce README est générique : ajustez les noms de tables, politiques RLS et index selon votre domaine.
- Les migrations présentes servent d’exemple; remplacez-les par celles de votre application.
