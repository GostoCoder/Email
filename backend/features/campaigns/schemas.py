"""
Campaign Models - Pydantic schemas for campaigns
"""

from datetime import datetime
from typing import Optional, Dict, Any, List
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, field_validator


# ============================================
# Campaign Schemas
# ============================================

class CampaignBase(BaseModel):
    """Base campaign schema"""
    name: str = Field(..., min_length=1, max_length=255)
    subject: Optional[str] = Field(None, min_length=1, max_length=500)
    from_name: Optional[str] = Field(None, min_length=1, max_length=255)
    from_email: Optional[EmailStr] = None
    reply_to: Optional[EmailStr] = None
    html_content: Optional[str] = Field(None, min_length=1)
    template_id: Optional[UUID] = None
    batch_size: int = Field(default=100, ge=1, le=1000)
    rate_limit_per_second: int = Field(default=10, ge=1, le=100)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class CampaignCreate(CampaignBase):
    """Schema for creating a campaign"""
    scheduled_at: Optional[datetime] = None


class CampaignUpdate(BaseModel):
    """Schema for updating a campaign"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    subject: Optional[str] = Field(None, min_length=1, max_length=500)
    from_name: Optional[str] = Field(None, min_length=1, max_length=255)
    from_email: Optional[EmailStr] = None
    reply_to: Optional[EmailStr] = None
    html_content: Optional[str] = Field(None, min_length=1)
    template_id: Optional[UUID] = None
    status: Optional[str] = None
    batch_size: Optional[int] = Field(None, ge=1, le=1000)
    rate_limit_per_second: Optional[int] = Field(None, ge=1, le=100)
    scheduled_at: Optional[datetime] = None
    metadata: Optional[Dict[str, Any]] = None
    
    @field_validator('status')
    @classmethod
    def validate_status(cls, v):
        valid_statuses = ['draft', 'scheduled', 'sending', 'paused', 'completed', 'failed', 'cancelled']
        if v and v not in valid_statuses:
            raise ValueError(f'Status must be one of: {", ".join(valid_statuses)}')
        return v


class CampaignResponse(CampaignBase):
    """Schema for campaign response"""
    id: UUID
    status: str
    scheduled_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    total_recipients: int = 0
    sent_count: int = 0
    failed_count: int = 0
    opened_count: int = 0
    clicked_count: int = 0
    unsubscribed_count: int = 0
    created_at: datetime
    updated_at: datetime
    created_by: Optional[UUID] = None
    
    class Config:
        from_attributes = True


class CampaignStats(BaseModel):
    """Campaign statistics"""
    campaign_id: UUID
    total_recipients: int
    sent_count: int
    failed_count: int
    opened_count: int
    clicked_count: int
    unsubscribed_count: int
    delivery_rate: float
    open_rate: float
    click_rate: float
    unsubscribe_rate: float


# ============================================
# Recipient Schemas
# ============================================

class RecipientBase(BaseModel):
    """Base recipient schema"""
    email: EmailStr
    first_name: Optional[str] = Field(None, max_length=255)
    last_name: Optional[str] = Field(None, max_length=255)
    company: Optional[str] = Field(None, max_length=255)
    custom_data: Dict[str, Any] = Field(default_factory=dict)


class RecipientCreate(RecipientBase):
    """Schema for creating a recipient"""
    campaign_id: UUID


class RecipientUpdate(BaseModel):
    """Schema for updating a recipient"""
    first_name: Optional[str] = Field(None, max_length=255)
    last_name: Optional[str] = Field(None, max_length=255)
    company: Optional[str] = Field(None, max_length=255)
    custom_data: Optional[Dict[str, Any]] = None
    status: Optional[str] = None
    
    @field_validator('status')
    @classmethod
    def validate_status(cls, v):
        valid_statuses = ['pending', 'sending', 'sent', 'failed', 'bounced', 'unsubscribed']
        if v and v not in valid_statuses:
            raise ValueError(f'Status must be one of: {", ".join(valid_statuses)}')
        return v


class RecipientResponse(RecipientBase):
    """Schema for recipient response"""
    id: UUID
    campaign_id: UUID
    status: str
    sent_at: Optional[datetime] = None
    opened_at: Optional[datetime] = None
    clicked_at: Optional[datetime] = None
    unsubscribed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    retry_count: int = 0
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class RecipientBulkCreate(BaseModel):
    """Schema for bulk creating recipients"""
    campaign_id: UUID
    recipients: List[RecipientBase]


# ============================================
# Email Template Schemas
# ============================================

class EmailTemplateBase(BaseModel):
    """Base email template schema"""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    html_content: str = Field(..., min_length=1)
    variables: List[str] = Field(default_factory=list)
    thumbnail_url: Optional[str] = None
    is_default: bool = False
    category: Optional[str] = Field(None, max_length=100)


class EmailTemplateCreate(EmailTemplateBase):
    """Schema for creating an email template"""
    pass


class EmailTemplateUpdate(BaseModel):
    """Schema for updating an email template"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    html_content: Optional[str] = Field(None, min_length=1)
    variables: Optional[List[str]] = None
    thumbnail_url: Optional[str] = None
    is_default: Optional[bool] = None
    category: Optional[str] = Field(None, max_length=100)


