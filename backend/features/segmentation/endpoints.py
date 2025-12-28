"""
Segmentation Endpoints

Endpoints for:
- Segment management
- Tag management
- Suppression list management
- Dynamic filtering
"""

from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query, HTTPException
from pydantic import BaseModel

from core.dependencies import get_current_user
from core.segmentation import (
    get_segmentation_service,
    SegmentCreate,
    SegmentResponse,
    SegmentFilter,
    FilterCondition,
    FilterOperator,
    FilterLogic,
    SegmentType,
    TagCreate,
    SuppressionListEntry,
)

router = APIRouter()


# ==========================================
# Segment Endpoints
# ==========================================

@router.post("/segments", response_model=SegmentResponse, status_code=201)
async def create_segment(
    segment: SegmentCreate,
    _: str = Depends(get_current_user)
):
    """
    Create a new recipient segment.
    
    Segment types:
    - static: Manually curated list of recipients
    - dynamic: Auto-updated based on filter rules
    
    Example dynamic segment:
    ```json
    {
        "name": "Active Gmail Users",
        "segment_type": "dynamic",
        "filters": {
            "logic": "and",
            "conditions": [
                {"field": "email", "operator": "ends_with", "value": "@gmail.com"},
                {"field": "status", "operator": "equals", "value": "sent"}
            ]
        }
    }
    ```
    """
    service = get_segmentation_service()
    return await service.create_segment(segment)


@router.get("/segments", response_model=List[SegmentResponse])
async def list_segments(
    segment_type: Optional[SegmentType] = None,
    tag: Optional[str] = None,
    _: str = Depends(get_current_user)
):
    """List all segments with optional filtering"""
    service = get_segmentation_service()
    return await service.list_segments(segment_type, tag)


@router.get("/segments/{segment_id}", response_model=SegmentResponse)
async def get_segment(
    segment_id: UUID,
    _: str = Depends(get_current_user)
):
    """Get segment details"""
    service = get_segmentation_service()
    return await service.get_segment(segment_id)


@router.patch("/segments/{segment_id}", response_model=SegmentResponse)
async def update_segment(
    segment_id: UUID,
    updates: dict,
    _: str = Depends(get_current_user)
):
    """Update a segment"""
    service = get_segmentation_service()
    return await service.update_segment(segment_id, updates)


@router.delete("/segments/{segment_id}", status_code=204)
async def delete_segment(
    segment_id: UUID,
    _: str = Depends(get_current_user)
):
    """Delete a segment"""
    service = get_segmentation_service()
    await service.delete_segment(segment_id)


@router.post("/segments/{segment_id}/refresh")
async def refresh_segment_count(
    segment_id: UUID,
    _: str = Depends(get_current_user)
):
    """Refresh recipient count for a dynamic segment"""
    service = get_segmentation_service()
    count = await service.refresh_segment_count(segment_id)
    return {"segment_id": str(segment_id), "recipient_count": count}


@router.get("/segments/{segment_id}/recipients")
async def get_segment_recipients(
    segment_id: UUID,
    limit: int = Query(default=100, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
    _: str = Depends(get_current_user)
):
    """Get recipients in a segment"""
    service = get_segmentation_service()
    segment = await service.get_segment(segment_id)
    
    if not segment.filters:
        return {"recipients": [], "total": 0}
    
    recipients = await service.get_matching_recipients(
        segment.filters,
        limit=limit,
        offset=offset
    )
    
    return {
        "recipients": recipients,
        "total": segment.recipient_count,
        "limit": limit,
        "offset": offset,
    }


# ==========================================
# Tag Endpoints
# ==========================================

@router.post("/tags", status_code=201)
async def create_tag(
    tag: TagCreate,
    _: str = Depends(get_current_user)
):
    """Create a new tag"""
    service = get_segmentation_service()
    return await service.create_tag(tag)


@router.get("/tags")
async def list_tags(
    _: str = Depends(get_current_user)
):
    """List all tags with usage counts"""
    service = get_segmentation_service()
    return await service.list_tags()


class TagAssignmentRequest(BaseModel):
    recipient_ids: List[UUID]
    tags: List[str]


@router.post("/tags/assign")
async def assign_tags_to_recipients(
    request: TagAssignmentRequest,
    _: str = Depends(get_current_user)
):
    """Add tags to multiple recipients"""
    service = get_segmentation_service()
    count = await service.add_tags_to_recipients(request.recipient_ids, request.tags)
    return {"updated": count}


@router.post("/tags/remove")
async def remove_tags_from_recipients(
    request: TagAssignmentRequest,
    _: str = Depends(get_current_user)
):
    """Remove tags from multiple recipients"""
    service = get_segmentation_service()
    count = await service.remove_tags_from_recipients(request.recipient_ids, request.tags)
    return {"updated": count}


@router.get("/tags/{tag}/recipients")
async def get_recipients_by_tag(
    tag: str,
    campaign_id: Optional[UUID] = None,
    limit: int = Query(default=100, ge=1, le=1000),
    _: str = Depends(get_current_user)
):
    """Get all recipients with a specific tag"""
    service = get_segmentation_service()
    recipients = await service.get_recipients_by_tag(tag, campaign_id, limit)
    return {"recipients": recipients, "count": len(recipients)}


# ==========================================
# Suppression List Endpoints
# ==========================================

class SuppressionAddRequest(BaseModel):
    entries: List[SuppressionListEntry]


@router.post("/suppression")
async def add_to_suppression_list(
    request: SuppressionAddRequest,
    _: str = Depends(get_current_user)
):
    """
    Add emails to the global suppression list.
    
    Suppressed emails will not receive any future campaigns.
    """
    service = get_segmentation_service()
    result = await service.add_to_suppression_list(request.entries)
    return result


@router.delete("/suppression/{email}")
async def remove_from_suppression_list(
    email: str,
    _: str = Depends(get_current_user)
):
    """Remove an email from the suppression list"""
    service = get_segmentation_service()
    removed = await service.remove_from_suppression_list(email)
    
    if not removed:
        raise HTTPException(status_code=404, detail="Email not found in suppression list")
    
    return {"removed": email}


@router.get("/suppression/check/{email}")
async def check_if_suppressed(
    email: str,
    _: str = Depends(get_current_user)
):
    """Check if an email is in the suppression list"""
    service = get_segmentation_service()
    is_suppressed = await service.is_suppressed(email)
    return {"email": email, "is_suppressed": is_suppressed}


class FilterEmailsRequest(BaseModel):
    emails: List[str]


@router.post("/suppression/filter")
async def filter_suppressed_emails(
    request: FilterEmailsRequest,
    _: str = Depends(get_current_user)
):
    """
    Filter a list of emails, removing suppressed ones.
    
    Useful before importing recipients.
    """
    service = get_segmentation_service()
    allowed = await service.filter_suppressed(request.emails)
    
    return {
        "original_count": len(request.emails),
        "allowed_count": len(allowed),
        "suppressed_count": len(request.emails) - len(allowed),
        "allowed_emails": allowed,
    }


@router.get("/suppression")
async def list_suppression_entries(
    source: Optional[str] = None,
    limit: int = Query(default=100, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
    _: str = Depends(get_current_user)
):
    """List suppression list entries"""
    service = get_segmentation_service()
    entries = await service.get_suppression_list(source, limit, offset)
    return {"entries": entries, "count": len(entries)}


@router.get("/suppression/stats")
async def get_suppression_stats(
    _: str = Depends(get_current_user)
):
    """Get suppression list statistics"""
    service = get_segmentation_service()
    return await service.get_suppression_stats()
