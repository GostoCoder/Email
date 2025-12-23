# 📧 Analyse : Email de Réponse & Désinscription

## 🎯 Résumé

L'application implémente un **système complet de désinscription** conforme GDPR/CAN-SPAM avec :
- ✅ Email de réponse (Reply-To) configurable par campagne
- ✅ Lien de désinscription obligatoire dans chaque email
- ✅ Headers List-Unsubscribe pour désinscription en un clic
- ✅ Page publique de désinscription
- ✅ Blacklist globale

---

## 📧 1. EMAIL DE RÉPONSE (Reply-To)

### Configuration Frontend
**Fichier:** [frontend/src/components/campaigns/CampaignForm.tsx](frontend/src/components/campaigns/CampaignForm.tsx#L112-L119)

```tsx
<div className="form-group">
  <label htmlFor="reply_to">Email de réponse</label>
  <input
    type="email"
    id="reply_to"
    name="reply_to"
    value={formData.reply_to}
    onChange={handleChange}
    placeholder="reply@example.com (optionnel)"
  />
</div>
```

**Champ:** `reply_to` (optionnel)  
**Type:** Email  
**Placeholder:** `reply@example.com (optionnel)`

### Traitement Backend
**Fichier:** [backend/features/campaigns/tasks.py](backend/features/campaigns/tasks.py#L113)

```python
message = EmailMessage(
    to_email=recipient["email"],
    subject=campaign["subject"],
    html_content=html_content,
    from_email=campaign["from_email"],
    from_name=campaign["from_name"],
    reply_to=campaign.get("reply_to"),  # ✅ Utilisé ici
    custom_args={
        "campaign_id": str(campaign_id),
        "recipient_id": recipient["id"]
    },
    headers=unsubscribe_headers
)
```

**Comportement:**
- Récupéré depuis les données de la campagne
- Défini dans le header `Reply-To` de l'email
- Les réponses sont envoyées à cette adresse
- Optionnel (peut être vide)

---

## 🔕 2. SYSTÈME DE DÉSINSCRIPTION

### 2.1 Lien de Désinscription dans le Email

**Variable Template:** `{{unsubscribe_url}}`

**Format du lien généré:**
```
/unsubscribe?email={email}&campaign_id={campaign_id}
```

**Exemple dans template:**
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

**Fichier:** [backend/features/campaigns/tasks.py](backend/features/campaigns/tasks.py#L75-L85)

```python
unsubscribe_url = f"{base_url}/unsubscribe?email={recipient['email']}&campaign_id={campaign_id}"

# Variables injectées
recipient_data = {
    "firstname": recipient.get("first_name", ""),
    "lastname": recipient.get("last_name", ""),
    "company": recipient.get("company", ""),
    "subject": campaign["subject"],
    "unsubscribe_url": unsubscribe_url,  # ✅ Injecté
    **(recipient.get("custom_data", {}))
}
```

### 2.2 Headers List-Unsubscribe (One-Click)

**Fichier:** [backend/core/email_service.py](backend/core/email_service.py#L343-L349)

```python
def build_unsubscribe_headers(self, unsubscribe_url: str, campaign_email: str) -> Dict[str, str]:
    """
    Build List-Unsubscribe headers for email clients
    These headers enable one-click unsubscribe in email clients like Gmail
    """
    return {
        "List-Unsubscribe": f"<{unsubscribe_url}>, <mailto:{campaign_email}?subject=unsubscribe>",
        "List-Unsubscribe-Post": "List-Unsubscribe=One-Click"
    }
```

**Headers générés:**
```
List-Unsubscribe: <https://app.com/unsubscribe?email=...>, <mailto:contact@example.com?subject=unsubscribe>
List-Unsubscribe-Post: List-Unsubscribe=One-Click
```

**Résultat:**
- ✅ Bouton "Se désinscrire" dans Gmail
- ✅ Lien de désinscription dans Outlook
- ✅ Désinscription en un clic sans site web

---

## 🔐 3. PAGE DE DÉSINSCRIPTION PUBLIQUE

### Interface Utilisateur
**Fichier:** [frontend/src/components/UnsubscribePage.tsx](frontend/src/components/UnsubscribePage.tsx)

```tsx
export function UnsubscribePage() {
  const [searchParams] = useSearchParams();
  const [email, setEmail] = useState(searchParams.get('email') || '');
  const [reason, setReason] = useState('');
  const [status, setStatus] = useState<'form' | 'processing' | 'success' | 'error'>('form');

  const handleSubmit = async (e: React.FormEvent) => {
    // ...
    const campaignId = searchParams.get('campaign_id') || undefined;
    await campaignApi.unsubscribe(email, reason || undefined, campaignId);
    setStatus('success');
  };
```

**Étapes:**

1. **Formulaire** (`status === 'form'`)
   - Email pré-rempli depuis URL si présent
   - Champ raison optionnel
   - Bouton "Confirmer la désinscription"

2. **Traitement** (`status === 'processing'`)
   - Spinner de chargement
   - Message "Traitement en cours..."

3. **Succès** (`status === 'success'`)
   - Icône ✅
   - Confirmation de désinscription
   - Message "Vous ne recevrez plus d'emails marketing"

4. **Erreur** (`status === 'error'`)
   - Icône ❌
   - Message d'erreur
   - Bouton "Réessayer"

### Endpoint Backend
**Fichier:** [backend/features/campaigns/endpoints.py](backend/features/campaigns/endpoints.py#L738-L769)

```python
@router.post("/unsubscribe", response_model=UnsubscribeResponse, status_code=201)
async def unsubscribe(request: UnsubscribeCreate):
    """Public endpoint for email unsubscription"""
    supabase = get_supabase_client()
    
    # 1. Vérifier si déjà désinscrit
    existing = (
        supabase.table("unsubscribe_list")
        .select("id")
        .eq("email", request.email)
        .eq("is_global", True)
        .execute()
    )
    
    if existing.data:
        return existing.data[0]  # Déjà désinscrit
    
    # 2. Créer entrée de désinscription
    unsubscribe_data = request.model_dump()
    unsubscribe_data["is_global"] = True
    
    result = supabase.table("unsubscribe_list").insert(unsubscribe_data).execute()
    
    if not result.data:
        raise HTTPException(status_code=400, detail="Failed to process unsubscribe request")
    
    # 3. Mettre à jour les destinataires en attente
    supabase.table("recipients").update({
        "status": "unsubscribed",
        "unsubscribed_at": "now()"
    }).eq("email", request.email).in_("status", ["pending", "sending"]).execute()
    
    return result.data[0]
```

**Champs de désinscription:**
- `email` (requis)
- `reason` (optionnel)
- `campaign_id` (optionnel)
- `ip_address` (optionnel)
- `user_agent` (optionnel)

---

## 💾 4. BASE DE DONNÉES

### Table: unsubscribe_list
**Fichier:** [supabase/migrations/20241215000001_create_email_campaign_schema.sql](supabase/migrations/20241215000001_create_email_campaign_schema.sql#L76-L95)

```sql
CREATE TABLE IF NOT EXISTS unsubscribe_list (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) NOT NULL UNIQUE,
    reason TEXT,
    unsubscribed_at TIMESTAMPTZ DEFAULT NOW(),
    ip_address INET,
    user_agent TEXT,
    campaign_id UUID REFERENCES campaigns(id),
    is_global BOOLEAN DEFAULT TRUE,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

**Colonnes importantes:**
- `email` - Adresse email (UNIQUE)
- `reason` - Raison de désinscription fournie par l'utilisateur
- `is_global` - Si TRUE, désinscrit de TOUTES les campagnes
- `campaign_id` - Campagne à l'origine de la désinscription
- `ip_address` & `user_agent` - Audit trail
- `unsubscribed_at` - Timestamp de désinscription

### Fonction SQL: Vérifier si désinscrit
**Fichier:** [supabase/migrations/20241215000001_create_email_campaign_schema.sql](supabase/migrations/20241215000001_create_email_campaign_schema.sql#L178-L185)

```sql
CREATE OR REPLACE FUNCTION is_email_unsubscribed(check_email TEXT)
RETURNS BOOLEAN AS $$
BEGIN
    RETURN EXISTS(
        SELECT 1 FROM unsubscribe_list
        WHERE email = check_email AND is_global = TRUE
    );
END;
$$ LANGUAGE plpgsql;
```

Utilisée avant d'envoyer un email pour vérifier la blacklist.

---

## 🔗 5. FLUX COMPLET

### Avant Envoi de Campagne

```
┌─────────────────────┐
│  Créer Campagne     │
│  - from_email       │
│  - from_name        │
│  - reply_to ◄──────── EMAIL DE RÉPONSE
│  - html_content     │
│  - subject          │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ Vérifier Blacklist  │
│ (is_email_         │
│  unsubscribed)      │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  Générer URL        │
│  Unsubscribe        │
│  /unsubscribe?email │
│  &campaign_id       │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ Injecter Variables  │
│ {{unsubscribe_url}} │
│ {{firstname}}, etc  │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ Ajouter Headers     │
│ List-Unsubscribe    │
│ List-Unsubscribe-   │
│ Post: One-Click     │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ Envoyer Email       │
│ Avec Reply-To       │
└─────────────────────┘
```

### Lors de la Désinscription

```
┌──────────────────────────┐
│ Clic sur lien             │
│ /unsubscribe?email=...   │
│ &campaign_id=...         │
└──────────────┬───────────┘
               │
               ▼
┌──────────────────────────┐
│ UnsubscribePage affiche  │
│ formulaire avec email    │
│ pré-rempli               │
└──────────────┬───────────┘
               │
               ▼
┌──────────────────────────┐
│ Utilisateur Soumet:      │
│ - email                  │
│ - reason (optionnel)     │
│ - campaign_id (optionnel)│
└──────────────┬───────────┘
               │
               ▼
┌──────────────────────────┐
│ POST /unsubscribe        │
│ → Vérifier si déjà       │
│   désinscrit             │
│ → Insérer dans           │
│   unsubscribe_list       │
│ → Mettre à jour          │
│   recipients status      │
└──────────────┬───────────┘
               │
               ▼
┌──────────────────────────┐
│ Afficher Success Page    │
│ ✅ Désinscription        │
│    confirmée             │
└──────────────────────────┘
```

---

## 🧪 6. TESTS RECOMMANDÉS

### Test 1: Email de Réponse
```bash
1. Créer une campagne avec reply_to = "support@example.com"
2. Envoyer à un email de test
3. Vérifier le header "Reply-To" dans l'email reçu
4. Répondre à l'email
5. Confirmer que la réponse arrive à support@example.com
```

### Test 2: Lien de Désinscription
```bash
1. Vérifier que {{unsubscribe_url}} est présent dans le template
2. Recevoir l'email
3. Cliquer sur le lien "Se désinscrire"
4. Formulaire s'affiche avec email pré-rempli
5. Soumettre le formulaire
6. Page de succès affichée
```

### Test 3: Headers One-Click
```bash
1. Envoyer un email via la campagne
2. Ouvrir dans Gmail/Outlook
3. Vérifier que le bouton "Se désinscrire" apparaît
4. Cliquer sur le bouton
5. Confirmer désinscription immédiate
```

### Test 4: Blacklist Globale
```bash
1. Désinscrire une adresse email
2. Vérifier qu'elle est dans unsubscribe_list avec is_global=true
3. Créer une nouvelle campagne
4. Ajouter l'adresse désinscrite aux destinataires
5. Envoyer la campagne
6. Vérifier que l'adresse ne reçoit PAS l'email
```

### Test 5: Désinscription Déjà Effectuée
```bash
1. Désinscrire une adresse
2. Cliquer à nouveau sur le lien de désinscription
3. Soumettre le formulaire
4. Vérifier que la page de succès s'affiche (pas d'erreur)
```

---

## 📋 CONFORMITÉ LÉGALE

✅ **GDPR:**
- Lien de désinscription visible et facilement accessible
- Traitement immédiat de la demande
- Audit trail complet (ip_address, user_agent)

✅ **CAN-SPAM:**
- Header List-Unsubscribe obligatoire
- Lien de désinscription dans chaque email
- Adresse physique de l'expéditeur (À configurer)

✅ **CASL:**
- Consentement explicite requis
- Désinscription en un clic
- Respect de la blacklist

---

## 🚀 POINTS CLÉS

| Aspect | Implémentation |
|--------|----------------|
| **Email de Réponse** | Configurable par campagne (reply_to field) |
| **Lien Désinscription** | Variable `{{unsubscribe_url}}` injectée dans HTML |
| **One-Click Unsubscribe** | Headers List-Unsubscribe + List-Unsubscribe-Post |
| **Page Publique** | Route `/unsubscribe` accessible sans auth |
| **Blacklist Globale** | Table `unsubscribe_list` avec `is_global=true` |
| **Vérification Avant Envoi** | Fonction SQL `is_email_unsubscribed()` |
| **Audit Trail** | IP, User-Agent, Reason enregistrés |
| **Feedback** | Raison de désinscription optionnelle |

