"""
Routes Flask pour les désabonnements.
Implémente les endpoints API et les pages de désinscription utilisateur.
"""

from flask import Blueprint, jsonify, request, render_template_string
from app.features.suppression.viewmodel.suppression_viewmodel import SuppressionViewModel

suppression_bp = Blueprint('suppression', __name__)
suppression_vm = SuppressionViewModel()


# =============================================================================
# API Endpoints (JSON)
# =============================================================================

@suppression_bp.route('/unsubscribe', methods=['POST'])
def unsubscribe():
    """
    Désabonne un email via token.
    
    Body JSON:
        - token: Le token de désabonnement (obligatoire)
        - reason: Raison du désabonnement (optionnel)
    
    Returns:
        JSON avec success, message, email
    """
    data = request.get_json() or {}
    token = data.get('token')
    reason = data.get('reason', '')
    
    if not token:
        return jsonify({
            'success': False,
            'error': 'Token manquant'
        }), 400
    
    # Récupérer les infos de la requête pour audit
    ip_address = request.headers.get('X-Forwarded-For', request.remote_addr)
    user_agent = request.headers.get('User-Agent', '')
    
    result = suppression_vm.unsubscribe_command(
        token=token,
        reason=reason,
        ip_address=ip_address,
        user_agent=user_agent
    )
    
    if result['success']:
        return jsonify(result), 200
    else:
        return jsonify(result), 400


@suppression_bp.route('/list', methods=['GET'])
def list_unsubscribed():
    """Liste tous les emails désabonnés."""
    result = suppression_vm.get_all_unsubscribed()
    return jsonify(result), 200


@suppression_bp.route('/logs', methods=['GET'])
def get_logs():
    """
    Récupère les logs de désabonnements.
    
    Query params:
        - limit: Nombre max de logs (défaut: 100)
        - email: Filtrer par email
        - campaign_id: Filtrer par campagne
    """
    limit = request.args.get('limit', 100, type=int)
    email = request.args.get('email')
    campaign_id = request.args.get('campaign_id')
    
    result = suppression_vm.get_unsubscribe_logs(
        limit=limit,
        email=email,
        campaign_id=campaign_id
    )
    return jsonify(result), 200


@suppression_bp.route('/add', methods=['POST'])
def add_unsubscribe():
    """
    Ajoute manuellement un email à la liste de suppression.
    
    Body JSON:
        - email: L'email à désabonner (obligatoire)
        - reason: Raison du désabonnement (optionnel)
    """
    data = request.get_json() or {}
    email = data.get('email')
    reason = data.get('reason', 'manual')
    
    if not email:
        return jsonify({
            'success': False,
            'error': 'Email manquant'
        }), 400
    
    result = suppression_vm.add_unsubscribe_command(email, reason)
    
    if result['success']:
        return jsonify(result), 200
    else:
        return jsonify(result), 400


@suppression_bp.route('/remove', methods=['POST'])
def remove_unsubscribe():
    """Retire un email de la liste de suppression."""
    data = request.get_json() or {}
    email = data.get('email')
    
    if not email:
        return jsonify({
            'success': False,
            'error': 'Email manquant'
        }), 400
    
    result = suppression_vm.remove_unsubscribe_command(email)
    
    if result['success']:
        return jsonify(result), 200
    else:
        return jsonify(result), 404


@suppression_bp.route('/check', methods=['GET'])
def check_email():
    """
    Vérifie si un email est désabonné.
    
    Query params:
        - email: L'email à vérifier
    """
    email = request.args.get('email')
    
    if not email:
        return jsonify({
            'success': False,
            'error': 'Email manquant'
        }), 400
    
    result = suppression_vm.check_email_status(email)
    return jsonify(result), 200


@suppression_bp.route('/generate-token', methods=['POST'])
def generate_token():
    """
    Génère un token et URL de désabonnement.
    
    Body JSON:
        - email: L'email du contact (obligatoire)
        - contact_id: UUID du contact (optionnel)
        - campaign_id: UUID de la campagne (optionnel)
    """
    data = request.get_json() or {}
    email = data.get('email')
    
    if not email:
        return jsonify({
            'success': False,
            'error': 'Email manquant'
        }), 400
    
    result = suppression_vm.generate_unsubscribe_url(
        email=email,
        contact_id=data.get('contact_id'),
        campaign_id=data.get('campaign_id')
    )
    
    return jsonify(result), 200


