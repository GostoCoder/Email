"""
Advanced Segmentation Module

Provides:
- Dynamic recipient segmentation
- Tag management
- Global suppression lists
- Custom filters on recipient data
- Segment-based targeting
"""

import logging
import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass
from enum import Enum
from uuid import UUID, uuid4

from pydantic import BaseModel, Field

from core.supabase import get_supabase_client

logger = logging.getLogger(__name__)


class FilterOperator(str, Enum):
    EQUALS = "equals"
    NOT_EQUALS = "not_equals"
    CONTAINS = "contains"
    NOT_CONTAINS = "not_contains"
    STARTS_WITH = "starts_with"
    ENDS_WITH = "ends_with"
    GREATER_THAN = "greater_than"
    LESS_THAN = "less_than"
    IS_EMPTY = "is_empty"
    IS_NOT_EMPTY = "is_not_empty"
    IN_LIST = "in_list"
    NOT_IN_LIST = "not_in_list"
    REGEX = "regex"


class FilterLogic(str, Enum):
    AND = "and"
    OR = "or"


class SegmentType(str, Enum):
    STATIC = "static"  # Manually added recipients
    DYNAMIC = "dynamic"  # Filter-based, auto-updated


class FilterCondition(BaseModel):
    """Single filter condition"""
    field: str  # e.g., "email", "custom_data.industry", "engagement_score"
    operator: FilterOperator
    value: Optional[Union[str, int, float, List[str]]] = None


class SegmentFilter(BaseModel):
    """Complete segment filter definition"""
    logic: FilterLogic = FilterLogic.AND
    conditions: List[FilterCondition]


class SegmentCreate(BaseModel):
    """Schema for creating a segment"""
    name: str
    description: Optional[str] = None
    segment_type: SegmentType = SegmentType.DYNAMIC
    filters: Optional[SegmentFilter] = None
    tags: List[str] = Field(default_factory=list)


class SegmentResponse(BaseModel):
    """Schema for segment response"""
    id: UUID
    name: str
    description: Optional[str]
    segment_type: SegmentType
    filters: Optional[SegmentFilter]
    tags: List[str]
    recipient_count: int
    created_at: datetime
    updated_at: datetime


class TagCreate(BaseModel):
    """Schema for creating a tag"""
    name: str
    color: Optional[str] = "#3B82F6"  # Default blue
    description: Optional[str] = None


class SuppressionListEntry(BaseModel):
    """Schema for suppression list entry"""
    email: str
    reason: str
    source: str = "manual"  # manual, bounce, unsubscribe, complaint
    is_global: bool = True
    expires_at: Optional[datetime] = None


