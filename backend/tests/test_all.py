"""
Tests for Campaign Email Application

Provides:
- Unit tests for core services
- Integration tests for API endpoints
- Test fixtures and utilities
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any
from uuid import uuid4
from unittest.mock import Mock, patch, AsyncMock

# ==========================================
# Test Fixtures
# ==========================================

@pytest.fixture
def sample_campaign() -> Dict[str, Any]:
    """Sample campaign data"""
    return {
        "id": str(uuid4()),
        "name": "Test Campaign",
        "subject": "Test Subject - Hello {{firstname}}!",
        "from_name": "Test Sender",
        "from_email": "test@example.com",
        "reply_to": "reply@example.com",
        "html_content": "<html><body><h1>Hello {{firstname}}!</h1><p>Welcome to {{company}}.</p><a href='https://example.com'>Click here</a></body></html>",
        "status": "draft",
        "total_recipients": 0,
        "sent_count": 0,
        "failed_count": 0,
        "opened_count": 0,
        "clicked_count": 0,
        "batch_size": 100,
        "rate_limit_per_second": 10,
        "created_at": datetime.utcnow().isoformat(),
    }


@pytest.fixture
def sample_recipient() -> Dict[str, Any]:
    """Sample recipient data"""
    return {
        "id": str(uuid4()),
        "email": "recipient@example.com",
        "first_name": "John",
        "last_name": "Doe",
        "company": "Acme Inc",
        "custom_data": {"industry": "tech", "role": "developer"},
        "status": "pending",
    }


@pytest.fixture
def sample_recipients() -> list:
    """Multiple sample recipients"""
    return [
        {
            "id": str(uuid4()),
            "email": f"user{i}@example.com",
            "first_name": f"User{i}",
            "last_name": "Test",
            "company": "Test Co",
            "status": "pending",
        }
        for i in range(10)
    ]


# ==========================================
# Unit Tests - Retry Logic
# ==========================================

class TestRetryLogic:
    """Tests for email retry with backoff"""
    
    def test_should_retry_permanent_error_invalid_email(self):
        """Permanent errors should not retry"""
        from backend.features.campaigns.tasks import should_retry_email
        
        # These should NOT retry
        permanent_errors = [
            "Invalid email address: test@invalid",
            "Domain not found: invalid.domain",
            "User not found in domain",
            "Mailbox not found: user@domain.com",
            "Recipient address rejected",
            "Permanent failure: 550",
        ]
        
        for error in permanent_errors:
            result = should_retry_email(error, retry_count=0, max_retries=3)
            assert result is False, f"Should not retry: {error}"
    
    def test_should_retry_temporary_error(self):
        """Temporary errors should retry"""
        from backend.features.campaigns.tasks import should_retry_email
        
        # These should retry
        temporary_errors = [
            "Connection timeout",
            "Temporary failure, try again later",
            "Rate limit exceeded",
            "Mailbox full, quota exceeded",
            "Service unavailable",
            "Network error",
        ]
        
        for error in temporary_errors:
            result = should_retry_email(error, retry_count=0, max_retries=3)
            assert result is True, f"Should retry: {error}"
    
    def test_should_not_retry_after_max_attempts(self):
        """Should not retry after max attempts reached"""
        from backend.features.campaigns.tasks import should_retry_email
        
        result = should_retry_email(
            "Connection timeout",
            retry_count=3,
            max_retries=3
        )
        assert result is False


# ==========================================
# Unit Tests - Tracking
# ==========================================

class TestTracking:
    """Tests for email tracking functionality"""
    
    def test_generate_tracking_token(self):
        """Test tracking token generation"""
        from backend.core.tracking import generate_tracking_token, verify_tracking_token
        
        campaign_id = uuid4()
        recipient_id = uuid4()
        
        token = generate_tracking_token(campaign_id, recipient_id)
        
        assert token is not None
        assert len(token) > 0
        
        # Verify token (correct parameter order: campaign_id, recipient_id, token)
        is_valid = verify_tracking_token(campaign_id, recipient_id, token)
        assert is_valid is True
    
    def test_invalid_tracking_token(self):
        """Test invalid tracking token rejection"""
        from backend.core.tracking import verify_tracking_token
        
        campaign_id = uuid4()
        recipient_id = uuid4()
        
        # Correct parameter order: campaign_id, recipient_id, token
        is_valid = verify_tracking_token(
            campaign_id,
            recipient_id,
            "invalid_token"
        )
        assert is_valid is False
    
    def test_inject_tracking_pixel(self):
        """Test tracking pixel injection"""
        from backend.core.tracking import inject_tracking_into_html
        
        html = "<html><body><h1>Hello</h1></body></html>"
        campaign_id = uuid4()
        recipient_id = uuid4()
        
        result = inject_tracking_into_html(
            html,
            campaign_id,
            recipient_id,
            enable_open_tracking=True,
            enable_click_tracking=False
        )
        
        assert "/track/open" in result
        assert "img" in result.lower()
    
    def test_inject_click_tracking(self):
        """Test click tracking link wrapping"""
        from backend.core.tracking import inject_tracking_into_html
        
        html = '<html><body><a href="https://example.com">Click</a></body></html>'
        campaign_id = uuid4()
        recipient_id = uuid4()
        
        result = inject_tracking_into_html(
            html,
            campaign_id,
            recipient_id,
            enable_open_tracking=False,
            enable_click_tracking=True
        )
        
        assert "/track/click" in result
        assert "example.com" not in result.split("href=")[1].split(">")[0]
    
    def test_exclude_special_links_from_tracking(self):
        """Special links should not be tracked"""
        from backend.core.tracking import inject_tracking_into_html
        
        html = '''
        <html><body>
            <a href="mailto:test@example.com">Email</a>
            <a href="tel:+1234567890">Call</a>
            <a href="#section">Anchor</a>
            <a href="javascript:void(0)">JS</a>
        </body></html>
        '''
        campaign_id = uuid4()
        recipient_id = uuid4()
        
        result = inject_tracking_into_html(
            html,
            campaign_id,
            recipient_id,
            enable_click_tracking=True
        )
        
        # Special links should remain unchanged
        assert 'href="mailto:test@example.com"' in result
        assert 'href="tel:+1234567890"' in result
        assert 'href="#section"' in result


# ==========================================
# Unit Tests - Template Service
# ==========================================

class TestTemplateService:
    """Tests for template rendering"""
    
    def test_render_simple_variables(self):
        """Test basic variable substitution"""
        from backend.core.template_service import get_template_service
        
        service = get_template_service()
        
        template = "Hello {{firstname}} {{lastname}}!"
        data = {"firstname": "John", "lastname": "Doe"}
        
        result = service.render(template, data)
        
        assert result == "Hello John Doe!"
    
    def test_render_missing_variable(self):
        """Missing variables should be replaced with empty string"""
        from backend.core.template_service import get_template_service
        
        service = get_template_service()
        
        template = "Hello {{firstname}} from {{company}}!"
        data = {"firstname": "John"}
        
        result = service.render(template, data)
        
        assert result == "Hello John from !"
    
    def test_render_html_content(self):
        """Test HTML template rendering"""
        from backend.core.template_service import get_template_service
        
        service = get_template_service()
        
        template = "<h1>Welcome {{firstname}}</h1><p>Your company: {{company}}</p>"
        data = {"firstname": "Jane", "company": "Acme"}
        
        result = service.render(template, data)
        
        assert "<h1>Welcome Jane</h1>" in result
        assert "Your company: Acme" in result


# ==========================================
# Unit Tests - Rate Limiter
# ==========================================

class TestRateLimiter:
    """Tests for rate limiting"""
    
    def test_rate_limit_allows_requests_under_limit(self):
        """Requests under limit should be allowed"""
        from backend.core.rate_limiter import InMemoryRateLimiter
        
        limiter = InMemoryRateLimiter()
        
        for i in range(5):
            allowed, remaining = limiter.check_rate_limit(
                "test_client",
                max_requests=10,
                window_seconds=60
            )
            assert allowed is True
            assert remaining == 10 - i - 1
    
    def test_rate_limit_blocks_over_limit(self):
        """Requests over limit should be blocked"""
        from backend.core.rate_limiter import InMemoryRateLimiter
        
        limiter = InMemoryRateLimiter()
        
        # Use up the limit
        for _ in range(5):
            limiter.check_rate_limit("test_client", max_requests=5, window_seconds=60)
        
        # Next request should be blocked
        allowed, remaining = limiter.check_rate_limit(
            "test_client",
            max_requests=5,
            window_seconds=60
        )
        
        assert allowed is False
        assert remaining == 0
    
    def test_blocked_client(self):
        """Blocked clients should be rejected"""
        from backend.core.rate_limiter import InMemoryRateLimiter
        
        limiter = InMemoryRateLimiter()
        limiter.block("bad_client", duration_seconds=3600)
        
        assert limiter.is_blocked("bad_client") is True
        
        allowed, _ = limiter.check_rate_limit(
            "bad_client",
            max_requests=100,
            window_seconds=60
        )
        assert allowed is False


# ==========================================
# Unit Tests - Bounce Classification
# ==========================================

class TestBounceClassification:
    """Tests for bounce handling"""
    
    def test_classify_hard_bounce(self):
        """Test hard bounce classification"""
        from backend.core.bounce_handler import classify_bounce, BounceType, BounceReason
        
        bounce_type, reason = classify_bounce("550", "User not found")
        
        assert bounce_type == BounceType.HARD
    
    def test_classify_soft_bounce(self):
        """Test soft bounce classification"""
        from backend.core.bounce_handler import classify_bounce, BounceType, BounceReason
        
        bounce_type, reason = classify_bounce("451", "Mailbox full")
        
        assert bounce_type == BounceType.SOFT
        assert reason == BounceReason.MAILBOX_FULL
    
    def test_classify_spam_complaint(self):
        """Test spam complaint classification"""
        from backend.core.bounce_handler import classify_bounce, BounceType, BounceReason
        
        bounce_type, reason = classify_bounce("", "Message blocked due to spam")
        
        assert bounce_type == BounceType.COMPLAINT
        assert reason == BounceReason.SPAM


# ==========================================
# Unit Tests - A/B Testing Statistics
# ==========================================

class TestABTestingStats:
    """Tests for A/B testing statistical calculations"""
    
    def test_z_to_confidence_high_z(self):
        """High Z-score should give high confidence"""
        from backend.core.ab_testing import ABTestingService
        
        service = ABTestingService()
        
        confidence = service._z_to_confidence(3.0)
        assert confidence > 0.99
    
    def test_z_to_confidence_low_z(self):
        """Low Z-score should give low confidence"""
        from backend.core.ab_testing import ABTestingService
        
        service = ABTestingService()
        
        confidence = service._z_to_confidence(1.0)
        assert confidence < 0.85


# ==========================================
# Unit Tests - Segmentation Filters
# ==========================================

class TestSegmentationFilters:
    """Tests for recipient segmentation"""
    
    def test_filter_condition_equals(self):
        """Test equals filter"""
        from backend.core.segmentation import FilterCondition, FilterOperator
        
        condition = FilterCondition(
            field="status",
            operator=FilterOperator.EQUALS,
            value="sent"
        )
        
        assert condition.field == "status"
        assert condition.operator == FilterOperator.EQUALS
        assert condition.value == "sent"
    
    def test_filter_condition_contains(self):
        """Test contains filter"""
        from backend.core.segmentation import FilterCondition, FilterOperator
        
        condition = FilterCondition(
            field="email",
            operator=FilterOperator.CONTAINS,
            value="gmail.com"
        )
        
        assert condition.operator == FilterOperator.CONTAINS


# ==========================================
# Unit Tests - DNS Validation
# ==========================================

class TestDNSValidation:
    """Tests for DNS validation"""
    
    @pytest.mark.asyncio
    async def test_validate_known_domain(self):
        """Test validation of known good domain"""
        from backend.core.dns_validator import get_dns_validator
        
        validator = get_dns_validator()
        
        # Gmail should have valid records
        result = await validator.validate_domain("gmail.com")
        
        assert result["has_mx"] is True
        assert len(result["mx_records"]) > 0
    
    @pytest.mark.asyncio
    async def test_validate_invalid_domain(self):
        """Test validation of invalid domain"""
        from backend.core.dns_validator import get_dns_validator
        
        validator = get_dns_validator()
        
        result = await validator.validate_domain("this-domain-does-not-exist-12345.com")
        
        assert result["has_mx"] is False


# ==========================================
# Unit Tests - Analytics
# ==========================================

class TestAnalytics:
    """Tests for analytics calculations"""
    
    def test_calculate_open_rate(self):
        """Test open rate calculation"""
        sent = 1000
        opened = 250
        
        open_rate = (opened / sent) * 100
        
        assert open_rate == 25.0
    
    def test_calculate_click_rate(self):
        """Test click rate calculation"""
        sent = 1000
        clicked = 50
        
        click_rate = (clicked / sent) * 100
        
        assert click_rate == 5.0


# ==========================================
# Integration Tests - API Endpoints
# ==========================================

class TestAPIEndpoints:
    """Integration tests for API endpoints"""
    
    @pytest.fixture
    def client(self):
        """Create test client"""
        from fastapi.testclient import TestClient
        from backend.main import app
        
        return TestClient(app)
    
    def test_health_endpoint(self, client):
        """Test health check endpoint"""
        response = client.get("/health")
        
        assert response.status_code == 200
        assert response.json()["status"] == "ok"
    
    def test_root_endpoint(self, client):
        """Test root endpoint"""
        response = client.get("/")
        
        assert response.status_code == 200
        assert "status" in response.json()


# ==========================================
# Test Utilities
# ==========================================

def create_mock_supabase():
    """Create a mock Supabase client"""
    mock = Mock()
    
    # Mock table operations
    mock.table.return_value.select.return_value.execute.return_value.data = []
    mock.table.return_value.insert.return_value.execute.return_value.data = []
    mock.table.return_value.update.return_value.execute.return_value.data = []
    mock.table.return_value.delete.return_value.execute.return_value.data = []
    
    return mock


def generate_test_emails(count: int) -> list:
    """Generate test email addresses"""
    return [f"test{i}@example.com" for i in range(count)]


def generate_test_campaign_data() -> dict:
    """Generate random campaign data for testing"""
    return {
        "name": f"Test Campaign {uuid4().hex[:8]}",
        "subject": "Test Subject",
        "from_name": "Test Sender",
        "from_email": "test@example.com",
        "html_content": "<h1>Test</h1>",
    }


# ==========================================
# Run Tests
# ==========================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
