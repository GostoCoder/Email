"""
Campaign Endpoints - REST API for campaign management
"""

import csv
import io
import logging
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, File, UploadFile, HTTPException, BackgroundTasks, Query
from fastapi.responses import JSONResponse

from core.config import get_settings
from core.supabase import get_supabase_client
from core.template_service import get_template_service
from features.campaigns.schemas import (
    CampaignCreate,
    CampaignUpdate,
    CampaignResponse,
    CampaignStats,
    RecipientCreate,
    RecipientBulkCreate,
    RecipientResponse,
    RecipientUpdate,
    CSVImportResponse,
    CSVPreviewResponse,
    CSVPreviewRow,
    CampaignSendRequest,
    CampaignProgressResponse,
    EmailTemplateCreate,
    EmailTemplateUpdate,
    EmailTemplateResponse,
    UnsubscribeCreate,
    UnsubscribeResponse,
    TemplateRenderRequest,
    TemplateRenderResponse,
)

router = APIRouter()
settings = get_settings()
logger = logging.getLogger(__name__)


# ============================================
# Campaign CRUD Endpoints
# ============================================

@router.post("/campaigns", response_model=CampaignResponse, status_code=201)
async def create_campaign(campaign: CampaignCreate):
    """Create a new email campaign"""
    supabase = get_supabase_client()
    
    campaign_data = campaign.model_dump()
    
    # Set reply_to to from_email if not provided
    if not campaign_data.get("reply_to"):
        campaign_data["reply_to"] = campaign_data["from_email"]
    
    result = supabase.table("campaigns").insert(campaign_data).execute()
    
    if not result.data:
        raise HTTPException(status_code=400, detail="Failed to create campaign")
    
    return result.data[0]


@router.get("/campaigns", response_model=List[CampaignResponse])
async def list_campaigns(
    status: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100)
):
    """List all campaigns with optional filtering"""
    supabase = get_supabase_client()
    
    query = supabase.table("campaigns").select("*")
    
    if status:
        query = query.eq("status", status)
    
    result = query.order("created_at", desc=True).range(skip, skip + limit - 1).execute()
    
    return result.data


@router.get("/campaigns/{campaign_id}", response_model=CampaignResponse)
async def get_campaign(campaign_id: UUID):
    """Get a specific campaign by ID"""
    supabase = get_supabase_client()
    
    result = supabase.table("campaigns").select("*").eq("id", str(campaign_id)).execute()
    
    if not result.data:
        raise HTTPException(status_code=404, detail="Campaign not found")
    
    return result.data[0]


@router.patch("/campaigns/{campaign_id}", response_model=CampaignResponse)
async def update_campaign(campaign_id: UUID, campaign: CampaignUpdate):
    """Update a campaign"""
    supabase = get_supabase_client()
    
    # Only update fields that are provided
    update_data = campaign.model_dump(exclude_unset=True)
    
    if not update_data:
        raise HTTPException(status_code=400, detail="No fields to update")
    
    result = (
        supabase.table("campaigns")
        .update(update_data)
        .eq("id", str(campaign_id))
        .execute()
    )
    
    if not result.data:
        raise HTTPException(status_code=404, detail="Campaign not found")
    
    return result.data[0]


@router.delete("/campaigns/{campaign_id}", status_code=204)
async def delete_campaign(campaign_id: UUID):
    """Delete a campaign and all associated data"""
    supabase = get_supabase_client()
    
    # Check if campaign exists and is not currently sending
    campaign_result = supabase.table("campaigns").select("status").eq("id", str(campaign_id)).execute()
    
    if not campaign_result.data:
        raise HTTPException(status_code=404, detail="Campaign not found")
    
    if campaign_result.data[0]["status"] == "sending":
        raise HTTPException(status_code=400, detail="Cannot delete campaign that is currently sending")
    
    supabase.table("campaigns").delete().eq("id", str(campaign_id)).execute()
    
    return None


