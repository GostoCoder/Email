"""
A/B Testing Endpoints

Endpoints for:
- Creating A/B tests
- Assigning variants
- Getting test results
- Selecting winners
"""

from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from core.dependencies import get_current_user
from core.ab_testing import (
    get_ab_testing_service,
    ABTestCreate,
    ABTestResponse,
    ABTestStatus,
    VariantType,
)

router = APIRouter()


class ABTestCreateRequest(BaseModel):
    campaign_id: UUID
    name: str
    variant_type: VariantType
    variants: List[dict]
    traffic_split: Optional[List[float]] = None
    test_size_percent: float = 20
    winning_metric: str = "open_rate"
    auto_select_winner: bool = True
    min_sample_size: int = 100
    confidence_level: float = 0.95


class ABTestResultsResponse(BaseModel):
    test_id: UUID
    status: ABTestStatus
    variants: List[dict]
    winner: Optional[dict]
    confidence: float
    is_significant: bool


class SelectWinnerRequest(BaseModel):
    variant_id: Optional[str] = None


@router.post("/campaigns/{campaign_id}/ab-test", response_model=ABTestResponse, status_code=201)
async def create_ab_test(
    campaign_id: UUID,
    test_data: ABTestCreateRequest,
    _: str = Depends(get_current_user)
):
    """
    Create an A/B test for a campaign.
    
    Variants can test:
    - Subject lines
    - Email content
    - From names
    - Send times
    
    Example:
    ```json
    {
        "name": "Subject Line Test",
        "variant_type": "subject",
        "variants": [
            {"name": "Variant A", "subject": "Check out our new products!"},
            {"name": "Variant B", "subject": "You won't believe these deals"}
        ],
        "traffic_split": [50, 50],
        "winning_metric": "open_rate"
    }
    ```
    """
    if str(test_data.campaign_id) != str(campaign_id):
        raise HTTPException(
            status_code=400,
            detail="Campaign ID in URL must match campaign_id in body"
        )
    
    service = get_ab_testing_service()
    
    create_data = ABTestCreate(
        campaign_id=campaign_id,
        name=test_data.name,
        variant_type=test_data.variant_type,
        variants=test_data.variants,
        traffic_split=test_data.traffic_split,
        test_size_percent=test_data.test_size_percent,
        winning_metric=test_data.winning_metric,
        auto_select_winner=test_data.auto_select_winner,
        min_sample_size=test_data.min_sample_size,
        confidence_level=test_data.confidence_level,
    )
    
    return await service.create_test(create_data)


@router.get("/ab-tests/{test_id}", response_model=ABTestResponse)
async def get_ab_test(
    test_id: UUID,
    _: str = Depends(get_current_user)
):
    """Get A/B test details"""
    service = get_ab_testing_service()
    
    # Fetch from database
    from core.supabase import get_supabase_client
    supabase = get_supabase_client()
    
    result = supabase.table("ab_tests").select("*").eq("id", str(test_id)).single().execute()
    
    if not result.data:
        raise HTTPException(status_code=404, detail="A/B test not found")
    
    return ABTestResponse(**result.data)


@router.get("/ab-tests/{test_id}/results", response_model=ABTestResultsResponse)
async def get_ab_test_results(
    test_id: UUID,
    _: str = Depends(get_current_user)
):
    """
    Get current A/B test results.
    
    Returns:
    - Performance metrics for each variant
    - Statistical significance
    - Recommended winner (if significant)
    """
    service = get_ab_testing_service()
    result = await service.calculate_results(test_id)
    
    return ABTestResultsResponse(
        test_id=result.test_id,
        status=result.status,
        variants=[
            {
                "id": v.variant_id,
                "name": v.name,
                "recipients": v.recipients_count,
                "sent": v.sent_count,
                "opened": v.opened_count,
                "clicked": v.clicked_count,
                "open_rate": v.open_rate,
                "click_rate": v.click_rate,
            }
            for v in result.variants
        ],
        winner={
            "id": result.winner.variant_id,
            "name": result.winner.name,
            "open_rate": result.winner.open_rate,
            "click_rate": result.winner.click_rate,
        } if result.winner else None,
        confidence=result.confidence,
        is_significant=result.is_significant,
    )


@router.post("/ab-tests/{test_id}/select-winner")
async def select_ab_test_winner(
    test_id: UUID,
    request: SelectWinnerRequest,
    _: str = Depends(get_current_user)
):
    """
    Select a winner for the A/B test.
    
    If variant_id is provided, selects that variant manually.
    Otherwise, auto-selects based on statistical results.
    
    The winning variant's content is applied to the remaining campaign recipients.
    """
    service = get_ab_testing_service()
    return await service.select_winner(test_id, request.variant_id)


@router.get("/campaigns/{campaign_id}/ab-tests", response_model=List[ABTestResponse])
async def list_campaign_ab_tests(
    campaign_id: UUID,
    _: str = Depends(get_current_user)
):
    """List all A/B tests for a campaign"""
    from core.supabase import get_supabase_client
    supabase = get_supabase_client()
    
    result = supabase.table("ab_tests").select("*").eq(
        "campaign_id", str(campaign_id)
    ).order("created_at", desc=True).execute()
    
    return [ABTestResponse(**test) for test in result.data or []]
