"""
Celery Configuration and Tasks

Provides:
- Celery app configuration
- Task definitions for email campaigns
- Retry logic with exponential backoff
- Task monitoring and logging
"""

import os
import logging
from datetime import timedelta
from typing import Optional, List
from uuid import UUID

from celery import Celery, Task
from celery.signals import task_prerun, task_postrun, task_failure

from core.config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)


# Celery configuration
def get_celery_config():
    """Get Celery configuration based on environment"""
    broker_url = settings.celery_broker_url or settings.redis_url or "redis://localhost:6379/0"
    result_backend = settings.celery_result_backend or settings.redis_url or "redis://localhost:6379/0"
    
    return {
        "broker_url": broker_url,
        "result_backend": result_backend,
        "task_serializer": "json",
        "accept_content": ["json"],
        "result_serializer": "json",
        "timezone": "UTC",
        "enable_utc": True,
        
        # Task execution settings
        "task_acks_late": True,  # Acknowledge after task completion
        "task_reject_on_worker_lost": True,  # Re-queue if worker dies
        "worker_prefetch_multiplier": 1,  # Fair task distribution
        
        # Result backend settings
        "result_expires": 3600,  # 1 hour
        
        # Retry settings
        "task_default_retry_delay": 60,  # 1 minute
        "task_max_retries": 3,
        
        # Concurrency
        "worker_concurrency": 4,
        
        # Task routes
        "task_routes": {
            "tasks.send_campaign_email": {"queue": "emails"},
            "tasks.process_campaign_batch": {"queue": "campaigns"},
            "tasks.send_webhook_notification": {"queue": "webhooks"},
        },
        
        # Rate limiting
        "task_annotations": {
            "tasks.send_campaign_email": {
                "rate_limit": "10/s"  # 10 emails per second per worker
            }
        },
        
        # Beat schedule for periodic tasks
        "beat_schedule": {
            "process-scheduled-campaigns": {
                "task": "tasks.process_scheduled_campaigns",
                "schedule": timedelta(minutes=1),
            },
            "cleanup-old-logs": {
                "task": "tasks.cleanup_old_logs",
                "schedule": timedelta(hours=24),
            },
            "update-campaign-stats": {
                "task": "tasks.update_campaign_stats",
                "schedule": timedelta(minutes=5),
            },
        },
    }


# Create Celery app
celery_app = Celery("email_campaigns")
celery_app.config_from_object(get_celery_config())


class BaseTask(Task):
    """Base task with common functionality"""
    
    abstract = True
    max_retries = 3
    
    def on_success(self, retval, task_id, args, kwargs):
        logger.info(f"Task {self.name}[{task_id}] completed successfully")
    
    def on_failure(self, exc, task_id, args, kwargs, einfo):
        logger.error(f"Task {self.name}[{task_id}] failed: {exc}")
    
    def on_retry(self, exc, task_id, args, kwargs, einfo):
        logger.warning(f"Task {self.name}[{task_id}] retrying: {exc}")


# Task signals for monitoring
@task_prerun.connect
def task_prerun_handler(sender=None, task_id=None, task=None, args=None, kwargs=None, **other):
    """Log task start"""
    logger.debug(f"Starting task {sender.name}[{task_id}]")


@task_postrun.connect
def task_postrun_handler(sender=None, task_id=None, task=None, args=None, kwargs=None, retval=None, state=None, **other):
    """Log task completion"""
    logger.debug(f"Completed task {sender.name}[{task_id}] with state {state}")


@task_failure.connect
def task_failure_handler(sender=None, task_id=None, exception=None, args=None, kwargs=None, traceback=None, einfo=None, **other):
    """Handle task failures"""
    logger.error(f"Task {sender.name}[{task_id}] failed with exception: {exception}")


# ============================================
# Email Campaign Tasks
# ============================================

