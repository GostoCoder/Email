"""
Bounce Handling Endpoints (SMTP-only)
"""

import logging
from datetime import datetime, timedelta

from fastapi import APIRouter, HTTPException, Depends

from core.config import settings
from core.bounce_handler import get_bounce_handler, BounceType, BounceReason, BounceEvent
from core.dependencies import get_current_user

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/bounces/stats")
async def get_bounce_statistics(
    days: int = 30,
    _: str = Depends(get_current_user)
):
    """Get bounce statistics for the past N days"""
    from core.supabase import get_supabase

    try:
        supabase = await get_supabase()

        start_date = datetime.utcnow() - timedelta(days=days)

        result = supabase.table("bounce_events").select("*").gte(
            "bounced_at", start_date.isoformat()
        ).execute()

        events = result.data if result.data else []

        total_bounces = len(events)
        hard_bounces = len([e for e in events if e.get("bounce_type") == "hard"])
        soft_bounces = len([e for e in events if e.get("bounce_type") == "soft"])

        by_domain = {}
        for event in events:
            email = event.get("email", "")
            if "@" in email:
                domain = email.split("@")[1]
                by_domain[domain] = by_domain.get(domain, 0) + 1

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
    """
    if not settings.DEBUG:
        raise HTTPException(
            status_code=403,
            detail="This endpoint is only available in debug mode"
        )

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
