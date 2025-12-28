"""
Campaign Scheduler Service
Handles scheduled campaign sending using APScheduler
"""

import asyncio
import logging
from datetime import datetime, timezone
from typing import Optional

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.date import DateTrigger

from core.config import get_settings
from core.supabase import get_supabase_client

settings = get_settings()
logger = logging.getLogger(__name__)

# Global scheduler instance
_scheduler: Optional[AsyncIOScheduler] = None


def get_scheduler() -> AsyncIOScheduler:
    """Get or create scheduler singleton"""
    global _scheduler
    if _scheduler is None:
        _scheduler = AsyncIOScheduler()
        _scheduler.start()
        logger.info("Scheduler started")
        
        # Add job to check for scheduled campaigns every minute
        _scheduler.add_job(
            check_scheduled_campaigns,
            IntervalTrigger(seconds=60),
            id="check_scheduled_campaigns",
            replace_existing=True,
            name="Check for campaigns ready to send"
        )
        logger.info("Added scheduled campaigns check job (every 60s)")
    
    return _scheduler


async def check_scheduled_campaigns():
    """
    Check for campaigns that are scheduled to be sent and start them.
    This runs every minute.
    """
    from features.campaigns.tasks import process_campaign_send
    
    try:
        supabase = get_supabase_client()
        now = datetime.now(timezone.utc).isoformat()
        
        # Find campaigns that are scheduled and ready to send
        result = (
            supabase.table("campaigns")
            .select("*")
            .eq("status", "scheduled")
            .lte("scheduled_at", now)
            .execute()
        )
        
        if not result.data:
            return
        
        logger.info(f"Found {len(result.data)} scheduled campaigns ready to send")
        
        for campaign in result.data:
            campaign_id = campaign["id"]
            
            # Check if campaign has recipients
            if campaign["total_recipients"] == 0:
                logger.warning(f"Scheduled campaign {campaign_id} has no recipients, skipping")
                supabase.table("campaigns").update({
                    "status": "failed"
                }).eq("id", campaign_id).execute()
                continue
            
            logger.info(f"Starting scheduled campaign: {campaign_id}")
            
            # Update status to sending
            supabase.table("campaigns").update({
                "status": "sending",
                "started_at": now
            }).eq("id", campaign_id).execute()
            
            # Start the send task
            asyncio.create_task(
                process_campaign_send(
                    campaign_id=campaign_id,
                    test_mode=False,
                    test_emails=None
                )
            )
            
    except Exception as e:
        logger.error(f"Error checking scheduled campaigns: {str(e)}")


async def schedule_campaign(campaign_id: str, scheduled_at: datetime) -> bool:
    """
    Schedule a campaign to be sent at a specific time.
    
    Args:
        campaign_id: UUID of the campaign
        scheduled_at: When to send the campaign
        
    Returns:
        True if scheduled successfully
    """
    try:
        supabase = get_supabase_client()
        
        # Update campaign with scheduled status and time
        result = (
            supabase.table("campaigns")
            .update({
                "status": "scheduled",
                "scheduled_at": scheduled_at.isoformat()
            })
            .eq("id", campaign_id)
            .in_("status", ["draft", "paused"])
            .execute()
        )
        
        if not result.data:
            return False
        
        logger.info(f"Campaign {campaign_id} scheduled for {scheduled_at}")
        return True
        
    except Exception as e:
        logger.error(f"Error scheduling campaign {campaign_id}: {str(e)}")
        return False


async def cancel_scheduled_campaign(campaign_id: str) -> bool:
    """
    Cancel a scheduled campaign (revert to draft).
    
    Args:
        campaign_id: UUID of the campaign
        
    Returns:
        True if cancelled successfully
    """
    try:
        supabase = get_supabase_client()
        
        result = (
            supabase.table("campaigns")
            .update({
                "status": "draft",
                "scheduled_at": None
            })
            .eq("id", campaign_id)
            .eq("status", "scheduled")
            .execute()
        )
        
        if not result.data:
            return False
        
        logger.info(f"Cancelled scheduled campaign: {campaign_id}")
        return True
        
    except Exception as e:
        logger.error(f"Error cancelling scheduled campaign {campaign_id}: {str(e)}")
        return False


def shutdown_scheduler():
    """Shutdown the scheduler gracefully"""
    global _scheduler
    if _scheduler is not None:
        _scheduler.shutdown(wait=True)
        _scheduler = None
        logger.info("Scheduler shutdown complete")