@router.get("/campaigns/{campaign_id}/stats", response_model=CampaignStats)
async def get_campaign_stats(campaign_id: UUID):
    """Get detailed statistics for a campaign"""
    supabase = get_supabase_client()
    
    result = supabase.table("campaigns").select("*").eq("id", str(campaign_id)).execute()
    
    if not result.data:
        raise HTTPException(status_code=404, detail="Campaign not found")
    
    campaign = result.data[0]
    
    # Calculate rates
    total = campaign["total_recipients"]
    sent = campaign["sent_count"]
    
    delivery_rate = (sent / total * 100) if total > 0 else 0
    open_rate = (campaign["opened_count"] / sent * 100) if sent > 0 else 0
    click_rate = (campaign["clicked_count"] / sent * 100) if sent > 0 else 0
    unsubscribe_rate = (campaign["unsubscribed_count"] / sent * 100) if sent > 0 else 0
    
    return {
        "campaign_id": campaign_id,
        "total_recipients": total,
        "sent_count": sent,
        "failed_count": campaign["failed_count"],
        "opened_count": campaign["opened_count"],
        "clicked_count": campaign["clicked_count"],
        "unsubscribed_count": campaign["unsubscribed_count"],
        "delivery_rate": round(delivery_rate, 2),
        "open_rate": round(open_rate, 2),
        "click_rate": round(click_rate, 2),
        "unsubscribe_rate": round(unsubscribe_rate, 2),
    }


# ============================================
# Recipient Management Endpoints
# ============================================

@router.post("/campaigns/{campaign_id}/recipients", response_model=RecipientResponse, status_code=201)
async def add_recipient(campaign_id: UUID, recipient: RecipientCreate):
    """Add a single recipient to a campaign"""
    supabase = get_supabase_client()
    
    # Check if campaign exists
    campaign_result = supabase.table("campaigns").select("id").eq("id", str(campaign_id)).execute()
    if not campaign_result.data:
        raise HTTPException(status_code=404, detail="Campaign not found")
    
    # Check if email is unsubscribed
    unsubscribe_check = (
        supabase.table("unsubscribe_list")
        .select("id")
        .eq("email", recipient.email)
        .eq("is_global", True)
        .execute()
    )
    
    if unsubscribe_check.data:
        raise HTTPException(
            status_code=400,
            detail="This email address has unsubscribed from all communications"
        )
    
    recipient_data = recipient.model_dump()
    result = supabase.table("recipients").insert(recipient_data).execute()
    
    if not result.data:
        raise HTTPException(status_code=400, detail="Failed to add recipient")
    
    # Update campaign total_recipients count
    supabase.rpc("increment_campaign_recipients", {"campaign_id": str(campaign_id)}).execute()
    
    return result.data[0]


@router.get("/campaigns/{campaign_id}/recipients", response_model=List[RecipientResponse])
async def list_recipients(
    campaign_id: UUID,
    status: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000)
):
    """List recipients for a campaign"""
    supabase = get_supabase_client()
    
    query = supabase.table("recipients").select("*").eq("campaign_id", str(campaign_id))
    
    if status:
        query = query.eq("status", status)
    
    result = query.order("created_at").range(skip, skip + limit - 1).execute()
    
    return result.data


@router.get("/recipients/{recipient_id}", response_model=RecipientResponse)
async def get_recipient(recipient_id: UUID):
    """Get a specific recipient"""
    supabase = get_supabase_client()
    
    result = supabase.table("recipients").select("*").eq("id", str(recipient_id)).execute()
    
    if not result.data:
        raise HTTPException(status_code=404, detail="Recipient not found")
    
    return result.data[0]


@router.patch("/recipients/{recipient_id}", response_model=RecipientResponse)
async def update_recipient(recipient_id: UUID, recipient: RecipientUpdate):
    """Update a recipient"""
    supabase = get_supabase_client()
    
    update_data = recipient.model_dump(exclude_unset=True)
    
    if not update_data:
        raise HTTPException(status_code=400, detail="No fields to update")
    
    result = (
        supabase.table("recipients")
        .update(update_data)
        .eq("id", str(recipient_id))
        .execute()
    )
    
    if not result.data:
        raise HTTPException(status_code=404, detail="Recipient not found")
    
    return result.data[0]


@router.delete("/recipients/{recipient_id}", status_code=204)
async def delete_recipient(recipient_id: UUID):
    """Delete a recipient"""
    supabase = get_supabase_client()
    
    supabase.table("recipients").delete().eq("id", str(recipient_id)).execute()
    
    return None


# ============================================
# CSV Import Endpoints
# ============================================

