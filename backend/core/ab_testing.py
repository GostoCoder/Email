"""
A/B Testing Module

Provides:
- Campaign variant creation
- Traffic distribution
- Statistical significance testing
- Winner determination
- Auto-selection of winning variant
"""

import logging
import random
import math
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum
from uuid import UUID, uuid4

from pydantic import BaseModel, Field

from core.supabase import get_supabase_client

logger = logging.getLogger(__name__)


class ABTestStatus(str, Enum):
    DRAFT = "draft"
    RUNNING = "running"
    COMPLETED = "completed"
    WINNER_SELECTED = "winner_selected"


class VariantType(str, Enum):
    SUBJECT = "subject"
    CONTENT = "content"
    FROM_NAME = "from_name"
    SEND_TIME = "send_time"


class ABTestCreate(BaseModel):
    """Schema for creating an A/B test"""
    campaign_id: UUID
    name: str
    variant_type: VariantType
    variants: List[Dict[str, Any]] = Field(min_length=2, max_length=5)
    traffic_split: Optional[List[float]] = None  # e.g., [50, 50] or [33, 33, 34]
    test_size_percent: float = Field(default=20, ge=5, le=50)  # % of recipients for test
    winning_metric: str = Field(default="open_rate")  # open_rate, click_rate, conversion_rate
    auto_select_winner: bool = True
    min_sample_size: int = Field(default=100, ge=10)
    confidence_level: float = Field(default=0.95, ge=0.8, le=0.99)


class ABTestResponse(BaseModel):
    """Schema for A/B test response"""
    id: UUID
    campaign_id: UUID
    name: str
    status: ABTestStatus
    variant_type: VariantType
    variants: List[Dict[str, Any]]
    traffic_split: List[float]
    test_size_percent: float
    winning_metric: str
    winner_variant_id: Optional[str] = None
    created_at: datetime
    completed_at: Optional[datetime] = None


@dataclass
class VariantStats:
    """Statistics for a single variant"""
    variant_id: str
    name: str
    recipients_count: int
    sent_count: int
    opened_count: int
    clicked_count: int
    converted_count: int
    open_rate: float
    click_rate: float
    conversion_rate: float


@dataclass
class ABTestResult:
    """Complete A/B test results"""
    test_id: UUID
    status: ABTestStatus
    variants: List[VariantStats]
    winner: Optional[VariantStats]
    confidence: float
    is_significant: bool