# =============================================================================
# Pages HTML pour l'utilisateur final
# =============================================================================

# Template CSS commun pour les pages de désabonnement
UNSUBSCRIBE_CSS = """
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body { 
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        min-height: 100vh;
        display: flex;
        align-items: center;
        justify-content: center;
        padding: 20px;
    }
    .container {
        background: white;
        border-radius: 16px;
        box-shadow: 0 20px 60px rgba(0,0,0,0.3);
        max-width: 480px;
        width: 100%;
        padding: 40px;
        text-align: center;
    }
    .icon {
        width: 80px;
        height: 80px;
        margin: 0 auto 20px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 40px;
    }
    .icon-warning { background: #fff3cd; }
    .icon-success { background: #d4edda; }
    .icon-error { background: #f8d7da; }
    h1 {
        color: #333;
        font-size: 24px;
        margin-bottom: 15px;
        font-weight: 600;
    }
    p {
        color: #666;
        line-height: 1.6;
        margin-bottom: 20px;
    }
    .email {
        background: #f8f9fa;
        padding: 10px 20px;
        border-radius: 8px;
        font-family: monospace;
        color: #495057;
        margin-bottom: 25px;
        word-break: break-all;
    }
    button, .btn {
        display: inline-block;
        padding: 14px 32px;
        border: none;
        border-radius: 8px;
        font-size: 16px;
        font-weight: 600;
        cursor: pointer;
        transition: all 0.3s ease;
        text-decoration: none;
    }
    .btn-danger {
        background: linear-gradient(135deg, #dc3545 0%, #c82333 100%);
        color: white;
    }
    .btn-danger:hover {
        transform: translateY(-2px);
        box-shadow: 0 5px 20px rgba(220, 53, 69, 0.4);
    }
    .btn-secondary {
        background: #6c757d;
        color: white;
        margin-left: 10px;
    }
    .btn-secondary:hover {
        background: #5a6268;
    }
    .btn-primary {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
    }
    .btn-primary:hover {
        transform: translateY(-2px);
        box-shadow: 0 5px 20px rgba(102, 126, 234, 0.4);
    }
    .spinner {
        display: none;
        width: 20px;
        height: 20px;
        border: 3px solid #f3f3f3;
        border-top: 3px solid #667eea;
        border-radius: 50%;
        animation: spin 1s linear infinite;
        margin: 0 auto 20px;
    }
    @keyframes spin {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
    }
    .footer {
        margin-top: 30px;
        padding-top: 20px;
        border-top: 1px solid #eee;
        font-size: 13px;
        color: #999;
    }
    .footer a { color: #667eea; text-decoration: none; }
    .footer a:hover { text-decoration: underline; }
    .reason-input {
        width: 100%;
        padding: 12px;
        border: 1px solid #ddd;
        border-radius: 8px;
        font-size: 14px;
        margin-bottom: 20px;
        resize: vertical;
    }
    .reason-input:focus {
        outline: none;
        border-color: #667eea;
        box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
    }
    .hidden { display: none; }
"""