class SegmentationService:
    """Service for advanced recipient segmentation"""
    
    def __init__(self):
        self.supabase = get_supabase_client()
    
    # ==========================================
    # Segment Management
    # ==========================================
    
    async def create_segment(self, segment: SegmentCreate) -> SegmentResponse:
        """Create a new segment"""
        segment_id = str(uuid4())
        now = datetime.utcnow().isoformat()
        
        segment_data = {
            "id": segment_id,
            "name": segment.name,
            "description": segment.description,
            "segment_type": segment.segment_type.value,
            "filters": segment.filters.model_dump() if segment.filters else None,
            "tags": segment.tags,
            "recipient_count": 0,
            "created_at": now,
            "updated_at": now,
        }
        
        result = self.supabase.table("segments").insert(segment_data).execute()
        
        if not result.data:
            raise ValueError("Failed to create segment")
        
        # Calculate initial count for dynamic segments
        if segment.segment_type == SegmentType.DYNAMIC and segment.filters:
            count = await self.count_matching_recipients(segment.filters)
            self.supabase.table("segments").update({
                "recipient_count": count
            }).eq("id", segment_id).execute()
            result.data[0]["recipient_count"] = count
        
        logger.info(f"Created segment {segment_id}: {segment.name}")
        return SegmentResponse(**result.data[0])
    
    async def get_segment(self, segment_id: UUID) -> SegmentResponse:
        """Get a segment by ID"""
        result = self.supabase.table("segments").select("*").eq(
            "id", str(segment_id)
        ).single().execute()
        
        if not result.data:
            raise ValueError("Segment not found")
        
        return SegmentResponse(**result.data)
    
    async def list_segments(
        self,
        segment_type: Optional[SegmentType] = None,
        tag: Optional[str] = None
    ) -> List[SegmentResponse]:
        """List all segments with optional filtering"""
        query = self.supabase.table("segments").select("*")
        
        if segment_type:
            query = query.eq("segment_type", segment_type.value)
        
        if tag:
            query = query.contains("tags", [tag])
        
        result = query.order("created_at", desc=True).execute()
        
        return [SegmentResponse(**s) for s in result.data or []]
    
    async def update_segment(
        self,
        segment_id: UUID,
        updates: Dict[str, Any]
    ) -> SegmentResponse:
        """Update a segment"""
        updates["updated_at"] = datetime.utcnow().isoformat()
        
        result = self.supabase.table("segments").update(updates).eq(
            "id", str(segment_id)
        ).execute()
        
        if not result.data:
            raise ValueError("Segment not found")
        
        return SegmentResponse(**result.data[0])
    
    async def delete_segment(self, segment_id: UUID) -> None:
        """Delete a segment"""
        self.supabase.table("segments").delete().eq(
            "id", str(segment_id)
        ).execute()
        
        logger.info(f"Deleted segment {segment_id}")
    
    async def refresh_segment_count(self, segment_id: UUID) -> int:
        """Refresh recipient count for a dynamic segment"""
        segment = await self.get_segment(segment_id)
        
        if segment.segment_type != SegmentType.DYNAMIC:
            return segment.recipient_count
        
        if not segment.filters:
            return 0
        
        count = await self.count_matching_recipients(segment.filters)
        
        self.supabase.table("segments").update({
            "recipient_count": count,
            "updated_at": datetime.utcnow().isoformat(),
        }).eq("id", str(segment_id)).execute()
        
        return count
    
    # ==========================================
    # Dynamic Filtering
    # ==========================================
    
    async def count_matching_recipients(
        self,
        filters: SegmentFilter,
        campaign_id: Optional[UUID] = None
    ) -> int:
        """Count recipients matching filter conditions"""
        recipients = await self.get_matching_recipients(
            filters, campaign_id, count_only=True
        )
        return len(recipients)
    
    async def get_matching_recipients(
        self,
        filters: SegmentFilter,
        campaign_id: Optional[UUID] = None,
        limit: int = 1000,
        offset: int = 0,
        count_only: bool = False
    ) -> List[Dict[str, Any]]:
        """Get recipients matching filter conditions"""
        # Start with base query
        query = self.supabase.table("recipients").select(
            "id" if count_only else "*"
        )
        
        if campaign_id:
            query = query.eq("campaign_id", str(campaign_id))
        
        # Apply filters
        # Note: Complex filtering may require RPC function for full flexibility
        for condition in filters.conditions:
            query = self._apply_condition(query, condition)
        
        if not count_only:
            query = query.range(offset, offset + limit - 1)
        
        result = query.execute()
        return result.data or []
    
    def _apply_condition(self, query, condition: FilterCondition):
        """Apply a single filter condition to query"""
        field = condition.field
        op = condition.operator
        value = condition.value
        
        # Handle nested fields (custom_data.*)
        if field.startswith("custom_data."):
            json_path = field.replace("custom_data.", "")
            # Use Supabase JSON operators
            if op == FilterOperator.EQUALS:
                query = query.eq(f"custom_data->>{json_path}", value)
            elif op == FilterOperator.NOT_EQUALS:
                query = query.neq(f"custom_data->>{json_path}", value)
            elif op == FilterOperator.CONTAINS:
                query = query.ilike(f"custom_data->>{json_path}", f"%{value}%")
            return query
        
        # Standard field operations
        if op == FilterOperator.EQUALS:
            query = query.eq(field, value)
        elif op == FilterOperator.NOT_EQUALS:
            query = query.neq(field, value)
        elif op == FilterOperator.CONTAINS:
            query = query.ilike(field, f"%{value}%")
        elif op == FilterOperator.NOT_CONTAINS:
            query = query.not_.ilike(field, f"%{value}%")
        elif op == FilterOperator.STARTS_WITH:
            query = query.ilike(field, f"{value}%")
        elif op == FilterOperator.ENDS_WITH:
            query = query.ilike(field, f"%{value}")
        elif op == FilterOperator.GREATER_THAN:
            query = query.gt(field, value)
        elif op == FilterOperator.LESS_THAN:
            query = query.lt(field, value)
        elif op == FilterOperator.IS_EMPTY:
            query = query.is_(field, "null")
        elif op == FilterOperator.IS_NOT_EMPTY:
            query = query.not_.is_(field, "null")
        elif op == FilterOperator.IN_LIST:
            query = query.in_(field, value if isinstance(value, list) else [value])
        elif op == FilterOperator.NOT_IN_LIST:
            query = query.not_.in_(field, value if isinstance(value, list) else [value])
        
        return query
    
    # ==========================================
    # Tag Management
    # ==========================================
    
    async def create_tag(self, tag: TagCreate) -> Dict[str, Any]:
        """Create a new tag"""
        tag_data = {
            "id": str(uuid4()),
            "name": tag.name,
            "color": tag.color,
            "description": tag.description,
            "usage_count": 0,
            "created_at": datetime.utcnow().isoformat(),
        }
        
        result = self.supabase.table("tags").insert(tag_data).execute()
        
        if not result.data:
            raise ValueError("Failed to create tag")
        
        return result.data[0]
    
    async def list_tags(self) -> List[Dict[str, Any]]:
        """List all tags with usage counts"""
        result = self.supabase.table("tags").select("*").order(
            "usage_count", desc=True
        ).execute()
        
        return result.data or []
    
    async def add_tags_to_recipients(
        self,
        recipient_ids: List[UUID],
        tags: List[str]
    ) -> int:
        """Add tags to multiple recipients"""
        updated = 0
        
        for recipient_id in recipient_ids:
            # Get current tags
            result = self.supabase.table("recipients").select(
                "metadata"
            ).eq("id", str(recipient_id)).single().execute()
            
            if result.data:
                metadata = result.data.get("metadata", {})
                current_tags = set(metadata.get("tags", []))
                current_tags.update(tags)
                metadata["tags"] = list(current_tags)
                
                self.supabase.table("recipients").update({
                    "metadata": metadata
                }).eq("id", str(recipient_id)).execute()
                
                updated += 1
        
        # Update tag usage counts
        for tag in tags:
            self.supabase.rpc("increment_tag_usage", {"p_tag_name": tag}).execute()
        
        return updated
    
    async def remove_tags_from_recipients(
        self,
        recipient_ids: List[UUID],
        tags: List[str]
    ) -> int:
        """Remove tags from multiple recipients"""
        updated = 0
        
        for recipient_id in recipient_ids:
            result = self.supabase.table("recipients").select(
                "metadata"
            ).eq("id", str(recipient_id)).single().execute()
            
            if result.data:
                metadata = result.data.get("metadata", {})
                current_tags = set(metadata.get("tags", []))
                current_tags.difference_update(tags)
                metadata["tags"] = list(current_tags)
                
                self.supabase.table("recipients").update({
                    "metadata": metadata
                }).eq("id", str(recipient_id)).execute()
                
                updated += 1
        
        return updated
    
    async def get_recipients_by_tag(
        self,
        tag: str,
        campaign_id: Optional[UUID] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get recipients with a specific tag"""
        query = self.supabase.table("recipients").select("*")
        
        if campaign_id:
            query = query.eq("campaign_id", str(campaign_id))
        
        # Filter by tag in metadata
        query = query.contains("metadata", {"tags": [tag]})
        
        result = query.limit(limit).execute()
        return result.data or []
    
    # ==========================================
    # Suppression List Management
    # ==========================================
    
    async def add_to_suppression_list(
        self,
        entries: List[SuppressionListEntry]
    ) -> Dict[str, int]:
        """Add emails to suppression list"""
        added = 0
        duplicates = 0
        
        for entry in entries:
            try:
                data = {
                    "id": str(uuid4()),
                    "email": entry.email.lower(),
                    "reason": entry.reason,
                    "source": entry.source,
                    "is_global": entry.is_global,
                    "expires_at": entry.expires_at.isoformat() if entry.expires_at else None,
                    "created_at": datetime.utcnow().isoformat(),
                }
                
                self.supabase.table("suppression_list").insert(data).execute()
                added += 1
                
            except Exception as e:
                if "duplicate" in str(e).lower():
                    duplicates += 1
                else:
                    logger.error(f"Failed to add {entry.email} to suppression: {e}")
        
        logger.info(f"Added {added} to suppression list, {duplicates} duplicates")
        return {"added": added, "duplicates": duplicates}
    
    async def remove_from_suppression_list(self, email: str) -> bool:
        """Remove email from suppression list"""
        result = self.supabase.table("suppression_list").delete().eq(
            "email", email.lower()
        ).execute()
        
        return len(result.data or []) > 0
    
    async def is_suppressed(self, email: str) -> bool:
        """Check if email is in suppression list"""
        result = self.supabase.table("suppression_list").select("id").eq(
            "email", email.lower()
        ).eq("is_global", True).single().execute()
        
        if not result.data:
            return False
        
        # Check expiration
        entry = result.data
        if entry.get("expires_at"):
            expires = datetime.fromisoformat(entry["expires_at"])
            if datetime.utcnow() > expires:
                return False
        
        return True
    
    async def filter_suppressed(self, emails: List[str]) -> List[str]:
        """Filter out suppressed emails from a list"""
        emails_lower = [e.lower() for e in emails]
        
        result = self.supabase.table("suppression_list").select("email").in_(
            "email", emails_lower
        ).eq("is_global", True).execute()
        
        suppressed = {r["email"] for r in result.data or []}
        
        return [e for e in emails if e.lower() not in suppressed]
    
    async def get_suppression_list(
        self,
        source: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """Get suppression list entries"""
        query = self.supabase.table("suppression_list").select("*")
        
        if source:
            query = query.eq("source", source)
        
        result = query.order("created_at", desc=True).range(
            offset, offset + limit - 1
        ).execute()
        
        return result.data or []
    
    async def get_suppression_stats(self) -> Dict[str, Any]:
        """Get suppression list statistics"""
        result = self.supabase.table("suppression_list").select(
            "source, is_global"
        ).execute()
        
        stats = {
            "total": 0,
            "global": 0,
            "by_source": {}
        }
        
        for entry in result.data or []:
            stats["total"] += 1
            if entry["is_global"]:
                stats["global"] += 1
            source = entry["source"]
            stats["by_source"][source] = stats["by_source"].get(source, 0) + 1
        
        return stats


# Singleton instance
_segmentation_service: Optional[SegmentationService] = None


def get_segmentation_service() -> SegmentationService:
    """Get or create segmentation service instance"""
    global _segmentation_service
    if _segmentation_service is None:
        _segmentation_service = SegmentationService()
    return _segmentation_service
