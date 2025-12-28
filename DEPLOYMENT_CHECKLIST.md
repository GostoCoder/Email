# ✅ Checklist de Déploiement - Email Campaign Platform

Cette checklist vous guide pour déployer l'application avec toutes les nouvelles fonctionnalités.

## 📋 Pré-Déploiement

### 1. Infrastructure

- [ ] Redis installé et accessible
- [ ] Supabase projet créé et accessible
- [ ] Domaine configuré avec DNS
- [ ] Certificat SSL/TLS obtenu (Let's Encrypt recommandé)
- [ ] Firewall configuré (ports 80, 443, optionnellement 8000, 6379)

### 2. Comptes Email Provider

Choisir UN provider et configurer:

**Option A: SendGrid**
- [ ] Compte SendGrid créé
- [ ] API Key générée (Full Access)
- [ ] Domaine vérifié
- [ ] Webhook configuré : `https://yourdomain.com/v1/webhooks/sendgrid`
- [ ] Clé de vérification webhook sauvegardée

**Option B: Mailgun**
- [ ] Compte Mailgun créé
- [ ] Domaine ajouté et DNS configuré
- [ ] API Key générée
- [ ] Webhook configuré : `https://yourdomain.com/v1/webhooks/mailgun`

**Option C: AWS SES**
- [ ] Compte AWS et SES activé
- [ ] Sortie du sandbox (si production)
- [ ] Domaine/email vérifié
- [ ] IAM user créé avec permissions SES
- [ ] SNS topic créé
- [ ] SNS souscription configurée : `https://yourdomain.com/v1/webhooks/ses`

### 3. Variables d'Environnement

- [ ] Fichier `.env` créé à partir de `.env.example`
- [ ] `SUPABASE_URL` configuré
- [ ] `SUPABASE_SERVICE_ROLE_KEY` configuré (⚠️ GARDEZ SECRET!)
- [ ] Email provider API keys configurés
- [ ] `SECRET_KEY` généré (`openssl rand -hex 32`)
- [ ] `REDIS_URL` configuré
- [ ] `ALLOWED_ORIGINS` mis à jour avec votre domaine

## 🗄️ Base de Données

### 4. Migrations Supabase

- [ ] Migration initiale appliquée : `20241215000001_create_email_campaign_schema.sql`
- [ ] Migration nouvelles tables appliquée : `20241216000001_add_abtesting_segmentation_tables.sql`
- [ ] Vérifier tables créées dans Supabase Dashboard
- [ ] Vérifier RLS policies actives
- [ ] Tester connexion depuis backend : `curl http://localhost:8000/health`

### 5. Indexes et Performance

- [ ] Tous les indexes créés (vérifier dans migration)
- [ ] Analyser query plans pour requêtes fréquentes
- [ ] Configurer auto-vacuum si nécessaire

## 🐳 Docker & Services

### 6. Build et Démarrage

- [ ] Docker et Docker Compose installés
- [ ] Images buildées : `docker-compose -f docker-compose.full.yml build`
- [ ] Services démarrés : `docker-compose -f docker-compose.full.yml up -d`
- [ ] Vérifier logs : `docker-compose logs -f backend`

### 7. Vérification des Services

- [ ] Backend API accessible : `curl http://localhost:8000/health`
- [ ] Redis accessible : `redis-cli ping`
- [ ] Celery worker en cours : `docker-compose logs celery_worker`
- [ ] Celery beat en cours : `docker-compose logs celery_beat`
- [ ] Frontend accessible : `http://localhost`
- [ ] Flower accessible (monitoring) : `http://localhost:5555`

## 🔒 Sécurité

### 8. Configuration Sécurité

- [ ] `DEBUG=false` en production
- [ ] Swagger désactivé en production (`SWAGGER_ENABLED=false`)
- [ ] Rate limiting activé (`RATE_LIMIT_ENABLED=true`)
- [ ] CORS configuré avec domaines spécifiques
- [ ] Secrets validés au démarrage (logs sans erreur)
- [ ] HTTPS forcé (HSTS activé dans nginx)
- [ ] Firewall configuré (bloquer ports Redis, Postgres si publics)

### 9. Headers de Sécurité

- [ ] CSP configuré dans nginx.conf
- [ ] HSTS activé (après vérification HTTPS)
- [ ] X-Frame-Options configuré
- [ ] Permissions-Policy configuré

## 🧪 Tests

### 10. Tests Fonctionnels

- [ ] Health check répond : `curl https://yourdomain.com/health`
- [ ] Créer une campagne via API
- [ ] Upload CSV de recipients
- [ ] Envoyer une campagne test
- [ ] Vérifier réception email
- [ ] Tester tracking (open, click)
- [ ] Tester unsubscribe

### 11. Tests Nouvelles Fonctionnalités

**A/B Testing:**
- [ ] Créer un test A/B
- [ ] Vérifier distribution de trafic
- [ ] Attendre échantillon minimum
- [ ] Vérifier sélection auto du gagnant

**Segmentation:**
- [ ] Créer un segment dynamique
- [ ] Créer des tags
- [ ] Assigner tags à recipients
- [ ] Vérifier filtrage

**Suppression List:**
- [ ] Ajouter email à suppression
- [ ] Vérifier qu'il ne reçoit pas de campagne
- [ ] Tester filtrage avant envoi

**Bounces:**
- [ ] Simuler un bounce (mode dev)
- [ ] Vérifier classification (hard/soft)
- [ ] Vérifier suppression automatique après seuils
- [ ] Tester webhooks providers

**Analytics:**
- [ ] Consulter stats par domaine
- [ ] Vérifier heatmap d'engagement
- [ ] Analyser bounces
- [ ] Comparer campagnes

## 📊 Monitoring

### 12. Observabilité

- [ ] Logs structurés JSON activés
- [ ] Prometheus configuré pour scraper `/metrics`
- [ ] Grafana dashboards créés
- [ ] Alertes configurées (bounce rate, error rate, etc.)
- [ ] Sentry configuré pour error tracking (optionnel)

### 13. Métriques à Surveiller

- [ ] `http_requests_total` - Volume de requêtes
- [ ] `http_request_duration_seconds` - Latence
- [ ] `http_requests_in_progress` - Charge actuelle
- [ ] Bounce rate < 5%
- [ ] Open rate suivi
- [ ] Click rate suivi
- [ ] Queue Celery (longueur, temps d'attente)

## 🚀 Post-Déploiement

### 14. Vérifications Finales

- [ ] DNS propagé et domaine accessible
- [ ] SSL certificate valide
- [ ] Tous les endpoints API testés
- [ ] Webhooks email provider testés
- [ ] Rate limiting fonctionne (tester avec burst)
- [ ] Cache Redis fonctionne
- [ ] Logs centralisés accessibles

### 15. Performance

- [ ] Temps de réponse API < 200ms (endpoints simples)
- [ ] Cache hit rate > 70%
- [ ] Throughput email (tester avec grande campagne)
- [ ] Load testing effectué (k6, Artillery, etc.)

### 16. Documentation

- [ ] Documentation API mise à jour
- [ ] Guide d'utilisation créé
- [ ] Runbook créé (incidents communs)
- [ ] Contact support configuré

## 🔄 Maintenance Continue

### 17. Sauvegarde

- [ ] Backup automatique Supabase configuré
- [ ] Backup Redis configuré (si données critiques)
- [ ] Plan de restauration testé

### 18. Mises à Jour

- [ ] Stratégie de déploiement définie (blue-green, rolling)
- [ ] CI/CD pipeline configuré
- [ ] Tests automatisés en CI
- [ ] Rollback plan défini

### 19. Scaling

- [ ] Auto-scaling configuré (si cloud)
- [ ] Limites de ressources définies
- [ ] Plan de scaling horizontal (Celery workers)
- [ ] CDN configuré pour frontend (optionnel)

## 📈 KPIs à Suivre

### 20. Métriques Business

- [ ] Dashboard KPIs créé
- [ ] Nombre de campagnes/jour
- [ ] Emails envoyés/jour
- [ ] Open rate moyen
- [ ] Click rate moyen
- [ ] Bounce rate
- [ ] Unsubscribe rate
- [ ] A/B tests gagnés
- [ ] Temps moyen de campagne

## 🆘 Troubleshooting

### Checklist de Debug

Si problème, vérifier dans l'ordre:

1. [ ] Health check : `curl https://yourdomain.com/health`
2. [ ] Logs backend : `docker-compose logs -f backend`
3. [ ] Logs Celery : `docker-compose logs -f celery_worker`
4. [ ] Redis accessible : `redis-cli ping`
5. [ ] Supabase accessible : vérifier dashboard
6. [ ] Rate limiting pas trop restrictif
7. [ ] Secrets bien configurés
8. [ ] Email provider API key valide
9. [ ] Webhooks configurés correctement
10. [ ] DNS résolu correctement

### Problèmes Courants

**Emails non envoyés:**
- [ ] Vérifier API key email provider
- [ ] Vérifier Celery worker actif
- [ ] Vérifier queue Celery (`celery -A core.celery_tasks inspect active`)
- [ ] Vérifier logs pour erreurs

**Webhooks non reçus:**
- [ ] Vérifier URL webhook accessible publiquement
- [ ] Vérifier signature webhook
- [ ] Vérifier logs webhooks dans dashboard provider
- [ ] Tester avec ngrok en local

**Performance lente:**
- [ ] Vérifier cache Redis
- [ ] Analyser slow queries dans Supabase
- [ ] Vérifier indexes DB
- [ ] Augmenter workers Celery

**Rate limiting trop agressif:**
- [ ] Ajuster `RATE_LIMIT_PER_MINUTE`
- [ ] Vérifier logs d'abus (IP bloquées)
- [ ] Whitelist IPs internes si nécessaire

## ✅ Déploiement Complet

Une fois toutes les cases cochées:

🎉 **Félicitations! Votre plateforme Email Campaign est en production!**

---

## 📞 Support

- Documentation: `/docs` (si DEBUG=true)
- Logs: `docker-compose logs -f`
- Health: `https://yourdomain.com/health`
- Metrics: `https://yourdomain.com/metrics`
- Flower: `https://yourdomain.com:5555` (si activé)

## 📚 Ressources

- [COMPLETE_IMPROVEMENTS.md](./COMPLETE_IMPROVEMENTS.md)
- [QUICK_START_GUIDE.md](./QUICK_START_GUIDE.md)
- [FINAL_REPORT.md](./FINAL_REPORT.md)
- Supabase Dashboard: https://app.supabase.com
- Provider Dashboard: SendGrid/Mailgun/AWS Console
