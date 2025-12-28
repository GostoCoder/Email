"""
Bounce Handling Endpoints

Webhook receivers for email providers to report bounces, complaints, and delivery events.
"""

import hashlib
import hmac
import json
import logging
from typing import Optional
from datetime import datetime

from fastapi import APIRouter, Request, Header, HTTPException, BackgroundTasks

from core.config import settings
from core.bounce_handler import (
    get_bounce_handler,
    SendGridWebhookHandler,
    MailgunWebhookHandler,
    SESWebhookHandler,
    BounceType,
)

router = APIRouter()
logger = logging.getLogger(__name__)


def verify_sendgrid_webhook(
    payload: bytes,
    signature: str,
    timestamp: str,
) -> bool:
    """Verify SendGrid webhook signature"""
    verification_key = getattr(settings, "SENDGRID_WEBHOOK_VERIFICATION_KEY", None)
    
    if not verification_key:
        # If no key configured, allow in development
        return settings.DEBUG
    
    timestamped_payload = timestamp.encode() + payload
    computed_signature = hmac.new(
        verification_key.encode(),
        timestamped_payload,
        hashlib.sha256
    ).hexdigest()
    
    return hmac.compare_digest(signature, computed_signature)


def verify_mailgun_webhook(
    token: str,
    timestamp: str,
    signature: str,
) -> bool:
    """Verify Mailgun webhook signature"""
    api_key = settings.MAILGUN_API_KEY
    
    if not api_key:
        return settings.DEBUG
    
    data = f"{timestamp}{token}"
    computed_signature = hmac.new(
        api_key.encode(),
        data.encode(),
        hashlib.sha256
    ).hexdigest()
    
    return hmac.compare_digest(signature, computed_signature)


@router.post("/webhooks/sendgrid")
async def sendgrid_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    x_twilio_email_event_webhook_signature: Optional[str] = Header(None),
    x_twilio_email_event_webhook_timestamp: Optional[str] = Header(None),
):
    """
    Receive SendGrid Event Webhooks
    
    Handles:
    - bounce
    - dropped
    - deferred
    - delivered
    - open
    - click
    - spam_report
    - unsubscribe
    """
    body = await request.body()
    
    # Verify signature in production
    if not settings.DEBUG:
        if not x_twilio_email_event_webhook_signature:
            raise HTTPException(status_code=401, detail="Missing signature")
        
        if not verify_sendgrid_webhook(
            body,
            x_twilio_email_event_webhook_signature,
            x_twilio_email_event_webhook_timestamp or ""
        ):
            raise HTTPException(status_code=401, detail="Invalid signature")
    
    try:
        events = json.loads(body)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON")
    
    handler = SendGridWebhookHandler()
    bounce_handler = get_bounce_handler()
    
    processed = 0
    errors = []
    
    for event in events:
        try:
            event_type = event.get("event", "")
            
            # Process bounces and spam reports
            if event_type in ["bounce", "dropped", "spam_report"]:
                bounce_event = handler.parse_event(event)
                
                if bounce_event:
                    background_tasks.add_task(
                        bounce_handler.process_bounce,
                        bounce_event
                    )
                    processed += 1
            
            # Update delivery status
            elif event_type == "delivered":
                email = event.get("email")
                if email:
                    background_tasks.add_task(
                        update_delivery_status,
                        email,
                        "delivered",
                        event
                    )
                    processed += 1
            
            # Track opens
            elif event_type == "open":
                email = event.get("email")
                campaign_id = event.get("campaign_id")
                if email:
                    background_tasks.add_task(
                        track_open_event,
                        email,
                        campaign_id,
                        event
                    )
                    processed += 1
            
            # Track clicks
            elif event_type == "click":
                email = event.get("email")
                url = event.get("url")
                campaign_id = event.get("campaign_id")
                if email and url:
                    background_tasks.add_task(
                        track_click_event,
                        email,
                        url,
                        campaign_id,
                        event
                    )
                    processed += 1
            
            # Handle unsubscribes
            elif event_type == "unsubscribe":
                email = event.get("email")
                if email:
                    background_tasks.add_task(
                        process_unsubscribe,
                        email,
                        "sendgrid_webhook",
                        event
                    )
                    processed += 1
        
        except Exception as e:
            logger.error(f"Error processing SendGrid event: {e}")
            errors.append(str(e))
    
    return {
        "processed": processed,
        "total": len(events),
        "errors": len(errors),
    }