class ABTestingService:
    """Service for A/B testing functionality"""
    
    def __init__(self):
        self.supabase = get_supabase_client()
    
    async def create_test(self, test_data: ABTestCreate) -> ABTestResponse:
        """
        Create a new A/B test for a campaign.
        """
        # Validate campaign exists and is in draft status
        campaign = self.supabase.table("campaigns").select(
            "id, status, total_recipients"
        ).eq("id", str(test_data.campaign_id)).single().execute()
        
        if not campaign.data:
            raise ValueError("Campaign not found")
        
        if campaign.data["status"] != "draft":
            raise ValueError("A/B tests can only be created for draft campaigns")
        
        # Calculate traffic split if not provided
        num_variants = len(test_data.variants)
        if not test_data.traffic_split:
            equal_split = 100 / num_variants
            traffic_split = [equal_split] * num_variants
        else:
            if len(test_data.traffic_split) != num_variants:
                raise ValueError("Traffic split must match number of variants")
            if abs(sum(test_data.traffic_split) - 100) > 0.01:
                raise ValueError("Traffic split must sum to 100")
            traffic_split = test_data.traffic_split
        
        # Assign IDs to variants
        variants = []
        for i, v in enumerate(test_data.variants):
            variants.append({
                "id": str(uuid4()),
                "name": v.get("name", f"Variant {chr(65 + i)}"),  # A, B, C, etc.
                "content": v.get("content", v),
                "traffic_percent": traffic_split[i],
            })
        
        # Create A/B test record
        test_record = {
            "id": str(uuid4()),
            "campaign_id": str(test_data.campaign_id),
            "name": test_data.name,
            "status": ABTestStatus.DRAFT.value,
            "variant_type": test_data.variant_type.value,
            "variants": variants,
            "traffic_split": traffic_split,
            "test_size_percent": test_data.test_size_percent,
            "winning_metric": test_data.winning_metric,
            "auto_select_winner": test_data.auto_select_winner,
            "min_sample_size": test_data.min_sample_size,
            "confidence_level": test_data.confidence_level,
            "created_at": datetime.utcnow().isoformat(),
        }
        
        result = self.supabase.table("ab_tests").insert(test_record).execute()
        
        if not result.data:
            raise ValueError("Failed to create A/B test")
        
        logger.info(f"Created A/B test {test_record['id']} for campaign {test_data.campaign_id}")
        
        return ABTestResponse(**result.data[0])
    
    async def assign_variant(self, test_id: UUID, recipient_id: UUID) -> str:
        """
        Assign a variant to a recipient based on traffic split.
        Returns variant ID.
        """
        test = self.supabase.table("ab_tests").select("*").eq(
            "id", str(test_id)
        ).single().execute()
        
        if not test.data:
            raise ValueError("A/B test not found")
        
        variants = test.data["variants"]
        traffic_split = test.data["traffic_split"]
        
        # Weighted random selection
        rand = random.uniform(0, 100)
        cumulative = 0
        
        for i, variant in enumerate(variants):
            cumulative += traffic_split[i]
            if rand <= cumulative:
                # Record assignment
                self.supabase.table("ab_test_assignments").insert({
                    "test_id": str(test_id),
                    "recipient_id": str(recipient_id),
                    "variant_id": variant["id"],
                    "assigned_at": datetime.utcnow().isoformat(),
                }).execute()
                
                return variant["id"]
        
        # Fallback to first variant
        return variants[0]["id"]
    
    async def get_variant_content(
        self,
        test_id: UUID,
        variant_id: str,
        original_content: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Get modified content based on variant.
        """
        test = self.supabase.table("ab_tests").select(
            "variant_type, variants"
        ).eq("id", str(test_id)).single().execute()
        
        if not test.data:
            return original_content
        
        variant_type = test.data["variant_type"]
        variant = next(
            (v for v in test.data["variants"] if v["id"] == variant_id),
            None
        )
        
        if not variant:
            return original_content
        
        modified = original_content.copy()
        variant_content = variant.get("content", {})
        
        if variant_type == "subject":
            modified["subject"] = variant_content.get("subject", original_content.get("subject"))
        elif variant_type == "content":
            modified["html_content"] = variant_content.get("html_content", original_content.get("html_content"))
        elif variant_type == "from_name":
            modified["from_name"] = variant_content.get("from_name", original_content.get("from_name"))
        
        return modified
    
    async def calculate_results(self, test_id: UUID) -> ABTestResult:
        """
        Calculate current results for an A/B test.
        """
        test = self.supabase.table("ab_tests").select("*").eq(
            "id", str(test_id)
        ).single().execute()
        
        if not test.data:
            raise ValueError("A/B test not found")
        
        test_data = test.data
        variants = test_data["variants"]
        winning_metric = test_data["winning_metric"]
        
        variant_stats = []
        
        for variant in variants:
            # Get recipients assigned to this variant
            assignments = self.supabase.table("ab_test_assignments").select(
                "recipient_id"
            ).eq("test_id", str(test_id)).eq("variant_id", variant["id"]).execute()
            
            recipient_ids = [a["recipient_id"] for a in assignments.data or []]
            
            if not recipient_ids:
                variant_stats.append(VariantStats(
                    variant_id=variant["id"],
                    name=variant["name"],
                    recipients_count=0,
                    sent_count=0,
                    opened_count=0,
                    clicked_count=0,
                    converted_count=0,
                    open_rate=0,
                    click_rate=0,
                    conversion_rate=0,
                ))
                continue
            
            # Get recipient stats
            recipients = self.supabase.table("recipients").select(
                "status, opened_at, clicked_at"
            ).in_("id", recipient_ids).execute()
            
            sent = sum(1 for r in recipients.data if r["status"] == "sent")
            opened = sum(1 for r in recipients.data if r.get("opened_at"))
            clicked = sum(1 for r in recipients.data if r.get("clicked_at"))
            
            variant_stats.append(VariantStats(
                variant_id=variant["id"],
                name=variant["name"],
                recipients_count=len(recipient_ids),
                sent_count=sent,
                opened_count=opened,
                clicked_count=clicked,
                converted_count=0,  # Would need conversion tracking
                open_rate=round(opened / sent * 100, 2) if sent > 0 else 0,
                click_rate=round(clicked / sent * 100, 2) if sent > 0 else 0,
                conversion_rate=0,
            ))
        
        # Determine winner
        metric_attr = winning_metric.replace("_rate", "_rate")
        sorted_variants = sorted(
            variant_stats,
            key=lambda v: getattr(v, metric_attr, 0),
            reverse=True
        )
        
        # Check statistical significance
        confidence, is_significant = self._calculate_significance(
            sorted_variants[:2] if len(sorted_variants) >= 2 else sorted_variants,
            winning_metric,
            test_data["confidence_level"]
        )
        
        winner = sorted_variants[0] if is_significant else None
        
        return ABTestResult(
            test_id=test_id,
            status=ABTestStatus(test_data["status"]),
            variants=variant_stats,
            winner=winner,
            confidence=confidence,
            is_significant=is_significant,
        )
    
    def _calculate_significance(
        self,
        variants: List[VariantStats],
        metric: str,
        required_confidence: float
    ) -> tuple[float, bool]:
        """
        Calculate statistical significance using Z-test for proportions.
        """
        if len(variants) < 2:
            return 0, False
        
        v1, v2 = variants[0], variants[1]
        
        n1 = v1.sent_count
        n2 = v2.sent_count
        
        if n1 < 30 or n2 < 30:  # Minimum sample size
            return 0, False
        
        # Get proportions based on metric
        if metric == "open_rate":
            p1 = v1.opened_count / n1 if n1 > 0 else 0
            p2 = v2.opened_count / n2 if n2 > 0 else 0
        elif metric == "click_rate":
            p1 = v1.clicked_count / n1 if n1 > 0 else 0
            p2 = v2.clicked_count / n2 if n2 > 0 else 0
        else:
            return 0, False
        
        # Pooled proportion
        p_pool = (p1 * n1 + p2 * n2) / (n1 + n2)
        
        if p_pool == 0 or p_pool == 1:
            return 0, False
        
        # Standard error
        se = math.sqrt(p_pool * (1 - p_pool) * (1/n1 + 1/n2))
        
        if se == 0:
            return 0, False
        
        # Z-score
        z = abs(p1 - p2) / se
        
        # Convert Z-score to confidence
        # Using normal distribution approximation
        confidence = self._z_to_confidence(z)
        
        is_significant = confidence >= required_confidence
        
        return confidence, is_significant
    
    def _z_to_confidence(self, z: float) -> float:
        """Convert Z-score to confidence level (approximate)"""
        # Approximation of cumulative normal distribution
        if z > 3.5:
            return 0.9999
        
        # Taylor series approximation
        t = 1 / (1 + 0.2316419 * z)
        d = 0.3989423 * math.exp(-z * z / 2)
        p = d * t * (0.3193815 + t * (-0.3565638 + t * (1.781478 + t * (-1.821256 + t * 1.330274))))
        
        return 1 - 2 * p
    
    async def select_winner(self, test_id: UUID, variant_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Select a winner and apply to remaining campaign recipients.
        """
        test = self.supabase.table("ab_tests").select("*").eq(
            "id", str(test_id)
        ).single().execute()
        
        if not test.data:
            raise ValueError("A/B test not found")
        
        test_data = test.data
        
        if variant_id:
            # Manual selection
            winner = next(
                (v for v in test_data["variants"] if v["id"] == variant_id),
                None
            )
            if not winner:
                raise ValueError("Variant not found")
        else:
            # Auto-select based on results
            results = await self.calculate_results(test_id)
            if not results.winner:
                raise ValueError("No statistically significant winner yet")
            winner = next(
                (v for v in test_data["variants"] if v["id"] == results.winner.variant_id),
                None
            )
        
        if not winner:
            raise ValueError(f"Winner variant not found for test {test_id}")
        
        # Update campaign with winning variant content
        campaign_update = {}
        variant_content = winner.get("content", {})
        
        if test_data["variant_type"] == "subject":
            campaign_update["subject"] = variant_content.get("subject")
        elif test_data["variant_type"] == "content":
            campaign_update["html_content"] = variant_content.get("html_content")
        elif test_data["variant_type"] == "from_name":
            campaign_update["from_name"] = variant_content.get("from_name")
        
        if campaign_update:
            self.supabase.table("campaigns").update(campaign_update).eq(
                "id", test_data["campaign_id"]
            ).execute()
        
        # Update test status
        self.supabase.table("ab_tests").update({
            "status": ABTestStatus.WINNER_SELECTED.value,
            "winner_variant_id": winner["id"],
            "completed_at": datetime.utcnow().isoformat(),
        }).eq("id", str(test_id)).execute()
        
        logger.info(f"A/B test {test_id}: Winner selected - {winner['name']}")
        
        return {
            "test_id": str(test_id),
            "winner": winner,
            "applied_to_campaign": test_data["campaign_id"],
        }


# Singleton instance
_ab_testing_service: Optional[ABTestingService] = None


def get_ab_testing_service() -> ABTestingService:
    """Get or create A/B testing service instance"""
    global _ab_testing_service
    if _ab_testing_service is None:
        _ab_testing_service = ABTestingService()
    return _ab_testing_service
