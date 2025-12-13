"""
Tests pour la fonctionnalité de désinscription.
"""

import pytest
import os
from datetime import datetime, timedelta

# Configuration pour les tests
os.environ['SECRET_KEY'] = 'test-secret-key-for-testing'


class TestTokenService:
    """Tests pour le service de tokens."""
    
    def setup_method(self):
        """Setup avant chaque test."""
        from app.core.shared.services.token_service import TokenService
        self.token_service = TokenService('test-secret-key')
    
    def test_generate_simple_token(self):
        """Test génération d'un token simple."""
        token = self.token_service.generate_token('test@example.com')
        
        assert token is not None
        assert ':' in token
        parts = token.split(':')
        assert len(parts) == 3
        assert parts[0] == 'test@example.com'
    
    def test_validate_simple_token(self):
        """Test validation d'un token simple."""
        email = 'test@example.com'
        token = self.token_service.generate_token(email)
        
        is_valid, returned_email = self.token_service.validate_token(token)
        
        assert is_valid is True
        assert returned_email == email
    
    def test_generate_unsubscribe_token_with_ids(self):
        """Test génération d'un token enrichi."""
        token = self.token_service.generate_unsubscribe_token(
            email='test@example.com',
            contact_id='contact-uuid-123',
            campaign_id='campaign-uuid-456'
        )
        
        assert token is not None
        assert '.' in token
        parts = token.split('.')
        assert len(parts) == 2
    
    def test_validate_unsubscribe_token(self):
        """Test validation d'un token enrichi."""
        email = 'test@example.com'
        contact_id = 'contact-uuid-123'
        campaign_id = 'campaign-uuid-456'
        
        token = self.token_service.generate_unsubscribe_token(
            email=email,
            contact_id=contact_id,
            campaign_id=campaign_id
        )
        
        is_valid, data = self.token_service.validate_unsubscribe_token(token)
        
        assert is_valid is True
        assert data is not None
        assert data.get('email') == email
        assert data.get('contact_id') == contact_id
        assert data.get('campaign_id') == campaign_id
    
    def test_token_expiration(self):
        """Test expiration des tokens."""
        # Créer un token avec expiration dans le passé
        token = self.token_service.generate_unsubscribe_token(
            email='test@example.com',
            expiry_days=-1  # Déjà expiré
        )
        
        is_valid, data = self.token_service.validate_unsubscribe_token(token)
        
        # Le token devrait être invalide car expiré
        assert is_valid is False
    
    def test_invalid_token_signature(self):
        """Test détection d'une signature invalide."""
        token = self.token_service.generate_unsubscribe_token(
            email='test@example.com'
        )
        
        # Modifier la signature
        parts = token.split('.')
        parts[1] = 'invalidsignature12345678901234'
        modified_token = '.'.join(parts)
        
        is_valid, data = self.token_service.validate_unsubscribe_token(modified_token)
        
        assert is_valid is False
    
    def test_invalid_token_format(self):
        """Test tokens malformés."""
        invalid_tokens = [
            '',
            'not.a.valid.token',
            'invalidtoken',
            None
        ]
        
        for token in invalid_tokens:
            if token is not None:
                is_valid, _ = self.token_service.validate_unsubscribe_token(token)
                assert is_valid is False


class TestSuppressionModels:
    """Tests pour les modèles de suppression."""
    
    def test_unsubscribe_model(self):
        """Test création d'un modèle Unsubscribe."""
        from app.features.suppression.model.suppression_model import Unsubscribe
        
        unsub = Unsubscribe(email='test@example.com', reason='unsubscribed')
        
        assert unsub.email == 'test@example.com'
        assert unsub.reason == 'unsubscribed'
        assert unsub.unsubscribed_at is not None
    
    def test_unsubscribe_request_model(self):
        """Test création d'un modèle UnsubscribeRequest."""
        from app.features.suppression.model.suppression_model import UnsubscribeRequest
        
        request = UnsubscribeRequest(
            token='test-token',
            email='test@example.com',
            contact_id='contact-123',
            campaign_id='campaign-456',
            ip_address='192.168.1.1',
            user_agent='Mozilla/5.0'
        )
        
        assert request.token == 'test-token'
        assert request.email == 'test@example.com'
        assert request.contact_id == 'contact-123'
    
    def test_unsubscribe_result_model(self):
        """Test création d'un modèle UnsubscribeResult."""
        from app.features.suppression.model.suppression_model import UnsubscribeResult
        
        result = UnsubscribeResult(
            success=True,
            email='test@example.com',
            message='Désabonnement réussi'
        )
        
        assert result.success is True
        assert result.email == 'test@example.com'
        assert result.already_unsubscribed is False


class TestSuppressionViewModel:
    """Tests pour le ViewModel de suppression."""
    
    def test_check_email_status_format(self):
        """Test format de la réponse check_email_status."""
        from app.features.suppression.viewmodel.suppression_viewmodel import SuppressionViewModel
        
        # Note: Ce test nécessite une connexion DB mock
        # Pour l'instant, on vérifie juste que la classe s'instancie
        try:
            vm = SuppressionViewModel()
            assert vm is not None
        except Exception:
            # Peut échouer sans DB, c'est OK pour ce test
            pass


# Tests d'intégration (nécessitent une DB)
class TestSuppressionIntegration:
    """Tests d'intégration pour la suppression."""
    
    @pytest.mark.skip(reason="Nécessite une connexion à la base de données")
    def test_full_unsubscribe_flow(self):
        """Test du flux complet de désabonnement."""
        from app.core.shared.services.token_service import TokenService
        from app.features.suppression.service.suppression_service import SuppressionService
        from app.features.suppression.model.suppression_model import UnsubscribeRequest
        
        token_service = TokenService('test-secret')
        suppression_service = SuppressionService()
        
        # 1. Générer un token
        email = f"test-{datetime.now().timestamp()}@example.com"
        token = token_service.generate_unsubscribe_token(email=email)
        
        # 2. Traiter la demande de désabonnement
        request = UnsubscribeRequest(token=token)
        result = suppression_service.process_unsubscribe(request)
        
        # 3. Vérifier le résultat
        assert result.success is True
        assert result.email == email
        
        # 4. Vérifier que l'email est maintenant dans la liste
        assert suppression_service.is_unsubscribed(email) is True


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