@router.post("/campaigns/{campaign_id}/import-csv/preview", response_model=CSVPreviewResponse)
async def preview_csv(campaign_id: UUID, file: UploadFile = File(...)):
    """Preview CSV file before importing"""
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="File must be a CSV")
    
    try:
        contents = await file.read()
        decoded = contents.decode('utf-8')
        csv_reader = csv.DictReader(io.StringIO(decoded))
        
        # Get column names
        fieldnames = csv_reader.fieldnames or []
        
        # Auto-detect column mapping
        column_mapping = {}
        for col in fieldnames:
            col_lower = col.lower().strip()
            if 'email' in col_lower or 'mail' in col_lower:
                column_mapping['email'] = col
            elif 'first' in col_lower or 'prénom' in col_lower or 'prenom' in col_lower:
                column_mapping['first_name'] = col
            elif 'last' in col_lower or 'nom' in col_lower:
                column_mapping['last_name'] = col
            elif 'company' in col_lower or 'société' in col_lower or 'societe' in col_lower or 'entreprise' in col_lower:
                column_mapping['company'] = col
        
        # Preview first 10 rows
        preview_rows = []
        total_rows = 0
        
        for idx, row in enumerate(csv_reader):
            total_rows += 1
            
            if idx < 10:
                email = row.get(column_mapping.get('email', ''), '')
                first_name = row.get(column_mapping.get('first_name', ''), '')
                last_name = row.get(column_mapping.get('last_name', ''), '')
                company = row.get(column_mapping.get('company', ''), '')
                
                # Validate email
                is_valid = '@' in email and '.' in email
                error = None if is_valid else "Invalid email format"
                
                preview_rows.append(CSVPreviewRow(
                    row_number=idx + 1,
                    email=email,
                    first_name=first_name or None,
                    last_name=last_name or None,
                    company=company or None,
                    is_valid=is_valid,
                    error=error
                ))
        
        return CSVPreviewResponse(
            total_rows=total_rows,
            preview_rows=preview_rows,
            detected_columns=fieldnames,
            column_mapping=column_mapping
        )
        
    except Exception as e:
        logger.error(f"CSV preview error: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Error reading CSV: {str(e)}")


@router.post("/campaigns/{campaign_id}/import-csv", response_model=CSVImportResponse)
async def import_csv(
    campaign_id: UUID,
    file: UploadFile = File(...),
    column_mapping: str = Query(..., description="JSON string with column mapping")
):
    """Import recipients from CSV file"""
    import json
    from email_validator import validate_email, EmailNotValidError
    
    supabase = get_supabase_client()
    
    # Check if campaign exists
    campaign_result = supabase.table("campaigns").select("id, status").eq("id", str(campaign_id)).execute()
    if not campaign_result.data:
        raise HTTPException(status_code=404, detail="Campaign not found")
    
    if campaign_result.data[0]["status"] not in ["draft", "scheduled"]:
        raise HTTPException(
            status_code=400,
            detail="Can only import recipients for draft or scheduled campaigns"
        )
    
    try:
        mapping = json.loads(column_mapping)
        contents = await file.read()
        decoded = contents.decode('utf-8')
        csv_reader = csv.DictReader(io.StringIO(decoded))
        
        total_rows = 0
        valid_rows = 0
        invalid_rows = 0
        duplicates = 0
        errors = []
        seen_emails = set()
        
        # Get existing unsubscribed emails
        unsubscribed = supabase.table("unsubscribe_list").select("email").eq("is_global", True).execute()
        unsubscribed_emails = {row["email"] for row in unsubscribed.data}
        
        recipients_to_insert = []
        
        for idx, row in enumerate(csv_reader):
            total_rows += 1
            
            try:
                email = row.get(mapping.get('email', ''), '').strip()
                
                if not email:
                    invalid_rows += 1
                    errors.append({"row": idx + 1, "error": "Missing email"})
                    continue
                
                # Validate email
                try:
                    validated = validate_email(email)
                    email = validated.email
                except EmailNotValidError as e:
                    invalid_rows += 1
                    errors.append({"row": idx + 1, "error": f"Invalid email: {str(e)}"})
                    continue
                
                # Check for duplicates in CSV
                if email in seen_emails:
                    duplicates += 1
                    continue
                
                # Check if unsubscribed
                if email in unsubscribed_emails:
                    invalid_rows += 1
                    errors.append({"row": idx + 1, "error": "Email is unsubscribed"})
                    continue
                
                seen_emails.add(email)
                
                recipient_data = {
                    "campaign_id": str(campaign_id),
                    "email": email,
                    "first_name": row.get(mapping.get('first_name', ''), '').strip() or None,
                    "last_name": row.get(mapping.get('last_name', ''), '').strip() or None,
                    "company": row.get(mapping.get('company', ''), '').strip() or None,
                    "status": "pending"
                }
                
                recipients_to_insert.append(recipient_data)
                valid_rows += 1
                
            except Exception as e:
                invalid_rows += 1
                errors.append({"row": idx + 1, "error": str(e)})
        
        # Bulk insert recipients
        if recipients_to_insert:
            supabase.table("recipients").insert(recipients_to_insert).execute()
            
            # Update campaign total_recipients
            supabase.table("campaigns").update({
                "total_recipients": valid_rows
            }).eq("id", str(campaign_id)).execute()
        
        # Store file info
        file_data = {
            "campaign_id": str(campaign_id),
            "file_name": file.filename,
            "file_path": f"campaigns/{campaign_id}/{file.filename}",
            "file_size": len(contents),
            "mime_type": "text/csv",
            "total_rows": total_rows,
            "valid_rows": valid_rows,
            "invalid_rows": invalid_rows,
            "status": "completed"
        }
        
        file_result = supabase.table("campaign_files").insert(file_data).execute()
        
        return CSVImportResponse(
            campaign_id=campaign_id,
            file_id=UUID(file_result.data[0]["id"]),
            total_rows=total_rows,
            valid_rows=valid_rows,
            invalid_rows=invalid_rows,
            duplicates=duplicates,
            errors=errors[:100]  # Limit errors to first 100
        )
        
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid column mapping JSON")
    except Exception as e:
        logger.error(f"CSV import error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Import failed: {str(e)}")


