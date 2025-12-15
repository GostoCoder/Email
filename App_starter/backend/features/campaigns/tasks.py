"""
Background tasks for campaign sending
"""

import asyncio
import logging
from datetime import datetime
from typing import List, Optional
from uuid import UUID

from core.config import get_settings
from core.supabase import get_supabase_client
from core.email_service import get_email_service, EmailMessage
from core.template_service import get_template_service

settings = get_settings()
logger = logging.getLogger(__name__)


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
    
    try:
        logger.info(f"Starting campaign send: {campaign_id}, test_mode={test_mode}")
        
        # Get campaign details
        campaign_result = supabase.table("campaigns").select("*").eq("id", str(campaign_id)).execute()
        
        if not campaign_result.data:
            logger.error(f"Campaign {campaign_id} not found")
            return
        
        campaign = campaign_result.data[0]
        
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
        
        # Process results and log events
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
            else:
                failed_count += 1
                
                # Update recipient status
                supabase.table("recipients").update({
                    "status": "failed",
                    "error_message": result.get("error", "Unknown error"),
                    "retry_count": recipient["retry_count"] + 1
                }).eq("id", str(recipient_id)).execute()
                
                # Log failure
                await log_email_event(
                    campaign_id=campaign_id,
                    recipient_id=recipient_id,
                    email=recipient["email"],
                    event_type="failed",
                    error_message=result.get("error", "Unknown error")
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
