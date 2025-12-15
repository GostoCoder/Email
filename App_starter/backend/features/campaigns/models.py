"""
Campaign Models - Database models
"""

from datetime import datetime
from typing import Optional, Dict, Any
from uuid import UUID

from pydantic import BaseModel


class Campaign(BaseModel):
    """Campaign database model"""
    id: UUID
    name: str
    subject: str
    from_name: str
    from_email: str
    reply_to: Optional[str]
    template_id: Optional[UUID]
    html_content: str
    status: str
    scheduled_at: Optional[datetime]
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    total_recipients: int
    sent_count: int
    failed_count: int
    opened_count: int
    clicked_count: int
    unsubscribed_count: int
    batch_size: int
    rate_limit_per_second: int
    metadata: Dict[str, Any]
    created_at: datetime
    updated_at: datetime
    created_by: Optional[UUID]


class Recipient(BaseModel):
    """Recipient database model"""
    id: UUID
    campaign_id: UUID
    email: str
    first_name: Optional[str]
    last_name: Optional[str]
    company: Optional[str]
    custom_data: Dict[str, Any]
    status: str
    sent_at: Optional[datetime]
    opened_at: Optional[datetime]
    clicked_at: Optional[datetime]
    unsubscribed_at: Optional[datetime]
    error_message: Optional[str]
    retry_count: int
    metadata: Dict[str, Any]
    created_at: datetime
    updated_at: datetime


class EmailTemplate(BaseModel):
    """Email template database model"""
    id: UUID
    name: str
    description: Optional[str]
    html_content: str
    variables: list
    thumbnail_url: Optional[str]
    is_default: bool
    category: Optional[str]
    created_at: datetime
    updated_at: datetime
    created_by: Optional[UUID]


class UnsubscribeEntry(BaseModel):
    """Unsubscribe list entry database model"""
    id: UUID
    email: str
    reason: Optional[str]
    unsubscribed_at: datetime
    ip_address: Optional[str]
    user_agent: Optional[str]
    campaign_id: Optional[UUID]
    is_global: bool
    metadata: Dict[str, Any]
    created_at: datetime


class EmailLog(BaseModel):
    """Email log database model"""
    id: UUID
    campaign_id: UUID
    recipient_id: UUID
    email: str
    event_type: str
    event_data: Dict[str, Any]
    provider_message_id: Optional[str]
    error_code: Optional[str]
    error_message: Optional[str]
    timestamp: datetime
    metadata: Dict[str, Any]