class EmailTemplateResponse(EmailTemplateBase):
    """Schema for email template response"""
    id: UUID
    created_at: datetime
    updated_at: datetime
    created_by: Optional[UUID] = None
    
    class Config:
        from_attributes = True


# ============================================
# Unsubscribe Schemas
# ============================================

class UnsubscribeCreate(BaseModel):
    """Schema for creating an unsubscribe request"""
    email: EmailStr
    reason: Optional[str] = Field(None, max_length=1000)
    campaign_id: Optional[UUID] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None


class UnsubscribeResponse(BaseModel):
    """Schema for unsubscribe response"""
    id: UUID
    email: EmailStr
    reason: Optional[str] = None
    unsubscribed_at: datetime
    campaign_id: Optional[UUID] = None
    is_global: bool = True
    
    class Config:
        from_attributes = True


# ============================================
# Email Log Schemas
# ============================================

class EmailLogCreate(BaseModel):
    """Schema for creating an email log"""
    campaign_id: UUID
    recipient_id: UUID
    email: EmailStr
    event_type: str
    event_data: Dict[str, Any] = Field(default_factory=dict)
    provider_message_id: Optional[str] = None
    error_code: Optional[str] = None
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    @field_validator('event_type')
    @classmethod
    def validate_event_type(cls, v):
        valid_types = ['sent', 'delivered', 'opened', 'clicked', 'bounced', 'hard_bounce', 'soft_bounce', 'failed', 'unsubscribed', 'spam_report']
        if v not in valid_types:
            raise ValueError(f'Event type must be one of: {", ".join(valid_types)}')
        return v


class EmailLogResponse(EmailLogCreate):
    """Schema for email log response"""
    id: UUID
    timestamp: datetime
    
    class Config:
        from_attributes = True


# ============================================
# CSV Import Schemas
# ============================================

class CSVImportResponse(BaseModel):
    """Response after CSV import"""
    campaign_id: UUID
    file_id: UUID
    total_rows: int
    valid_rows: int
    invalid_rows: int
    duplicates: int
    errors: List[Dict[str, Any]] = Field(default_factory=list)


class CSVPreviewRow(BaseModel):
    """Preview row from CSV"""
    row_number: int
    email: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    company: Optional[str] = None
    is_valid: bool
    error: Optional[str] = None


class CSVPreviewResponse(BaseModel):
    """Preview response for CSV"""
    total_rows: int
    preview_rows: List[CSVPreviewRow]
    detected_columns: List[str]
    column_mapping: Dict[str, str]


# ============================================
# Campaign Action Schemas
# ============================================

class CampaignSendRequest(BaseModel):
    """Request to start sending a campaign"""
    campaign_id: UUID
    test_mode: bool = False
    test_emails: Optional[List[EmailStr]] = None


class CampaignProgressResponse(BaseModel):
    """Real-time campaign progress"""
    campaign_id: UUID
    status: str
    total_recipients: int
    sent_count: int
    failed_count: int
    remaining: int
    progress_percentage: float
    estimated_time_remaining: Optional[int] = None  # seconds
    current_batch: Optional[int] = None
    errors: List[Dict[str, Any]] = Field(default_factory=list)


# ============================================
# Template Rendering Schemas
# ============================================

class TemplateRenderRequest(BaseModel):
    """Request to render a template with data"""
    template_id: Optional[UUID] = None
    html_content: Optional[str] = None
    data: Dict[str, Any]
    
    @field_validator('html_content', 'template_id')
    @classmethod
    def validate_template_source(cls, v, info):
        # Either template_id or html_content must be provided
        if not v and not info.data.get('template_id') and not info.data.get('html_content'):
            raise ValueError('Either template_id or html_content must be provided')
        return v


class TemplateRenderResponse(BaseModel):
    """Rendered template response"""
    html_content: str
    subject: str
    variables_used: List[str]


# ============================================
# Campaign Scheduling Schemas
# ============================================

class CampaignScheduleRequest(BaseModel):
    """Request to schedule a campaign for later sending"""
    scheduled_at: datetime = Field(..., description="When to send the campaign (ISO 8601 format)")
    
    @field_validator('scheduled_at')
    @classmethod
    def validate_scheduled_at(cls, v):
        from datetime import timezone
        # Ensure the datetime is timezone-aware
        if v.tzinfo is None:
            v = v.replace(tzinfo=timezone.utc)
        # Check that the scheduled time is in the future
        now = datetime.now(timezone.utc)
        if v <= now:
            raise ValueError('Scheduled time must be in the future')
        return v


class CampaignScheduleResponse(BaseModel):
    """Response after scheduling a campaign"""
    campaign_id: UUID
    scheduled_at: datetime
    status: str
    message: str