@celery_app.task(base=BaseTask, bind=True, name="tasks.send_campaign_email")
def send_campaign_email(
    self,
    campaign_id: str,
    recipient_id: str,
    email: str,
    subject: str,
    html_content: str,
    from_email: str,
    from_name: str,
    reply_to: Optional[str] = None,
    headers: Optional[dict] = None
):
    """
    Send a single campaign email with retry support.
    
    This task handles individual email sending with:
    - Automatic retries for transient failures
    - Exponential backoff
    - Dead letter queue for permanent failures
    """
    from core.email_service import get_email_service, EmailMessage
    from core.supabase import get_supabase_client
    
    try:
        logger.info(f"Sending email to {email} for campaign {campaign_id}")
        
        email_service = get_email_service()
        supabase = get_supabase_client()
        
        # Create email message
        message = EmailMessage(
            to_email=email,
            subject=subject,
            html_content=html_content,
            from_email=from_email,
            from_name=from_name,
            reply_to=reply_to,
            headers=headers or {}
        )
        
        # Send email
        result = email_service.send(message)
        
        if result.success:
            # Update recipient status
            supabase.table("recipients").update({
                "status": "sent",
                "sent_at": "now()"
            }).eq("id", recipient_id).execute()
            
            # Increment campaign sent count
            supabase.rpc("increment_campaign_sent", {"p_campaign_id": campaign_id}).execute()
            
            logger.info(f"Successfully sent email to {email}")
            return {"success": True, "recipient_id": recipient_id}
        else:
            raise Exception(result.error_message)
            
    except Exception as exc:
        error_message = str(exc)
        
        # Check if should retry
        if self._should_retry(error_message):
            # Exponential backoff: 1min, 2min, 4min, 8min
            countdown = 60 * (2 ** self.request.retries)
            logger.warning(f"Retrying email to {email} in {countdown}s: {error_message}")
            raise self.retry(exc=exc, countdown=countdown)
        else:
            # Permanent failure
            logger.error(f"Permanent failure for {email}: {error_message}")
            self._mark_failed(recipient_id, campaign_id, error_message)
            return {"success": False, "recipient_id": recipient_id, "error": error_message}
    
    def _should_retry(self, error_message: str) -> bool:
        """Determine if error is transient and worth retrying"""
        error_lower = error_message.lower()
        permanent_errors = [
            "invalid email", "domain not found", "user not found",
            "mailbox not found", "address rejected", "permanent failure"
        ]
        return not any(err in error_lower for err in permanent_errors)
    
    def _mark_failed(self, recipient_id: str, campaign_id: str, error: str):
        """Mark recipient as failed and update campaign stats"""
        from core.supabase import get_supabase_client
        supabase = get_supabase_client()
        
        supabase.table("recipients").update({
            "status": "failed",
            "error_message": error[:500]
        }).eq("id", recipient_id).execute()
        
        supabase.rpc("increment_campaign_failed", {"p_campaign_id": campaign_id}).execute()


@celery_app.task(base=BaseTask, bind=True, name="tasks.process_campaign_batch")
def process_campaign_batch(
    self,
    campaign_id: str,
    batch_number: int,
    batch_size: int = 100
):
    """
    Process a batch of campaign recipients.
    
    Fetches pending recipients and queues individual email tasks.
    """
    from core.supabase import get_supabase_client
    from core.template_service import get_template_service
    from core.tracking import inject_tracking_into_html
    
    try:
        supabase = get_supabase_client()
        template_service = get_template_service()
        
        # Get campaign
        campaign = supabase.table("campaigns").select("*").eq("id", campaign_id).single().execute()
        if not campaign.data:
            raise ValueError(f"Campaign {campaign_id} not found")
        
        campaign_data = campaign.data
        
        # Get batch of pending recipients
        offset = batch_number * batch_size
        recipients = supabase.table("recipients").select("*").eq(
            "campaign_id", campaign_id
        ).eq("status", "pending").range(offset, offset + batch_size - 1).execute()
        
        if not recipients.data:
            logger.info(f"No more recipients for campaign {campaign_id}")
            return {"processed": 0, "batch": batch_number}
        
        # Queue individual email tasks
        queued = 0
        for recipient in recipients.data:
            # Render template
            recipient_data = {
                "firstname": recipient.get("first_name", ""),
                "lastname": recipient.get("last_name", ""),
                "company": recipient.get("company", ""),
                **(recipient.get("custom_data", {}))
            }
            
            html_content = template_service.render(
                campaign_data["html_content"],
                recipient_data
            )
            
            # Inject tracking
            html_content = inject_tracking_into_html(
                html_content=html_content,
                campaign_id=UUID(campaign_id),
                recipient_id=UUID(recipient["id"]),
                enable_click_tracking=True,
                enable_open_tracking=True
            )
            
            # Queue email task
            send_campaign_email.delay(
                campaign_id=campaign_id,
                recipient_id=recipient["id"],
                email=recipient["email"],
                subject=campaign_data["subject"],
                html_content=html_content,
                from_email=campaign_data["from_email"],
                from_name=campaign_data["from_name"],
                reply_to=campaign_data.get("reply_to")
            )
            
            queued += 1
        
        logger.info(f"Queued {queued} emails for campaign {campaign_id} batch {batch_number}")
        
        # Queue next batch if there are more recipients
        if len(recipients.data) == batch_size:
            process_campaign_batch.delay(
                campaign_id=campaign_id,
                batch_number=batch_number + 1,
                batch_size=batch_size
            )
        
        return {"processed": queued, "batch": batch_number}
        
    except Exception as exc:
        logger.error(f"Error processing batch {batch_number} for campaign {campaign_id}: {exc}")
        raise self.retry(exc=exc, countdown=60)