@suppression_bp.route('/page/<token>', methods=['GET'])
def unsubscribe_page(token: str):
    """
    Page de confirmation de désabonnement pour l'utilisateur final.
    Affiche un formulaire de confirmation avant de désabonner.
    """
    html = f"""
    <!DOCTYPE html>
    <html lang="fr">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Se désabonner</title>
        <style>{UNSUBSCRIBE_CSS}</style>
    </head>
    <body>
        <div class="container" id="confirmContainer">
            <div class="icon icon-warning">📧</div>
            <h1>Confirmer le désabonnement</h1>
            <p>
                Vous êtes sur le point de vous désabonner de notre liste de diffusion.
                Vous ne recevrez plus nos emails.
            </p>
            
            <div style="margin-bottom: 20px;">
                <label for="reason" style="display: block; text-align: left; margin-bottom: 8px; color: #666; font-size: 14px;">
                    Raison (optionnel) :
                </label>
                <textarea id="reason" class="reason-input" rows="2" 
                    placeholder="Dites-nous pourquoi vous partez..."></textarea>
            </div>
            
            <div class="spinner" id="spinner"></div>
            
            <div id="buttons">
                <button class="btn btn-danger" onclick="confirmUnsubscribe()">
                    Confirmer le désabonnement
                </button>
            </div>
            
            <div class="footer">
                <p>Vous avez changé d'avis ? Fermez simplement cette page.</p>
            </div>
        </div>
        
        <div class="container hidden" id="successContainer">
            <div class="icon icon-success">✓</div>
            <h1>Désabonnement confirmé</h1>
            <p id="successMessage">
                Vous avez été désabonné·e avec succès.
                Vous ne recevrez plus nos communications.
            </p>
            <div class="footer">
                <p>Vous vous êtes désabonné·e par erreur ?<br>
                <a href="mailto:support@exemple.com">Contactez-nous</a> pour vous réinscrire.</p>
            </div>
        </div>
        
        <div class="container hidden" id="errorContainer">
            <div class="icon icon-error">✗</div>
            <h1>Une erreur est survenue</h1>
            <p id="errorMessage">
                Impossible de traiter votre demande.
            </p>
            <a href="mailto:support@exemple.com" class="btn btn-primary">
                Nous contacter
            </a>
        </div>
        
        <script>
            const token = '{token}';
            
            async function confirmUnsubscribe() {{
                const spinner = document.getElementById('spinner');
                const buttons = document.getElementById('buttons');
                const reason = document.getElementById('reason').value;
                
                spinner.style.display = 'block';
                buttons.style.display = 'none';
                
                try {{
                    const response = await fetch('/api/suppression/unsubscribe', {{
                        method: 'POST',
                        headers: {{ 'Content-Type': 'application/json' }},
                        body: JSON.stringify({{ 
                            token: token,
                            reason: reason
                        }})
                    }});
                    
                    const data = await response.json();
                    
                    if (data.success) {{
                        document.getElementById('confirmContainer').classList.add('hidden');
                        document.getElementById('successContainer').classList.remove('hidden');
                        
                        if (data.message) {{
                            document.getElementById('successMessage').textContent = data.message;
                        }}
                    }} else {{
                        document.getElementById('confirmContainer').classList.add('hidden');
                        document.getElementById('errorContainer').classList.remove('hidden');
                        
                        if (data.error || data.message) {{
                            document.getElementById('errorMessage').textContent = 
                                data.error || data.message;
                        }}
                    }}
                }} catch (error) {{
                    document.getElementById('confirmContainer').classList.add('hidden');
                    document.getElementById('errorContainer').classList.remove('hidden');
                    document.getElementById('errorMessage').textContent = 
                        'Erreur de connexion. Veuillez réessayer.';
                }}
            }}
        </script>
    </body>
    </html>
    """
    return render_template_string(html)


@suppression_bp.route('/success', methods=['GET'])
def unsubscribe_success():
    """Page de succès de désabonnement (accès direct possible)."""
    html = f"""
    <!DOCTYPE html>
    <html lang="fr">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Désabonnement confirmé</title>
        <style>{UNSUBSCRIBE_CSS}</style>
    </head>
    <body>
        <div class="container">
            <div class="icon icon-success">✓</div>
            <h1>Désabonnement confirmé</h1>
            <p>
                Vous avez été désabonné·e avec succès de notre liste de diffusion.
                Vous ne recevrez plus nos communications par email.
            </p>
            <div class="footer">
                <p>Vous vous êtes désabonné·e par erreur ?<br>
                <a href="mailto:support@exemple.com">Contactez-nous</a> pour vous réinscrire.</p>
            </div>
        </div>
    </body>
    </html>
    """
    return render_template_string(html)


@suppression_bp.route('/error', methods=['GET'])
def unsubscribe_error():
    """Page d'erreur de désabonnement."""
    error_message = request.args.get('message', 'Le lien de désabonnement est invalide ou a expiré.')
    
    html = f"""
    <!DOCTYPE html>
    <html lang="fr">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Erreur de désabonnement</title>
        <style>{UNSUBSCRIBE_CSS}</style>
    </head>
    <body>
        <div class="container">
            <div class="icon icon-error">✗</div>
            <h1>Lien invalide</h1>
            <p>{error_message}</p>
            <p>
                Si vous souhaitez vous désabonner, veuillez utiliser le lien
                dans un de nos emails récents ou nous contacter directement.
            </p>
            <a href="mailto:support@exemple.com" class="btn btn-primary">
                Nous contacter
            </a>
        </div>
    </body>
    </html>
    """
    return render_template_string(html)