@router.post("/webhooks/mailgun")
async def mailgun_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
):
    """
    Receive Mailgun Event Webhooks
    
    Handles:
    - bounced
    - failed
    - rejected
    - delivered
    - opened
    - clicked
    - complained
    - unsubscribed
    """
    form_data = await request.form()
    data = dict(form_data)
    
    # Verify signature
    if not settings.DEBUG:
        signature = data.get("signature", {})
        if isinstance(signature, str):
            signature = json.loads(signature)
        
        if not verify_mailgun_webhook(
            signature.get("token", ""),
            signature.get("timestamp", ""),
            signature.get("signature", ""),
        ):
            raise HTTPException(status_code=401, detail="Invalid signature")
    
    event_data = data.get("event-data", {})
    if isinstance(event_data, str):
        event_data = json.loads(event_data)
    
    event_type = event_data.get("event", "")
    
    handler = MailgunWebhookHandler()
    bounce_handler = get_bounce_handler()
    
    # Process bounces
    if event_type in ["bounced", "failed", "rejected", "complained"]:
        bounce_event = handler.parse_event(event_data)
        
        if bounce_event:
            background_tasks.add_task(
                bounce_handler.process_bounce,
                bounce_event
            )
    
    # Process delivery
    elif event_type == "delivered":
        recipient = event_data.get("recipient")
        if recipient:
            background_tasks.add_task(
                update_delivery_status,
                recipient,
                "delivered",
                event_data
            )
    
    # Process opens
    elif event_type == "opened":
        recipient = event_data.get("recipient")
        message_data = event_data.get("message", {})
        campaign_id = message_data.get("headers", {}).get("X-Campaign-ID")
        if recipient:
            background_tasks.add_task(
                track_open_event,
                recipient,
                campaign_id,
                event_data
            )
    
    # Process clicks
    elif event_type == "clicked":
        recipient = event_data.get("recipient")
        url = event_data.get("url")
        message_data = event_data.get("message", {})
        campaign_id = message_data.get("headers", {}).get("X-Campaign-ID")
        if recipient and url:
            background_tasks.add_task(
                track_click_event,
                recipient,
                url,
                campaign_id,
                event_data
            )
    
    # Process unsubscribes
    elif event_type == "unsubscribed":
        recipient = event_data.get("recipient")
        if recipient:
            background_tasks.add_task(
                process_unsubscribe,
                recipient,
                "mailgun_webhook",
                event_data
            )
    
    return {"status": "processed"}


@router.post("/webhooks/ses")
async def ses_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
):
    """
    Receive AWS SES Webhooks via SNS
    
    Handles:
    - Bounce
    - Complaint
    - Delivery
    """
    body = await request.body()
    
    try:
        message = json.loads(body)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON")
    
    # Handle SNS subscription confirmation
    if message.get("Type") == "SubscriptionConfirmation":
        # In production, validate and confirm subscription
        subscribe_url = message.get("SubscribeURL")
        logger.info(f"SNS subscription confirmation URL: {subscribe_url}")
        return {"status": "subscription_confirmation_received"}
    
    # Handle notifications
    if message.get("Type") == "Notification":
        notification = json.loads(message.get("Message", "{}"))
        notification_type = notification.get("notificationType", "")
        
        handler = SESWebhookHandler()
        bounce_handler = get_bounce_handler()
        
        # Process bounces
        if notification_type == "Bounce":
            bounce_data = notification.get("bounce", {})
            bounced_recipients = bounce_data.get("bouncedRecipients", [])
            
            for recipient in bounced_recipients:
                event_data = {
                    **notification,
                    "recipient": recipient,
                }
                bounce_event = handler.parse_event(event_data)
                
                if bounce_event:
                    background_tasks.add_task(
                        bounce_handler.process_bounce,
                        bounce_event
                    )
        
        # Process complaints
        elif notification_type == "Complaint":
            complaint_data = notification.get("complaint", {})
            complained_recipients = complaint_data.get("complainedRecipients", [])
            
            for recipient in complained_recipients:
                email = recipient.get("emailAddress")
                if email:
                    background_tasks.add_task(
                        process_complaint,
                        email,
                        notification
                    )
        
        # Process deliveries
        elif notification_type == "Delivery":
            delivery_data = notification.get("delivery", {})
            recipients = delivery_data.get("recipients", [])
            
            for email in recipients:
                background_tasks.add_task(
                    update_delivery_status,
                    email,
                    "delivered",
                    notification
                )
    
    return {"status": "processed"}


# ==========================================
# Helper Functions
# ==========================================

async def update_delivery_status(
    email: str,
    status: str,
    event_data: dict
):
    """Update recipient delivery status in database"""
    from core.supabase import get_supabase
    
    try:
        supabase = await get_supabase()
        
        # Find the most recent pending recipient
        result = supabase.table("email_recipients").select("id, campaign_id").eq(
            "email", email
        ).eq(
            "status", "pending"
        ).order(
            "created_at", desc=True
        ).limit(1).execute()
        
        if result.data:
            recipient = result.data[0]
            
            supabase.table("email_recipients").update({
                "status": status,
                "updated_at": datetime.utcnow().isoformat(),
            }).eq("id", recipient["id"]).execute()
            
            logger.info(f"Updated delivery status for {email}: {status}")
    
    except Exception as e:
        logger.error(f"Error updating delivery status: {e}")


async def track_open_event(
    email: str,
    campaign_id: Optional[str],
    event_data: dict
):
    """Track email open event"""
    from core.supabase import get_supabase
    
    try:
        supabase = await get_supabase()
        
        # Record the open
        supabase.table("email_opens").insert({
            "email": email,
            "campaign_id": campaign_id,
            "opened_at": datetime.utcnow().isoformat(),
            "user_agent": event_data.get("useragent", event_data.get("user-agent")),
            "ip_address": event_data.get("ip"),
        }).execute()
        
        logger.info(f"Tracked open for {email}")
    
    except Exception as e:
        logger.error(f"Error tracking open event: {e}")


