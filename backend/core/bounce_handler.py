"""
Bounce Handling Module

Provides:
- Webhook receivers for email provider bounces (SMTP-only stack)
- Automatic bounce classification (hard/soft)
- Automatic suppression list updates
- Bounce rate monitoring and alerts
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, Field

from core.config import get_settings
from core.supabase import get_supabase_client
from core.segmentation import get_segmentation_service, SuppressionListEntry

settings = get_settings()
logger = logging.getLogger(__name__)


class BounceType(str, Enum):
    HARD = "hard"  # Permanent failure
    SOFT = "soft"  # Temporary failure
    COMPLAINT = "complaint"  # Spam report
    UNSUBSCRIBE = "unsubscribe"


class BounceReason(str, Enum):
    INVALID_EMAIL = "invalid_email"
    MAILBOX_FULL = "mailbox_full"
    DOMAIN_NOT_FOUND = "domain_not_found"
    BLOCKED = "blocked"
    SPAM = "spam"
    POLICY = "policy"
    QUOTA = "quota"
    CONNECTION = "connection"
    UNKNOWN = "unknown"


@dataclass
class BounceEvent:
    """Standardized bounce event"""
    email: str
    bounce_type: BounceType
    reason: BounceReason
    provider_code: Optional[str]
    provider_message: Optional[str]
    campaign_id: Optional[UUID]
    recipient_id: Optional[UUID]
    timestamp: datetime
    raw_data: Dict[str, Any]


class BounceWebhookPayload(BaseModel):
    """Generic bounce webhook payload"""
    event_type: str
    email: str
    timestamp: Optional[str] = None
    reason: Optional[str] = None
    bounce_type: Optional[str] = None
    provider_data: Optional[Dict[str, Any]] = None


class BounceStats(BaseModel):
    """Bounce statistics"""
    total_bounces: int
    hard_bounces: int
    soft_bounces: int
    complaints: int
    bounce_rate: float
    complaint_rate: float
    by_domain: Dict[str, int]
    by_reason: Dict[str, int]


# Bounce classification rules
HARD_BOUNCE_CODES = [
    "550", "551", "552", "553", "554",  # SMTP codes
    "5.1.1", "5.1.2", "5.1.3",  # Enhanced codes - bad address
    "5.2.1",  # Mailbox disabled
]

SOFT_BOUNCE_CODES = [
    "421", "450", "451", "452",  # SMTP codes
    "4.2.2",  # Mailbox full
    "4.4.1", "4.4.2",  # Connection issues
]

SPAM_KEYWORDS = [
    "spam", "blocked", "blacklist", "rejected", "policy",
    "abuse", "reputation", "bulk"
]


def classify_bounce(code: str, message: str) -> tuple[BounceType, BounceReason]:
    """
    Classify a bounce based on error code and message.
    Returns (BounceType, BounceReason)
    """
    code = str(code).strip()
    message_lower = message.lower()
    
    # Check for spam/complaint indicators
    if any(kw in message_lower for kw in SPAM_KEYWORDS):
        return BounceType.COMPLAINT, BounceReason.SPAM
    
    # Check for hard bounce codes
    for hbc in HARD_BOUNCE_CODES:
        if code.startswith(hbc):
            if "mailbox" in message_lower and ("full" in message_lower or "quota" in message_lower):
                return BounceType.SOFT, BounceReason.MAILBOX_FULL
            if "domain" in message_lower or "host" in message_lower:
                return BounceType.HARD, BounceReason.DOMAIN_NOT_FOUND
            return BounceType.HARD, BounceReason.INVALID_EMAIL
    
    # Check for soft bounce codes
    for sbc in SOFT_BOUNCE_CODES:
        if code.startswith(sbc):
            if "full" in message_lower or "quota" in message_lower:
                return BounceType.SOFT, BounceReason.MAILBOX_FULL
            if "connection" in message_lower or "timeout" in message_lower:
                return BounceType.SOFT, BounceReason.CONNECTION
            return BounceType.SOFT, BounceReason.QUOTA
    
    # Default classification based on message content
    if "invalid" in message_lower or "not exist" in message_lower:
        return BounceType.HARD, BounceReason.INVALID_EMAIL
    if "blocked" in message_lower:
        return BounceType.SOFT, BounceReason.BLOCKED
    
    return BounceType.SOFT, BounceReason.UNKNOWN


class BounceHandler:
    """Handler for processing bounces"""
    
    def __init__(self):
        self.supabase = get_supabase_client()
        self.segmentation = get_segmentation_service()
    
    async def process_bounce(self, bounce: BounceEvent) -> Dict[str, Any]:
        """
        Process a bounce event:
        1. Log the bounce
        2. Update recipient status
        3. Add to suppression list if hard bounce
        4. Update campaign stats
        5. Check for threshold alerts
        """
        result = {
            "email": bounce.email,
            "bounce_type": bounce.bounce_type.value,
            "reason": bounce.reason.value,
            "actions_taken": [],
        }
        
        try:
            # 1. Log the bounce event
            log_data = {
                "email": bounce.email,
                "event_type": f"{bounce.bounce_type.value}_bounce",
                "error_code": bounce.provider_code,
                "error_message": bounce.provider_message,
                "event_data": bounce.raw_data,
                "timestamp": bounce.timestamp.isoformat(),
            }
            
            if bounce.campaign_id:
                log_data["campaign_id"] = str(bounce.campaign_id)
            if bounce.recipient_id:
                log_data["recipient_id"] = str(bounce.recipient_id)
            
            self.supabase.table("email_logs").insert(log_data).execute()
            result["actions_taken"].append("logged_event")
            
            # 2. Update recipient status if known
            if bounce.recipient_id:
                self.supabase.table("recipients").update({
                    "status": "bounced",
                    "error_message": bounce.provider_message[:500] if bounce.provider_message else None,
                }).eq("id", str(bounce.recipient_id)).execute()
                result["actions_taken"].append("updated_recipient")
            
            # 3. Add to suppression list if hard bounce or complaint
            if bounce.bounce_type in [BounceType.HARD, BounceType.COMPLAINT]:
                entry = SuppressionListEntry(
                    email=bounce.email,
                    reason=f"{bounce.bounce_type.value}: {bounce.reason.value}",
                    source="bounce",
                    is_global=True,
                )
                await self.segmentation.add_to_suppression_list([entry])
                result["actions_taken"].append("added_to_suppression")
            
            # 4. Update campaign stats if campaign known
            if bounce.campaign_id:
                self.supabase.rpc("increment_campaign_bounce", {
                    "p_campaign_id": str(bounce.campaign_id)
                }).execute()
                result["actions_taken"].append("updated_campaign_stats")
                
                # 5. Check bounce rate threshold
                await self._check_bounce_threshold(bounce.campaign_id)
            
            logger.info(f"Processed bounce for {bounce.email}: {result}")
            
        except Exception as e:
            logger.error(f"Error processing bounce for {bounce.email}: {e}")
            result["error"] = str(e)
        
        return result
    
    async def _check_bounce_threshold(
        self,
        campaign_id: UUID,
        threshold: float = 5.0  # 5% bounce rate
    ):
        """
        Check if campaign bounce rate exceeds threshold.
        Pause campaign if threshold exceeded.
        """
        campaign = self.supabase.table("campaigns").select(
            "sent_count, failed_count, status"
        ).eq("id", str(campaign_id)).single().execute()
        
        if not campaign.data:
            return
        
        data = campaign.data
        sent = data.get("sent_count", 0)
        failed = data.get("failed_count", 0)
        
        if sent < 100:  # Minimum sample size
            return
        
        bounce_rate = (failed / sent) * 100
        
        if bounce_rate >= threshold and data.get("status") == "sending":
            # Pause campaign
            self.supabase.table("campaigns").update({
                "status": "paused",
                "metadata": {
                    "pause_reason": f"Bounce rate {bounce_rate:.1f}% exceeded threshold {threshold}%",
                    "paused_at": datetime.utcnow().isoformat(),
                }
            }).eq("id", str(campaign_id)).execute()
            
            logger.warning(
                f"Campaign {campaign_id} paused: bounce rate {bounce_rate:.1f}%"
            )
            
            # TODO: Send alert notification
    
    async def get_bounce_stats(
        self,
        campaign_id: Optional[UUID] = None,
        days: int = 30
    ) -> BounceStats:
        """Get bounce statistics"""
        cutoff = (datetime.utcnow() - timedelta(days=days)).isoformat()
        
        query = self.supabase.table("email_logs").select(
            "email, event_type, error_code, error_message, timestamp"
        ).gte("timestamp", cutoff).in_(
            "event_type", ["hard_bounce", "soft_bounce", "bounced", "failed", "spam_report"]
        )
        
        if campaign_id:
            query = query.eq("campaign_id", str(campaign_id))
        
        result = query.execute()
        
        stats = {
            "total_bounces": 0,
            "hard_bounces": 0,
            "soft_bounces": 0,
            "complaints": 0,
            "by_domain": {},
            "by_reason": {},
        }
        
        for entry in result.data or []:
            stats["total_bounces"] += 1
            
            event_type = entry["event_type"]
            if event_type == "hard_bounce":
                stats["hard_bounces"] += 1
            elif event_type == "soft_bounce":
                stats["soft_bounces"] += 1
            elif event_type == "spam_report":
                stats["complaints"] += 1
            
            # Count by domain
            domain = entry["email"].split("@")[-1].lower()
            stats["by_domain"][domain] = stats["by_domain"].get(domain, 0) + 1
            
            # Count by reason
            reason = entry.get("error_message", "unknown")[:30]
            stats["by_reason"][reason] = stats["by_reason"].get(reason, 0) + 1
        
        # Calculate rates
        total_sent = 0
        if campaign_id:
            campaign = self.supabase.table("campaigns").select(
                "sent_count"
            ).eq("id", str(campaign_id)).single().execute()
            if campaign.data:
                total_sent = campaign.data.get("sent_count", 0)
        
        stats["bounce_rate"] = round(
            (stats["total_bounces"] / total_sent * 100) if total_sent > 0 else 0, 2
        )
        stats["complaint_rate"] = round(
            (stats["complaints"] / total_sent * 100) if total_sent > 0 else 0, 2
        )
        
        # Sort and limit dictionaries
        stats["by_domain"] = dict(
            sorted(stats["by_domain"].items(), key=lambda x: x[1], reverse=True)[:10]
        )
        stats["by_reason"] = dict(
            sorted(stats["by_reason"].items(), key=lambda x: x[1], reverse=True)[:10]
        )
        
        return BounceStats(**stats)

# Singleton instance
_bounce_handler: Optional[BounceHandler] = None


def get_bounce_handler() -> BounceHandler:
    """Get or create bounce handler instance"""
    global _bounce_handler
    if _bounce_handler is None:
        _bounce_handler = BounceHandler()
    return _bounce_handler
