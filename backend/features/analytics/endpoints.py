"""
Advanced Analytics Endpoints

Additional endpoints for:
- Domain statistics
- Engagement heatmaps
- Bounce analysis
- Trend analysis
- Recipient engagement scores
"""

from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query, HTTPException
from pydantic import BaseModel

from core.dependencies import get_current_user
from core.analytics import get_analytics_service

router = APIRouter()


class DomainStat(BaseModel):
    domain: str
    total_recipients: int
    sent_count: int
    open_rate: float
    click_rate: float
    bounce_rate: float
    fail_rate: float


class HeatmapResponse(BaseModel):
    heatmap: dict
    days: List[str]
    hours: List[int]
    peak_open_time: dict
    peak_click_time: dict
    total_opens: int
    total_clicks: int


class BounceAnalysis(BaseModel):
    total_bounces: int
    hard_bounces: int
    soft_bounces: int
    by_reason: dict
    by_domain: dict
    affected_domains: List[str]


class TrendData(BaseModel):
    campaigns: List[dict]
    summary: dict
    daily_volume: dict


class EngagementScore(BaseModel):
    email: str
    total_campaigns: int
    total_received: int
    total_opened: int
    total_clicked: int
    engagement_score: float
    engagement_level: str
    first_seen: Optional[str]
    last_engagement: Optional[str]


@router.get("/campaigns/{campaign_id}/analytics/domains", response_model=List[DomainStat])
async def get_domain_statistics(
    campaign_id: UUID,
    _: str = Depends(get_current_user)
):
    """
    Get email statistics grouped by recipient domain.
    
    Useful for:
    - Identifying problematic domains
    - Optimizing deliverability
    - Understanding audience composition
    """
    service = get_analytics_service()
    return await service.get_domain_stats(campaign_id)


@router.get("/campaigns/{campaign_id}/analytics/heatmap", response_model=HeatmapResponse)
async def get_engagement_heatmap(
    campaign_id: UUID,
    timezone: str = Query(default="UTC"),
    _: str = Depends(get_current_user)
):
    """
    Get engagement heatmap showing opens/clicks by hour and day of week.
    
    Useful for:
    - Determining optimal send times
    - Understanding recipient behavior patterns
    """
    service = get_analytics_service()
    return await service.get_engagement_heatmap(campaign_id, timezone)


@router.get("/campaigns/{campaign_id}/analytics/bounces", response_model=BounceAnalysis)
async def get_bounce_analysis(
    campaign_id: UUID,
    _: str = Depends(get_current_user)
):
    """
    Get detailed bounce analysis for a campaign.
    
    Returns:
    - Breakdown of hard vs soft bounces
    - Top bounce reasons
    - Most affected domains
    """
    service = get_analytics_service()
    return await service.get_bounce_analysis(campaign_id)


@router.get("/analytics/trends", response_model=TrendData)
async def get_campaign_trends(
    days: int = Query(default=30, ge=7, le=365),
    limit: int = Query(default=10, ge=1, le=50),
    _: str = Depends(get_current_user)
):
    """
    Get performance trends across multiple campaigns.
    
    Useful for:
    - Tracking overall email performance over time
    - Identifying performance changes
    - Benchmarking campaigns against each other
    """
    service = get_analytics_service()
    return await service.get_campaign_trends(days, limit)


@router.get("/analytics/engagement/{email}", response_model=EngagementScore)
async def get_recipient_engagement(
    email: str,
    _: str = Depends(get_current_user)
):
    """
    Get engagement score for a specific recipient.
    
    Returns:
    - Overall engagement score (0-100)
    - Engagement level (cold, warm, hot, superfan)
    - Historical interaction data
    """
    service = get_analytics_service()
    return await service.get_recipient_engagement_score(email)


@router.post("/analytics/compare")
async def compare_campaigns(
    campaign_ids: List[UUID],
    _: str = Depends(get_current_user)
):
    """
    Compare multiple campaigns side by side.
    
    Returns:
    - Comparative metrics for each campaign
    - Best performers for each metric
    """
    if len(campaign_ids) < 2:
        raise HTTPException(status_code=400, detail="At least 2 campaigns required")
    if len(campaign_ids) > 5:
        raise HTTPException(status_code=400, detail="Maximum 5 campaigns can be compared")
    
    service = get_analytics_service()
    return await service.get_comparative_analysis(campaign_ids)