async def track_click_event(
    email: str,
    url: str,
    campaign_id: Optional[str],
    event_data: dict
):
    """Track link click event"""
    from core.supabase import get_supabase
    
    try:
        supabase = await get_supabase()
        
        # Record the click
        supabase.table("email_clicks").insert({
            "email": email,
            "url": url,
            "campaign_id": campaign_id,
            "clicked_at": datetime.utcnow().isoformat(),
            "user_agent": event_data.get("useragent", event_data.get("user-agent")),
            "ip_address": event_data.get("ip"),
        }).execute()
        
        logger.info(f"Tracked click for {email}: {url}")
    
    except Exception as e:
        logger.error(f"Error tracking click event: {e}")


async def process_unsubscribe(
    email: str,
    source: str,
    event_data: dict
):
    """Process unsubscribe request"""
    from core.segmentation import get_segmentation_service, SuppressionListEntry
    
    try:
        service = get_segmentation_service()
        
        await service.add_to_suppression_list([
            SuppressionListEntry(
                email=email,
                source=source,
                reason="unsubscribe",
            )
        ])
        
        logger.info(f"Processed unsubscribe for {email}")
    
    except Exception as e:
        logger.error(f"Error processing unsubscribe: {e}")


async def process_complaint(
    email: str,
    notification: dict
):
    """Process spam complaint"""
    from core.segmentation import get_segmentation_service, SuppressionListEntry
    
    try:
        service = get_segmentation_service()
        
        await service.add_to_suppression_list([
            SuppressionListEntry(
                email=email,
                source="ses_complaint",
                reason="spam_complaint",
            )
        ])
        
        logger.info(f"Processed complaint for {email}")
    
    except Exception as e:
        logger.error(f"Error processing complaint: {e}")


# ==========================================
# Bounce Statistics Endpoints
# ==========================================

from core.dependencies import get_current_user
from fastapi import Depends

@router.get("/bounces/stats")
async def get_bounce_statistics(
    days: int = 30,
    _: str = Depends(get_current_user)
):
    """Get bounce statistics for the past N days"""
    from core.supabase import get_supabase
    from datetime import timedelta
    
    try:
        supabase = await get_supabase()
        
        # Calculate date range
        start_date = datetime.utcnow() - timedelta(days=days)
        
        # Get bounce events
        result = supabase.table("bounce_events").select("*").gte(
            "bounced_at", start_date.isoformat()
        ).execute()
        
        events = result.data if result.data else []
        
        # Calculate stats
        total_bounces = len(events)
        hard_bounces = len([e for e in events if e.get("bounce_type") == "hard"])
        soft_bounces = len([e for e in events if e.get("bounce_type") == "soft"])
        
        # By domain
        by_domain = {}
        for event in events:
            email = event.get("email", "")
            if "@" in email:
                domain = email.split("@")[1]
                by_domain[domain] = by_domain.get(domain, 0) + 1
        
        # By bounce type
        by_type = {}
        for event in events:
            bounce_type = event.get("bounce_type", "unknown")
            by_type[bounce_type] = by_type.get(bounce_type, 0) + 1
        
        return {
            "period_days": days,
            "total_bounces": total_bounces,
            "hard_bounces": hard_bounces,
            "soft_bounces": soft_bounces,
            "by_domain": dict(sorted(by_domain.items(), key=lambda x: x[1], reverse=True)[:10]),
            "by_type": by_type,
        }
    
    except Exception as e:
        logger.error(f"Error getting bounce statistics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/bounces/suppressed")
async def get_suppressed_from_bounces(
    limit: int = 100,
    _: str = Depends(get_current_user)
):
    """Get list of emails suppressed due to bounces"""
    from core.segmentation import get_segmentation_service
    
    service = get_segmentation_service()
    entries = await service.get_suppression_list(source="bounce", limit=limit, offset=0)
    
    return {"entries": entries, "count": len(entries)}


@router.post("/bounces/test")
async def test_bounce_handling(
    email: str,
    bounce_type: str = "hard",
    _: str = Depends(get_current_user)
):
    """
    Test bounce handling (development only)
    
    Simulates a bounce for testing purposes.
    """
    if not settings.DEBUG:
        raise HTTPException(
            status_code=403,
            detail="This endpoint is only available in debug mode"
        )
    
    from core.bounce_handler import BounceEvent, BounceType, BounceReason
    
    bounce_handler = get_bounce_handler()
    
    event = BounceEvent(
        email=email,
        bounce_type=BounceType.HARD if bounce_type == "hard" else BounceType.SOFT,
        reason=BounceReason.INVALID_EMAIL,
        provider_code="550",
        provider_message="Test bounce for development",
        campaign_id=None,
        recipient_id=None,
        timestamp=datetime.utcnow(),
        raw_data={"test": True},
    )
    
    await bounce_handler.process_bounce(event)
    
    return {"status": "processed", "bounce_type": bounce_type, "email": email}