@celery_app.task(base=BaseTask, name="tasks.start_campaign")
def start_campaign(campaign_id: str):
    """
    Start sending a campaign.
    
    Updates campaign status and queues the first batch.
    """
    from core.supabase import get_supabase_client
    from datetime import datetime
    
    supabase = get_supabase_client()
    
    # Update campaign status
    supabase.table("campaigns").update({
        "status": "sending",
        "started_at": datetime.utcnow().isoformat()
    }).eq("id", campaign_id).execute()
    
    # Get campaign batch size
    campaign = supabase.table("campaigns").select("batch_size").eq("id", campaign_id).single().execute()
    batch_size = campaign.data.get("batch_size", 100) if campaign.data else 100
    
    # Start processing
    process_campaign_batch.delay(
        campaign_id=campaign_id,
        batch_number=0,
        batch_size=batch_size
    )
    
    logger.info(f"Started campaign {campaign_id}")
    return {"campaign_id": campaign_id, "status": "sending"}


@celery_app.task(base=BaseTask, name="tasks.process_scheduled_campaigns")
def process_scheduled_campaigns():
    """
    Check for campaigns scheduled to send and start them.
    Runs every minute via Celery Beat.
    """
    from core.supabase import get_supabase_client
    from datetime import datetime
    
    supabase = get_supabase_client()
    now = datetime.utcnow().isoformat()
    
    # Find scheduled campaigns that are due
    campaigns = supabase.table("campaigns").select("id").eq(
        "status", "scheduled"
    ).lte("scheduled_at", now).execute()
    
    started = 0
    for campaign in campaigns.data or []:
        start_campaign.delay(campaign["id"])
        started += 1
    
    if started > 0:
        logger.info(f"Started {started} scheduled campaigns")
    
    return {"started": started}


@celery_app.task(base=BaseTask, name="tasks.send_webhook_notification")
def send_webhook_notification(
    webhook_url: str,
    event_type: str,
    payload: dict,
    secret: Optional[str] = None
):
    """
    Send a webhook notification.
    
    Includes HMAC signature if secret is provided.
    """
    import httpx
    import hmac
    import hashlib
    import json
    
    try:
        headers = {
            "Content-Type": "application/json",
            "X-Webhook-Event": event_type
        }
        
        body = json.dumps(payload)
        
        if secret:
            signature = hmac.new(
                secret.encode(),
                body.encode(),
                hashlib.sha256
            ).hexdigest()
            headers["X-Webhook-Signature"] = f"sha256={signature}"
        
        with httpx.Client(timeout=30.0) as client:
            response = client.post(webhook_url, content=body, headers=headers)
            response.raise_for_status()
        
        logger.info(f"Webhook sent successfully to {webhook_url}")
        return {"success": True, "status_code": response.status_code}
        
    except Exception as exc:
        logger.error(f"Webhook failed to {webhook_url}: {exc}")
        raise


@celery_app.task(base=BaseTask, name="tasks.cleanup_old_logs")
def cleanup_old_logs(days: int = 90):
    """
    Clean up old email logs.
    Runs daily via Celery Beat.
    """
    from core.supabase import get_supabase_client
    from datetime import datetime, timedelta
    
    supabase = get_supabase_client()
    cutoff = (datetime.utcnow() - timedelta(days=days)).isoformat()
    
    result = supabase.table("email_logs").delete().lt("timestamp", cutoff).execute()
    
    deleted = len(result.data) if result.data else 0
    logger.info(f"Cleaned up {deleted} old log entries")
    
    return {"deleted": deleted}


@celery_app.task(base=BaseTask, name="tasks.update_campaign_stats")
def update_campaign_stats():
    """
    Update campaign statistics from email logs.
    Runs every 5 minutes via Celery Beat.
    """
    from core.supabase import get_supabase_client
    
    supabase = get_supabase_client()
    
    # Get active campaigns
    campaigns = supabase.table("campaigns").select("id").eq("status", "sending").execute()
    
    for campaign in campaigns.data or []:
        campaign_id = campaign["id"]
        
        # Count recipients by status
        stats = supabase.rpc("get_campaign_recipient_stats", {
            "p_campaign_id": campaign_id
        }).execute()
        
        if stats.data:
            supabase.table("campaigns").update({
                "sent_count": stats.data.get("sent", 0),
                "failed_count": stats.data.get("failed", 0),
                "opened_count": stats.data.get("opened", 0),
                "clicked_count": stats.data.get("clicked", 0),
            }).eq("id", campaign_id).execute()
    
    return {"updated": len(campaigns.data or [])}