# ============================================
# Campaign Sending Endpoints
# ============================================

@router.post("/campaigns/{campaign_id}/send", status_code=202)
async def send_campaign(
    campaign_id: UUID,
    request: CampaignSendRequest,
    background_tasks: BackgroundTasks
):
    """Start sending a campaign"""
    from features.campaigns.tasks import process_campaign_send
    
    supabase = get_supabase_client()
    
    # Get campaign
    campaign_result = supabase.table("campaigns").select("*").eq("id", str(campaign_id)).execute()
    
    if not campaign_result.data:
        raise HTTPException(status_code=404, detail="Campaign not found")
    
    campaign = campaign_result.data[0]
    
    # Validate campaign can be sent
    if campaign["status"] not in ["draft", "scheduled", "paused"]:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot send campaign with status: {campaign['status']}"
        )
    
    if campaign["total_recipients"] == 0:
        raise HTTPException(status_code=400, detail="Campaign has no recipients")
    
    # Update campaign status
    supabase.table("campaigns").update({
        "status": "sending",
        "started_at": "now()"
    }).eq("id", str(campaign_id)).execute()
    
    # Queue the send task
    background_tasks.add_task(process_campaign_send, campaign_id, request.test_mode, request.test_emails)
    
    return {
        "message": "Campaign sending started",
        "campaign_id": campaign_id,
        "test_mode": request.test_mode
    }


@router.post("/campaigns/{campaign_id}/pause")
async def pause_campaign(campaign_id: UUID):
    """Pause a sending campaign"""
    supabase = get_supabase_client()
    
    result = (
        supabase.table("campaigns")
        .update({"status": "paused"})
        .eq("id", str(campaign_id))
        .eq("status", "sending")
        .execute()
    )
    
    if not result.data:
        raise HTTPException(
            status_code=400,
            detail="Campaign not found or not in sending status"
        )
    
    return {"message": "Campaign paused", "campaign_id": campaign_id}


@router.get("/campaigns/{campaign_id}/progress", response_model=CampaignProgressResponse)
async def get_campaign_progress(campaign_id: UUID):
    """Get real-time progress of a sending campaign"""
    supabase = get_supabase_client()
    
    result = supabase.table("campaigns").select("*").eq("id", str(campaign_id)).execute()
    
    if not result.data:
        raise HTTPException(status_code=404, detail="Campaign not found")
    
    campaign = result.data[0]
    
    total = campaign["total_recipients"]
    sent = campaign["sent_count"]
    failed = campaign["failed_count"]
    remaining = total - sent - failed
    
    progress_percentage = (sent / total * 100) if total > 0 else 0
    
    # Get recent errors
    errors_result = (
        supabase.table("email_logs")
        .select("email, error_message")
        .eq("campaign_id", str(campaign_id))
        .eq("event_type", "failed")
        .order("timestamp", desc=True)
        .limit(10)
        .execute()
    )
    
    return CampaignProgressResponse(
        campaign_id=campaign_id,
        status=campaign["status"],
        total_recipients=total,
        sent_count=sent,
        failed_count=failed,
        remaining=remaining,
        progress_percentage=round(progress_percentage, 2),
        errors=errors_result.data if errors_result.data else []
    )


# ============================================
# Template Endpoints
# ============================================

@router.post("/templates", response_model=EmailTemplateResponse, status_code=201)
async def create_template(template: EmailTemplateCreate):
    """Create a new email template"""
    supabase = get_supabase_client()
    
    # Extract variables from HTML content
    template_service = get_template_service()
    variables = template_service.extract_variables(template.html_content)
    
    template_data = template.model_dump()
    template_data["variables"] = variables
    
    result = supabase.table("email_templates").insert(template_data).execute()
    
    if not result.data:
        raise HTTPException(status_code=400, detail="Failed to create template")
    
    return result.data[0]


