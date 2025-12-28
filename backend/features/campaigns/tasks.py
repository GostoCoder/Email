"""
Background tasks for campaign sending
"""

import asyncio
import logging
import re
from datetime import datetime, timedelta
from typing import List, Optional
from uuid import UUID

from core.config import get_settings
from core.supabase import get_supabase_client
from core.email_service import get_email_service, EmailMessage
from core.template_service import get_template_service
from core.tracking import inject_tracking_into_html
from core.webhooks import get_webhook_service, get_campaign_webhooks

settings = get_settings()
logger = logging.getLogger(__name__)


def should_retry_email(error_message: str, retry_count: int, max_retries: int) -> bool:
    """
    Determine if an email should be retried based on the error type.
    
    Permanent errors (hard bounces) should not be retried:
    - Invalid email address
    - Domain doesn't exist
    - Mailbox doesn't exist
    
    Temporary errors (soft bounces) can be retried:
    - Mailbox full
    - Server temporarily unavailable
    - Rate limiting
    - Connection timeout
    """
    if retry_count >= max_retries:
        return False
    
    error_lower = error_message.lower()
    
    # Permanent errors - do not retry
    permanent_errors = [
        "invalid email",
        "email address is invalid",
        "domain not found",
        "domain does not exist",
        "user not found",
        "mailbox not found",
        "recipient address rejected",
        "address rejected",
        "does not exist",
        "undeliverable",
        "permanent failure",
    ]
    
    for permanent_error in permanent_errors:
        if permanent_error in error_lower:
            logger.info(f"Permanent error detected, not retrying: {error_message}")
            return False
    
    # Temporary errors - can retry
    temporary_errors = [
        "timeout",
        "temporary",
        "try again",
        "rate limit",
        "mailbox full",
        "quota exceeded",
        "service unavailable",
        "connection",
        "network",
    ]
    
    for temp_error in temporary_errors:
        if temp_error in error_lower:
            logger.info(f"Temporary error detected, will retry: {error_message}")
            return True
    
    # Default: retry unknown errors
    return True


