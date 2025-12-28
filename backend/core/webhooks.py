"""
Webhook Service
Send notifications to external URLs when events occur (sent, opened, clicked, etc.)
"""

import asyncio
import hashlib
import hmac
import logging
from datetime import datetime
from typing import Dict, Optional, List
from uuid import UUID

import httpx

from core.config import get_settings
from core.supabase import get_supabase_client

settings = get_settings()
logger = logging.getLogger(__name__)


class WebhookService:
    """Service for sending webhook notifications"""
    
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=10.0)
    
    async def send_webhook(
        self,
        webhook_url: str,
        event_type: str,
        data: Dict,
        secret: Optional[str] = None
    ) -> bool:
        """
        Send a webhook notification to an external URL.
        
        Args:
            webhook_url: URL to send webhook to
            event_type: Type of event (email.sent, email.opened, email.clicked, etc.)
            data: Event data payload
            secret: Optional secret for HMAC signature
        
        Returns:
            True if webhook delivered successfully
        """
        try:
            payload = {
                "event": event_type,
                "timestamp": datetime.utcnow().isoformat(),
                "data": data
            }
            
            headers = {
                "Content-Type": "application/json",
                "User-Agent": "EmailCampaign-Webhook/1.0"
            }
            
            # Add HMAC signature if secret provided
            if secret:
                signature = self._generate_signature(payload, secret)
                headers["X-Webhook-Signature"] = signature
            
            response = await self.client.post(
                webhook_url,
                json=payload,
                headers=headers
            )
            
            if response.status_code >= 200 and response.status_code < 300:
                logger.info(f"Webhook delivered: {event_type} to {webhook_url}")
                return True
            else:
                logger.warning(
                    f"Webhook failed: {event_type} to {webhook_url} - "
                    f"Status {response.status_code}"
                )
                return False
        
        except Exception as e:
            logger.error(f"Webhook error for {webhook_url}: {str(e)}")
            return False
    
    def _generate_signature(self, payload: Dict, secret: str) -> str:
        """Generate HMAC-SHA256 signature for webhook verification"""
        import json
        
        payload_bytes = json.dumps(payload, sort_keys=True).encode('utf-8')
        signature = hmac.new(
            secret.encode('utf-8'),
            payload_bytes,
            hashlib.sha256
        ).hexdigest()
        
        return f"sha256={signature}"
    
    async def notify_email_sent(
        self,
        campaign_id: UUID,
        recipient_id: UUID,
        email: str,
        webhook_url: Optional[str] = None,
        secret: Optional[str] = None
    ):
        """Send webhook notification for email sent event"""
        if not webhook_url:
            return
        
        data = {
            "campaign_id": str(campaign_id),
            "recipient_id": str(recipient_id),
            "email": email,
            "status": "sent"
        }
        
        await self.send_webhook(webhook_url, "email.sent", data, secret)
    
    async def notify_email_opened(
        self,
        campaign_id: UUID,
        recipient_id: UUID,
        email: str,
        webhook_url: Optional[str] = None,
        secret: Optional[str] = None
    ):
        """Send webhook notification for email opened event"""
        if not webhook_url:
            return
        
        data = {
            "campaign_id": str(campaign_id),
            "recipient_id": str(recipient_id),
            "email": email,
            "status": "opened"
        }
        
        await self.send_webhook(webhook_url, "email.opened", data, secret)
    
    async def notify_email_clicked(
        self,
        campaign_id: UUID,
        recipient_id: UUID,
        email: str,
        url: str,
        webhook_url: Optional[str] = None,
        secret: Optional[str] = None
    ):
        """Send webhook notification for email clicked event"""
        if not webhook_url:
            return
        
        data = {
            "campaign_id": str(campaign_id),
            "recipient_id": str(recipient_id),
            "email": email,
            "url": url,
            "status": "clicked"
        }
        
        await self.send_webhook(webhook_url, "email.clicked", data, secret)
    
    async def notify_email_failed(
        self,
        campaign_id: UUID,
        recipient_id: UUID,
        email: str,
        error_message: str,
        webhook_url: Optional[str] = None,
        secret: Optional[str] = None
    ):
        """Send webhook notification for email failed event"""
        if not webhook_url:
            return
        
        data = {
            "campaign_id": str(campaign_id),
            "recipient_id": str(recipient_id),
            "email": email,
            "error": error_message,
            "status": "failed"
        }
        
        await self.send_webhook(webhook_url, "email.failed", data, secret)
    
    async def notify_campaign_completed(
        self,
        campaign_id: UUID,
        stats: Dict,
        webhook_url: Optional[str] = None,
        secret: Optional[str] = None
    ):
        """Send webhook notification when campaign completes"""
        if not webhook_url:
            return
        
        data = {
            "campaign_id": str(campaign_id),
            "status": "completed",
            **stats
        }
        
        await self.send_webhook(webhook_url, "campaign.completed", data, secret)
    
    async def close(self):
        """Close the HTTP client"""
        await self.client.aclose()


# Global webhook service instance
_webhook_service: Optional[WebhookService] = None


def get_webhook_service() -> WebhookService:
    """Get or create webhook service singleton"""
    global _webhook_service
    if _webhook_service is None:
        _webhook_service = WebhookService()
    return _webhook_service


async def get_campaign_webhooks(campaign_id: UUID) -> Optional[Dict]:
    """Get webhook configuration for a campaign"""
    supabase = get_supabase_client()
    
    campaign_result = supabase.table("campaigns").select("metadata").eq("id", str(campaign_id)).execute()
    
    if not campaign_result.data:
        return None
    
    metadata = campaign_result.data[0].get("metadata", {})
    webhooks = metadata.get("webhooks", {})
    
    return webhooks if webhooks.get("enabled") else None
