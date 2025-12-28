"""
Advanced Analytics Module

Provides:
- Detailed campaign analytics
- Domain-based statistics
- Time-based engagement heatmaps
- Bounce rate analysis
- Trend analysis across campaigns
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from collections import defaultdict
from uuid import UUID

from core.supabase import get_supabase_client

logger = logging.getLogger(__name__)


class AnalyticsService:
    """Service for advanced campaign analytics"""
    
    def __init__(self):
        self.supabase = get_supabase_client()
    
    async def get_domain_stats(self, campaign_id: UUID) -> List[Dict[str, Any]]:
        """
        Get email statistics grouped by recipient domain.
        
        Returns stats like:
        - gmail.com: 1000 sent, 45% open rate, 12% click rate, 0.5% bounce rate
        """
        result = self.supabase.rpc("get_campaign_domain_stats", {
            "p_campaign_id": str(campaign_id)
        }).execute()
        
        if not result.data:
            # Fallback: calculate manually
            recipients = self.supabase.table("recipients").select(
                "email, status, opened_at, clicked_at"
            ).eq("campaign_id", str(campaign_id)).execute()
            
            domain_stats = defaultdict(lambda: {
                "total": 0, "sent": 0, "opened": 0, "clicked": 0, "failed": 0, "bounced": 0
            })
            
            for r in recipients.data or []:
                domain = r["email"].split("@")[-1].lower()
                domain_stats[domain]["total"] += 1
                
                if r["status"] == "sent":
                    domain_stats[domain]["sent"] += 1
                elif r["status"] == "failed":
                    domain_stats[domain]["failed"] += 1
                elif r["status"] == "bounced":
                    domain_stats[domain]["bounced"] += 1
                
                if r.get("opened_at"):
                    domain_stats[domain]["opened"] += 1
                if r.get("clicked_at"):
                    domain_stats[domain]["clicked"] += 1
            
            # Calculate rates
            stats_list = []
            for domain, stats in domain_stats.items():
                total = stats["total"]
                stats_list.append({
                    "domain": domain,
                    "total_recipients": total,
                    "sent_count": stats["sent"],
                    "open_rate": round(stats["opened"] / total * 100, 2) if total > 0 else 0,
                    "click_rate": round(stats["clicked"] / total * 100, 2) if total > 0 else 0,
                    "bounce_rate": round(stats["bounced"] / total * 100, 2) if total > 0 else 0,
                    "fail_rate": round(stats["failed"] / total * 100, 2) if total > 0 else 0,
                })
            
            # Sort by total recipients
            stats_list.sort(key=lambda x: x["total_recipients"], reverse=True)
            return stats_list
        
        return result.data
    
    async def get_engagement_heatmap(
        self,
        campaign_id: UUID,
        timezone: str = "UTC"
    ) -> Dict[str, Any]:
        """
        Get engagement heatmap data showing opens/clicks by hour and day.
        
        Useful for determining optimal send times.
        """
        # Get email logs for opens and clicks
        logs = self.supabase.table("email_logs").select(
            "event_type, timestamp"
        ).eq("campaign_id", str(campaign_id)).in_(
            "event_type", ["opened", "clicked"]
        ).execute()
        
        # Initialize heatmap: 7 days x 24 hours
        heatmap = {
            "opens": [[0] * 24 for _ in range(7)],  # [day][hour]
            "clicks": [[0] * 24 for _ in range(7)],
        }
        
        day_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        
        for log in logs.data or []:
            try:
                ts = datetime.fromisoformat(log["timestamp"].replace("Z", "+00:00"))
                day = ts.weekday()  # 0 = Monday
                hour = ts.hour
                
                if log["event_type"] == "opened":
                    heatmap["opens"][day][hour] += 1
                elif log["event_type"] == "clicked":
                    heatmap["clicks"][day][hour] += 1
            except (ValueError, KeyError):
                continue
        
        # Find peak times
        max_opens = 0
        max_clicks = 0
        peak_open_time = {"day": 0, "hour": 0}
        peak_click_time = {"day": 0, "hour": 0}
        
        for day in range(7):
            for hour in range(24):
                if heatmap["opens"][day][hour] > max_opens:
                    max_opens = heatmap["opens"][day][hour]
                    peak_open_time = {"day": day_names[day], "hour": hour}
                if heatmap["clicks"][day][hour] > max_clicks:
                    max_clicks = heatmap["clicks"][day][hour]
                    peak_click_time = {"day": day_names[day], "hour": hour}
        
        return {
            "heatmap": heatmap,
            "days": day_names,
            "hours": list(range(24)),
            "peak_open_time": peak_open_time,
            "peak_click_time": peak_click_time,
            "total_opens": sum(sum(row) for row in heatmap["opens"]),
            "total_clicks": sum(sum(row) for row in heatmap["clicks"]),
        }
    
    async def get_bounce_analysis(self, campaign_id: UUID) -> Dict[str, Any]:
        """
        Analyze bounce types and patterns for a campaign.
        """
        # Get bounce events
        bounces = self.supabase.table("email_logs").select(
            "email, event_type, error_code, error_message, timestamp"
        ).eq("campaign_id", str(campaign_id)).in_(
            "event_type", ["bounced", "hard_bounce", "soft_bounce", "failed"]
        ).execute()
        
        analysis = {
            "total_bounces": 0,
            "hard_bounces": 0,
            "soft_bounces": 0,
            "by_reason": defaultdict(int),
            "by_domain": defaultdict(int),
            "affected_domains": [],
        }
        
        for bounce in bounces.data or []:
            analysis["total_bounces"] += 1
            
            event_type = bounce["event_type"]
            if event_type == "hard_bounce":
                analysis["hard_bounces"] += 1
            elif event_type == "soft_bounce":
                analysis["soft_bounces"] += 1
            
            # Categorize by reason
            error = bounce.get("error_message", "Unknown")[:50]
            analysis["by_reason"][error] += 1
            
            # Count by domain
            domain = bounce["email"].split("@")[-1].lower()
            analysis["by_domain"][domain] += 1
        
        # Convert defaultdicts to regular dicts and sort
        analysis["by_reason"] = dict(
            sorted(analysis["by_reason"].items(), key=lambda x: x[1], reverse=True)[:10]
        )
        analysis["by_domain"] = dict(
            sorted(analysis["by_domain"].items(), key=lambda x: x[1], reverse=True)[:10]
        )
        analysis["affected_domains"] = list(analysis["by_domain"].keys())
        
        return analysis
    
    async def get_campaign_trends(
        self,
        days: int = 30,
        limit: int = 10
    ) -> Dict[str, Any]:
        """
        Get trends across multiple campaigns over time.
        """
        cutoff = (datetime.utcnow() - timedelta(days=days)).isoformat()
        
        campaigns = self.supabase.table("campaigns").select(
            "id, name, created_at, total_recipients, sent_count, "
            "opened_count, clicked_count, failed_count"
        ).gte("created_at", cutoff).order(
            "created_at", desc=True
        ).limit(limit).execute()
        
        trends = {
            "campaigns": [],
            "summary": {
                "total_campaigns": 0,
                "total_sent": 0,
                "total_opened": 0,
                "total_clicked": 0,
                "avg_open_rate": 0,
                "avg_click_rate": 0,
            },
            "daily_volume": defaultdict(int),
        }
        
        total_open_rate = 0
        total_click_rate = 0
        
        for c in campaigns.data or []:
            sent = c["sent_count"] or 0
            opened = c["opened_count"] or 0
            clicked = c["clicked_count"] or 0
            
            open_rate = (opened / sent * 100) if sent > 0 else 0
            click_rate = (clicked / sent * 100) if sent > 0 else 0
            
            trends["campaigns"].append({
                "id": c["id"],
                "name": c["name"],
                "created_at": c["created_at"],
                "total_recipients": c["total_recipients"],
                "sent_count": sent,
                "open_rate": round(open_rate, 2),
                "click_rate": round(click_rate, 2),
            })
            
            trends["summary"]["total_campaigns"] += 1
            trends["summary"]["total_sent"] += sent
            trends["summary"]["total_opened"] += opened
            trends["summary"]["total_clicked"] += clicked
            total_open_rate += open_rate
            total_click_rate += click_rate
            
            # Daily volume
            date = c["created_at"][:10]
            trends["daily_volume"][date] += sent
        
        count = trends["summary"]["total_campaigns"]
        if count > 0:
            trends["summary"]["avg_open_rate"] = round(total_open_rate / count, 2)
            trends["summary"]["avg_click_rate"] = round(total_click_rate / count, 2)
        
        trends["daily_volume"] = dict(sorted(trends["daily_volume"].items()))
        
        return trends
    
    async def get_recipient_engagement_score(
        self,
        email: str
    ) -> Dict[str, Any]:
        """
        Calculate engagement score for a specific recipient across all campaigns.
        """
        # Get all recipient records for this email
        recipients = self.supabase.table("recipients").select(
            "id, campaign_id, status, sent_at, opened_at, clicked_at"
        ).eq("email", email).execute()
        
        score_data = {
            "email": email,
            "total_campaigns": 0,
            "total_received": 0,
            "total_opened": 0,
            "total_clicked": 0,
            "engagement_score": 0,  # 0-100
            "engagement_level": "unknown",  # cold, warm, hot, superfan
            "first_seen": None,
            "last_engagement": None,
        }
        
        if not recipients.data:
            return score_data
        
        score_data["total_campaigns"] = len(recipients.data)
        
        for r in recipients.data:
            if r["status"] == "sent":
                score_data["total_received"] += 1
            if r.get("opened_at"):
                score_data["total_opened"] += 1
                if not score_data["last_engagement"] or r["opened_at"] > score_data["last_engagement"]:
                    score_data["last_engagement"] = r["opened_at"]
            if r.get("clicked_at"):
                score_data["total_clicked"] += 1
                if not score_data["last_engagement"] or r["clicked_at"] > score_data["last_engagement"]:
                    score_data["last_engagement"] = r["clicked_at"]
            
            if r.get("sent_at"):
                if not score_data["first_seen"] or r["sent_at"] < score_data["first_seen"]:
                    score_data["first_seen"] = r["sent_at"]
        
        # Calculate engagement score (0-100)
        received = score_data["total_received"]
        if received > 0:
            open_rate = score_data["total_opened"] / received
            click_rate = score_data["total_clicked"] / received
            
            # Weight: opens = 30%, clicks = 70%
            score = (open_rate * 30) + (click_rate * 70)
            score_data["engagement_score"] = round(min(100, score * 100), 1)
        
        # Determine engagement level
        score = score_data["engagement_score"]
        if score >= 70:
            score_data["engagement_level"] = "superfan"
        elif score >= 40:
            score_data["engagement_level"] = "hot"
        elif score >= 20:
            score_data["engagement_level"] = "warm"
        else:
            score_data["engagement_level"] = "cold"
        
        return score_data
    
    async def get_comparative_analysis(
        self,
        campaign_ids: List[UUID]
    ) -> Dict[str, Any]:
        """
        Compare multiple campaigns side by side.
        """
        campaigns = []
        
        for campaign_id in campaign_ids[:5]:  # Limit to 5 campaigns
            result = self.supabase.table("campaigns").select("*").eq(
                "id", str(campaign_id)
            ).execute()
            
            if result.data:
                c = result.data[0]
                sent = c["sent_count"] or 1
                campaigns.append({
                    "id": c["id"],
                    "name": c["name"],
                    "subject": c["subject"],
                    "sent_count": c["sent_count"],
                    "open_rate": round((c["opened_count"] or 0) / sent * 100, 2),
                    "click_rate": round((c["clicked_count"] or 0) / sent * 100, 2),
                    "bounce_rate": round((c["failed_count"] or 0) / sent * 100, 2),
                    "unsubscribe_rate": round((c["unsubscribed_count"] or 0) / sent * 100, 2),
                })
        
        # Determine best performers
        if campaigns:
            best_open = max(campaigns, key=lambda x: x["open_rate"])
            best_click = max(campaigns, key=lambda x: x["click_rate"])
            lowest_bounce = min(campaigns, key=lambda x: x["bounce_rate"])
        else:
            best_open = best_click = lowest_bounce = None
        
        return {
            "campaigns": campaigns,
            "best_open_rate": best_open,
            "best_click_rate": best_click,
            "lowest_bounce_rate": lowest_bounce,
        }


# Singleton instance
_analytics_service: Optional[AnalyticsService] = None


def get_analytics_service() -> AnalyticsService:
    """Get or create analytics service instance"""
    global _analytics_service
    if _analytics_service is None:
        _analytics_service = AnalyticsService()
    return _analytics_service