async def process_campaign_send(
    campaign_id: UUID,
    test_mode: bool = False,
    test_emails: Optional[List[str]] = None
):
    """
    Process campaign email sending in batches
    
    This function runs in the background and sends emails to all recipients
    """
    supabase = get_supabase_client()
    email_service = get_email_service()
    template_service = get_template_service()
    webhook_service = get_webhook_service()
    
    try:
        logger.info(f"Starting campaign send: {campaign_id}, test_mode={test_mode}")
        
        # Get campaign details
        campaign_result = supabase.table("campaigns").select("*").eq("id", str(campaign_id)).execute()
        
        if not campaign_result.data:
            logger.error(f"Campaign {campaign_id} not found")
            return
        
        campaign = campaign_result.data[0]
        
        # Get webhook configuration
        webhook_config = await get_campaign_webhooks(campaign_id)
        
        # Get pending recipients
        if test_mode and test_emails:
            # In test mode, only send to specified test emails
            recipients_result = (
                supabase.table("recipients")
                .select("*")
                .eq("campaign_id", str(campaign_id))
                .in_("email", test_emails)
                .execute()
            )
        else:
            # Normal mode: send to all pending recipients
            recipients_result = (
                supabase.table("recipients")
                .select("*")
                .eq("campaign_id", str(campaign_id))
                .eq("status", "pending")
                .execute()
            )
        
        recipients = recipients_result.data
        
        if not recipients:
            logger.warning(f"No recipients to send for campaign {campaign_id}")
            supabase.table("campaigns").update({
                "status": "completed",
                "completed_at": datetime.utcnow().isoformat()
            }).eq("id", str(campaign_id)).execute()
            return
        
        logger.info(f"Sending to {len(recipients)} recipients")
        
        # Build unsubscribe headers
        base_url = settings.app_base_url
        
        # Prepare messages
        messages = []
        for recipient in recipients:
            unsubscribe_url = f"{base_url}/unsubscribe?email={recipient['email']}&campaign_id={campaign_id}"
            
            # Render email content with recipient data
            recipient_data = {
                "firstname": recipient.get("first_name", ""),
                "lastname": recipient.get("last_name", ""),
                "company": recipient.get("company", ""),
                "subject": campaign["subject"],
                "unsubscribe_url": unsubscribe_url,
                **(recipient.get("custom_data", {}))
            }
            
            try:
                html_content = template_service.render(campaign["html_content"], recipient_data)
                
                # Inject tracking pixels and links
                html_content = inject_tracking_into_html(
                    html_content=html_content,
                    campaign_id=campaign_id,
                    recipient_id=UUID(recipient["id"]),
                    enable_click_tracking=True,
                    enable_open_tracking=True
                )
            except Exception as e:
                logger.error(f"Failed to render template for {recipient['email']}: {str(e)}")
                # Mark as failed
                await log_email_event(
                    campaign_id=campaign_id,
                    recipient_id=UUID(recipient["id"]),
                    email=recipient["email"],
                    event_type="failed",
                    error_message=f"Template rendering failed: {str(e)}"
                )
                continue
            
            # Build unsubscribe headers
            unsubscribe_headers = email_service.build_unsubscribe_headers(
                unsubscribe_url=unsubscribe_url,
                campaign_email=campaign["from_email"]
            )
            
            message = EmailMessage(
                to_email=recipient["email"],
                subject=campaign["subject"],
                html_content=html_content,
                from_email=campaign["from_email"],
                from_name=campaign["from_name"],
                reply_to=campaign.get("reply_to"),
                custom_args={
                    "campaign_id": str(campaign_id),
                    "recipient_id": recipient["id"]
                },
                headers=unsubscribe_headers
            )
            
            messages.append((message, recipient))
        
        # Send emails in batches with progress tracking
        sent_count = 0
        failed_count = 0
        
        async def on_progress(current, total):
            nonlocal sent_count
            sent_count = current
            
            # Update campaign progress in database
            supabase.table("campaigns").update({
                "sent_count": sent_count,
                "failed_count": failed_count
            }).eq("id", str(campaign_id)).execute()
            
            logger.info(f"Campaign {campaign_id}: {sent_count}/{total} sent")
        
        # Send messages
        batch_messages = [msg for msg, _ in messages]
        results = await email_service.send_batch(batch_messages, on_progress=on_progress)
        
        # Process results and log events with retry logic
        for idx, result in enumerate(results):
            message, recipient = messages[idx]
            recipient_id = UUID(recipient["id"])
            
            if result["success"]:
                # Update recipient status
                supabase.table("recipients").update({
                    "status": "sent",
                    "sent_at": datetime.utcnow().isoformat()
                }).eq("id", str(recipient_id)).execute()
                
                # Log success
                await log_email_event(
                    campaign_id=campaign_id,
                    recipient_id=recipient_id,
                    email=recipient["email"],
                    event_type="sent",
                    provider_message_id=result.get("message_id")
                )
                
                # Send webhook notification
                if webhook_config:
                    await webhook_service.notify_email_sent(
                        campaign_id=campaign_id,
                        recipient_id=recipient_id,
                        email=recipient["email"],
                        webhook_config=webhook_config
                    )
            else:
                failed_count += 1
                retry_count = recipient["retry_count"] + 1
                max_retries = settings.email_max_retry_attempts
                
                # Determine if should retry based on error type
                error_msg = result.get("error", "Unknown error")
                should_retry = should_retry_email(error_msg, retry_count, max_retries)
                
                if should_retry:
                    # Calculate backoff delay: 2^retry_count minutes (1, 2, 4, 8...)
                    backoff_minutes = 2 ** (retry_count - 1)
                    
                    # Update recipient to pending for retry
                    supabase.table("recipients").update({
                        "status": "pending",
                        "error_message": f"Retry {retry_count}/{max_retries}: {error_msg}",
                        "retry_count": retry_count,
                        "metadata": {
                            **recipient.get("metadata", {}),
                            "retry_scheduled_at": (datetime.utcnow() + 
                                timedelta(minutes=backoff_minutes)).isoformat()
                        }
                    }).eq("id", str(recipient_id)).execute()
                    
                    logger.info(f"Scheduled retry {retry_count}/{max_retries} for {recipient['email']} "
                               f"in {backoff_minutes} minutes")
                else:
                    # Permanent failure
                    supabase.table("recipients").update({
                        "status": "failed",
                        "error_message": error_msg,
                        "retry_count": retry_count
                    }).eq("id", str(recipient_id)).execute()
                    
                    logger.warning(f"Permanent failure for {recipient['email']}: {error_msg}")
                
                # Log failure event
                await log_email_event(
                    campaign_id=campaign_id,
                    recipient_id=recipient_id,
                    email=recipient["email"],
                    event_type="failed",
                    error_message=error_msg
                )
                
                # Send webhook notification for permanent failures
                if not should_retry and webhook_config:
                    await webhook_service.notify_email_failed(
                        campaign_id=campaign_id,
                        recipient_id=recipient_id,
                        email=recipient["email"],
                        error=error_msg,
                        webhook_config=webhook_config
                    )
        
        # Send campaign completion webhook
        if webhook_config:
            campaign_stats = {
                "total_recipients": campaign["total_recipients"],
                "sent_count": sent_count,
                "failed_count": failed_count
            }
            await webhook_service.notify_campaign_completed(
                campaign_id=campaign_id,
                stats=campaign_stats,
                webhook_config=webhook_config
            )
        
        # Update final campaign status
        supabase.table("campaigns").update({
            "status": "completed",
            "completed_at": datetime.utcnow().isoformat(),
            "sent_count": sent_count,
            "failed_count": failed_count
        }).eq("id", str(campaign_id)).execute()
        
        logger.info(f"Campaign {campaign_id} completed: {sent_count} sent, {failed_count} failed")
        
    except Exception as e:
        logger.error(f"Campaign send failed for {campaign_id}: {str(e)}")
        
        # Mark campaign as failed
        supabase.table("campaigns").update({
            "status": "failed"
        }).eq("id", str(campaign_id)).execute()


async def log_email_event(
    campaign_id: UUID,
    recipient_id: UUID,
    email: str,
    event_type: str,
    provider_message_id: Optional[str] = None,
    error_message: Optional[str] = None,
    event_data: Optional[dict] = None
):
    """Log an email event to the database"""
    supabase = get_supabase_client()
    
    log_data = {
        "campaign_id": str(campaign_id),
        "recipient_id": str(recipient_id),
        "email": email,
        "event_type": event_type,
        "event_data": event_data or {},
        "provider_message_id": provider_message_id,
        "error_message": error_message
    }
    
    try:
        supabase.table("email_logs").insert(log_data).execute()
    except Exception as e:
        logger.error(f"Failed to log email event: {str(e)}")