@router.get("/templates", response_model=List[EmailTemplateResponse])
async def list_templates(
    category: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100)
):
    """List all email templates"""
    supabase = get_supabase_client()
    
    query = supabase.table("email_templates").select("*")
    
    if category:
        query = query.eq("category", category)
    
    result = query.order("created_at", desc=True).range(skip, skip + limit - 1).execute()
    
    return result.data


@router.get("/templates/{template_id}", response_model=EmailTemplateResponse)
async def get_template(template_id: UUID):
    """Get a specific template"""
    supabase = get_supabase_client()
    
    result = supabase.table("email_templates").select("*").eq("id", str(template_id)).execute()
    
    if not result.data:
        raise HTTPException(status_code=404, detail="Template not found")
    
    return result.data[0]


@router.patch("/templates/{template_id}", response_model=EmailTemplateResponse)
async def update_template(template_id: UUID, template: EmailTemplateUpdate):
    """Update a template"""
    supabase = get_supabase_client()
    
    update_data = template.model_dump(exclude_unset=True)
    
    # Re-extract variables if HTML content changed
    if "html_content" in update_data:
        template_service = get_template_service()
        update_data["variables"] = template_service.extract_variables(update_data["html_content"])
    
    result = (
        supabase.table("email_templates")
        .update(update_data)
        .eq("id", str(template_id))
        .execute()
    )
    
    if not result.data:
        raise HTTPException(status_code=404, detail="Template not found")
    
    return result.data[0]


@router.delete("/templates/{template_id}", status_code=204)
async def delete_template(template_id: UUID):
    """Delete a template"""
    supabase = get_supabase_client()
    
    supabase.table("email_templates").delete().eq("id", str(template_id)).execute()
    
    return None


@router.post("/templates/render", response_model=TemplateRenderResponse)
async def render_template(request: TemplateRenderRequest):
    """Render a template with provided data (for preview)"""
    template_service = get_template_service()
    supabase = get_supabase_client()
    
    html_content = request.html_content
    
    # If template_id provided, fetch the template
    if request.template_id:
        result = supabase.table("email_templates").select("html_content").eq("id", str(request.template_id)).execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="Template not found")
        
        html_content = result.data[0]["html_content"]
    
    if not html_content:
        raise HTTPException(status_code=400, detail="No template content provided")
    
    try:
        rendered = template_service.render(html_content, request.data)
        variables_used = template_service.extract_variables(html_content)
        
        return TemplateRenderResponse(
            html_content=rendered,
            subject=request.data.get("subject", ""),
            variables_used=variables_used
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Rendering failed: {str(e)}")


# ============================================
# Unsubscribe Endpoints (Public)
# ============================================

@router.post("/unsubscribe", response_model=UnsubscribeResponse, status_code=201)
async def unsubscribe(request: UnsubscribeCreate):
    """Public endpoint for email unsubscription"""
    supabase = get_supabase_client()
    
    # Check if already unsubscribed
    existing = (
        supabase.table("unsubscribe_list")
        .select("id")
        .eq("email", request.email)
        .eq("is_global", True)
        .execute()
    )
    
    if existing.data:
        # Already unsubscribed, return existing record
        return existing.data[0]
    
    # Create unsubscribe entry
    unsubscribe_data = request.model_dump()
    unsubscribe_data["is_global"] = True
    
    result = supabase.table("unsubscribe_list").insert(unsubscribe_data).execute()
    
    if not result.data:
        raise HTTPException(status_code=400, detail="Failed to process unsubscribe request")
    
    # Update any pending recipients with this email
    supabase.table("recipients").update({
        "status": "unsubscribed",
        "unsubscribed_at": "now()"
    }).eq("email", request.email).in_("status", ["pending", "sending"]).execute()
    
    return result.data[0]


@router.get("/unsubscribe/check/{email}")
async def check_unsubscribe_status(email: str):
    """Check if an email is unsubscribed"""
    supabase = get_supabase_client()
    
    result = (
        supabase.table("unsubscribe_list")
        .select("id, unsubscribed_at")
        .eq("email", email)
        .eq("is_global", True)
        .execute()
    )
    
    return {
        "email": email,
        "is_unsubscribed": len(result.data) > 0,
        "unsubscribed_at": result.data[0]["unsubscribed_at"] if result.data else None
    }
