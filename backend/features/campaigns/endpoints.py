"""
Campaign Endpoints - REST API for campaign management
"""

import csv
import io
import logging
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, File, UploadFile, HTTPException, BackgroundTasks, Query, Request
from fastapi.responses import JSONResponse, RedirectResponse, Response

from core.config import get_settings
from core.dependencies import get_current_user
from core.supabase import get_supabase_client
from core.template_service import get_template_service
from core.tracking import verify_tracking_token
from core.dns_validator import get_dns_validator
from core.webhooks import get_webhook_service, get_campaign_webhooks
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
    CampaignScheduleRequest,
    CampaignScheduleResponse,
)

router = APIRouter()
settings = get_settings()
logger = logging.getLogger(__name__)


# ============================================
# Campaign CRUD Endpoints
# ============================================

@router.post("/campaigns", response_model=CampaignResponse, status_code=201)
async def create_campaign(campaign: CampaignCreate, _: str = Depends(get_current_user)):
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
    limit: int = Query(50, ge=1, le=100),
    _: str = Depends(get_current_user)
):
    """List all campaigns with optional filtering"""
    supabase = get_supabase_client()
    
    query = supabase.table("campaigns").select("*")
    
    if status:
        query = query.eq("status", status)
    
    result = query.order("created_at", desc=True).range(skip, skip + limit - 1).execute()
    
    return result.data


@router.get("/campaigns/{campaign_id}", response_model=CampaignResponse)
async def get_campaign(campaign_id: UUID, _: str = Depends(get_current_user)):
    """Get a specific campaign by ID"""
    supabase = get_supabase_client()
    
    result = supabase.table("campaigns").select("*").eq("id", str(campaign_id)).execute()
    
    if not result.data:
        raise HTTPException(status_code=404, detail="Campaign not found")
    
    return result.data[0]


@router.patch("/campaigns/{campaign_id}", response_model=CampaignResponse)
async def update_campaign(campaign_id: UUID, campaign: CampaignUpdate, _: str = Depends(get_current_user)):
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
async def delete_campaign(campaign_id: UUID, _: str = Depends(get_current_user)):
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


@router.post("/campaigns/{campaign_id}/duplicate", response_model=CampaignResponse, status_code=201)
async def duplicate_campaign(campaign_id: UUID, _: str = Depends(get_current_user)):
    """
    Duplicate a campaign with all its settings but without recipients.
    New campaign will be in 'draft' status with name suffix '(Copy)'
    """
    supabase = get_supabase_client()
    
    # Get original campaign
    campaign_result = supabase.table("campaigns").select("*").eq("id", str(campaign_id)).execute()
    
    if not campaign_result.data:
        raise HTTPException(status_code=404, detail="Campaign not found")
    
    original = campaign_result.data[0]
    
    # Create new campaign data
    new_campaign = {
        "name": f"{original['name']} (Copy)",
        "subject": original["subject"],
        "from_name": original["from_name"],
        "from_email": original["from_email"],
        "reply_to": original.get("reply_to"),
        "html_content": original["html_content"],
        "template_id": original.get("template_id"),
        "batch_size": original.get("batch_size", 100),
        "rate_limit_per_second": original.get("rate_limit_per_second", 10),
        "metadata": original.get("metadata", {}),
        "status": "draft",
        "total_recipients": 0,
        "sent_count": 0,
        "failed_count": 0,
        "opened_count": 0,
        "clicked_count": 0,
        "unsubscribed_count": 0,
    }
    
    # Insert new campaign
    result = supabase.table("campaigns").insert(new_campaign).execute()
    
    if not result.data:
        raise HTTPException(status_code=400, detail="Failed to duplicate campaign")
    
    logger.info(f"Campaign {campaign_id} duplicated to {result.data[0]['id']}")
    
    return result.data[0]


@router.get("/campaigns/{campaign_id}/stats", response_model=CampaignStats)
async def get_campaign_stats(campaign_id: UUID, _: str = Depends(get_current_user)):
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


@router.get("/campaigns/{campaign_id}/stats/export")
async def export_campaign_stats(campaign_id: UUID, _: str = Depends(get_current_user)):
    """Export campaign statistics and recipient details as CSV"""
    supabase = get_supabase_client()
    
    # Get campaign
    campaign_result = supabase.table("campaigns").select("*").eq("id", str(campaign_id)).execute()
    
    if not campaign_result.data:
        raise HTTPException(status_code=404, detail="Campaign not found")
    
    campaign = campaign_result.data[0]
    
    # Get all recipients
    recipients_result = (
        supabase.table("recipients")
        .select("*")
        .eq("campaign_id", str(campaign_id))
        .execute()
    )
    
    # Create CSV in memory
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Write headers
    writer.writerow([
        "Email",
        "First Name",
        "Last Name",
        "Company",
        "Status",
        "Sent At",
        "Opened At",
        "Clicked At",
        "Unsubscribed At",
        "Error Message",
        "Retry Count"
    ])
    
    # Write recipient data
    for recipient in recipients_result.data:
        writer.writerow([
            recipient.get("email", ""),
            recipient.get("first_name", ""),
            recipient.get("last_name", ""),
            recipient.get("company", ""),
            recipient.get("status", ""),
            recipient.get("sent_at", ""),
            recipient.get("opened_at", ""),
            recipient.get("clicked_at", ""),
            recipient.get("unsubscribed_at", ""),
            recipient.get("error_message", ""),
            recipient.get("retry_count", 0)
        ])
    
    # Return CSV as download
    csv_content = output.getvalue()
    output.close()
    
    filename = f"campaign_{campaign['name'].replace(' ', '_')}_export.csv"
    
    return Response(
        content=csv_content.encode('utf-8'),
        media_type="text/csv",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"'
        }
    )


@router.get("/campaigns/{campaign_id}/preview")
async def preview_campaign_with_sample_data(
    campaign_id: UUID,
    recipient_email: Optional[str] = Query(None, description="Email of a specific recipient to use for preview"),
    _: str = Depends(get_current_user)
):
    """
    Preview campaign with real recipient data.
    If recipient_email provided, uses that recipient's data.
    Otherwise, uses first recipient in the campaign.
    """
    supabase = get_supabase_client()
    template_service = get_template_service()
    
    # Get campaign
    campaign_result = supabase.table("campaigns").select("*").eq("id", str(campaign_id)).execute()
    
    if not campaign_result.data:
        raise HTTPException(status_code=404, detail="Campaign not found")
    
    campaign = campaign_result.data[0]
    
    # Get recipient data
    if recipient_email:
        recipient_result = (
            supabase.table("recipients")
            .select("*")
            .eq("campaign_id", str(campaign_id))
            .eq("email", recipient_email)
            .limit(1)
            .execute()
        )
    else:
        # Get first recipient
        recipient_result = (
            supabase.table("recipients")
            .select("*")
            .eq("campaign_id", str(campaign_id))
            .limit(1)
            .execute()
        )
    
    if not recipient_result.data:
        raise HTTPException(
            status_code=404,
            detail="No recipients found for this campaign. Import recipients first."
        )
    
    recipient = recipient_result.data[0]
    
    # Build preview data
    unsubscribe_url = f"{settings.app_base_url}/unsubscribe?email={recipient['email']}&campaign_id={campaign_id}"
    
    recipient_data = {
        "firstname": recipient.get("first_name", ""),
        "lastname": recipient.get("last_name", ""),
        "company": recipient.get("company", ""),
        "subject": campaign["subject"],
        "unsubscribe_url": unsubscribe_url,
        **(recipient.get("custom_data", {}))
    }
    
    try:
        html_content = template_service.render(campaign["html_content"], recipient_data)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Template rendering failed: {str(e)}")
    
    return {
        "html_content": html_content,
        "subject": campaign["subject"],
        "from": f"{campaign['from_name']} <{campaign['from_email']}>",
        "reply_to": campaign.get("reply_to", campaign["from_email"]),
        "recipient_data": recipient_data,
        "recipient_email": recipient["email"]
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
async def preview_csv(
    campaign_id: UUID,
    file: UploadFile = File(...),
    _: str = Depends(get_current_user)
):
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
    column_mapping: str = Query(..., description="JSON string with column mapping"),
    _: str = Depends(get_current_user)
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
    background_tasks: BackgroundTasks,
    _: str = Depends(get_current_user)
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


# ============================================
# Campaign Scheduling Endpoints
# ============================================

@router.post("/campaigns/{campaign_id}/schedule", response_model=CampaignScheduleResponse)
async def schedule_campaign(
    campaign_id: UUID,
    request: CampaignScheduleRequest,
    _: str = Depends(get_current_user)
):
    """Schedule a campaign to be sent at a specific time"""
    from core.scheduler import schedule_campaign as do_schedule
    
    supabase = get_supabase_client()
    
    # Get campaign
    campaign_result = supabase.table("campaigns").select("*").eq("id", str(campaign_id)).execute()
    
    if not campaign_result.data:
        raise HTTPException(status_code=404, detail="Campaign not found")
    
    campaign = campaign_result.data[0]
    
    # Validate campaign can be scheduled
    if campaign["status"] not in ["draft", "paused"]:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot schedule campaign with status: {campaign['status']}. Must be 'draft' or 'paused'."
        )
    
    if campaign["total_recipients"] == 0:
        raise HTTPException(status_code=400, detail="Campaign has no recipients. Import recipients before scheduling.")
    
    # Schedule the campaign
    success = await do_schedule(str(campaign_id), request.scheduled_at)
    
    if not success:
        raise HTTPException(status_code=500, detail="Failed to schedule campaign")
    
    return CampaignScheduleResponse(
        campaign_id=campaign_id,
        scheduled_at=request.scheduled_at,
        status="scheduled",
        message=f"Campaign scheduled for {request.scheduled_at.strftime('%d/%m/%Y à %H:%M')}"
    )


@router.delete("/campaigns/{campaign_id}/schedule")
async def cancel_scheduled_campaign(
    campaign_id: UUID,
    _: str = Depends(get_current_user)
):
    """Cancel a scheduled campaign (revert to draft)"""
    from core.scheduler import cancel_scheduled_campaign as do_cancel
    
    supabase = get_supabase_client()
    
    # Check campaign exists and is scheduled
    campaign_result = supabase.table("campaigns").select("status").eq("id", str(campaign_id)).execute()
    
    if not campaign_result.data:
        raise HTTPException(status_code=404, detail="Campaign not found")
    
    if campaign_result.data[0]["status"] != "scheduled":
        raise HTTPException(
            status_code=400,
            detail="Campaign is not scheduled"
        )
    
    success = await do_cancel(str(campaign_id))
    
    if not success:
        raise HTTPException(status_code=500, detail="Failed to cancel scheduled campaign")
    
    return {
        "message": "Scheduled campaign cancelled",
        "campaign_id": campaign_id,
        "status": "draft"
    }


@router.patch("/campaigns/{campaign_id}/schedule", response_model=CampaignScheduleResponse)
async def reschedule_campaign(
    campaign_id: UUID,
    request: CampaignScheduleRequest,
    _: str = Depends(get_current_user)
):
    """Reschedule a campaign to a different time"""
    supabase = get_supabase_client()
    
    # Check campaign exists and is scheduled
    campaign_result = supabase.table("campaigns").select("*").eq("id", str(campaign_id)).execute()
    
    if not campaign_result.data:
        raise HTTPException(status_code=404, detail="Campaign not found")
    
    if campaign_result.data[0]["status"] != "scheduled":
        raise HTTPException(
            status_code=400,
            detail="Campaign is not scheduled. Use POST to schedule first."
        )
    
    # Update scheduled time
    result = (
        supabase.table("campaigns")
        .update({"scheduled_at": request.scheduled_at.isoformat()})
        .eq("id", str(campaign_id))
        .execute()
    )
    
    if not result.data:
        raise HTTPException(status_code=500, detail="Failed to reschedule campaign")
    
    return CampaignScheduleResponse(
        campaign_id=campaign_id,
        scheduled_at=request.scheduled_at,
        status="scheduled",
        message=f"Campaign rescheduled for {request.scheduled_at.strftime('%d/%m/%Y à %H:%M')}"
    )


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


# ============================================
# Tracking Endpoints (Public - No Auth)
# ============================================

@router.get("/track/open")
async def track_email_open(
    c: str = Query(..., description="Campaign ID"),
    r: str = Query(..., description="Recipient ID"),
    t: str = Query(..., description="Tracking token"),
    request: Request = None
):
    """
    Track email open via invisible 1x1 pixel.
    Returns a 1x1 transparent GIF.
    """
    try:
        campaign_id = UUID(c)
        recipient_id = UUID(r)
        
        # Verify tracking token
        if not verify_tracking_token(campaign_id, recipient_id, t):
            logger.warning(f"Invalid tracking token for campaign {c}, recipient {r}")
            return _get_tracking_pixel()
        
        supabase = get_supabase_client()
        webhook_service = get_webhook_service()
        
        # Check if already opened
        recipient_result = supabase.table("recipients").select("opened_at, email").eq("id", str(recipient_id)).execute()
        
        if recipient_result.data and not recipient_result.data[0].get("opened_at"):
            # First time opened - update recipient
            supabase.table("recipients").update({
                "opened_at": "now()"
            }).eq("id", str(recipient_id)).execute()
            
            # Increment campaign opened_count
            supabase.table("campaigns").update({
                "opened_count": supabase.table("campaigns").select("opened_count").eq("id", str(campaign_id)).execute().data[0]["opened_count"] + 1
            }).eq("id", str(campaign_id)).execute()
            
            # Log event
            supabase.table("email_logs").insert({
                "campaign_id": str(campaign_id),
                "recipient_id": str(recipient_id),
                "email": recipient_result.data[0].get("email", ""),
                "event_type": "opened",
                "event_data": {
                    "user_agent": request.headers.get("user-agent") if request else None,
                    "ip": request.client.host if request and request.client else None
                }
            }).execute()
            
            logger.info(f"Email opened: campaign={campaign_id}, recipient={recipient_id}")
            
            # Send webhook notification
            webhook_config = await get_campaign_webhooks(campaign_id)
            if webhook_config:
                await webhook_service.notify_email_opened(
                    campaign_id=campaign_id,
                    recipient_id=recipient_id,
                    email=recipient_result.data[0].get("email", ""),
                    webhook_url=webhook_config.get("url"),
                    secret=webhook_config.get("secret")
                )
    
    except Exception as e:
        logger.error(f"Error tracking open: {str(e)}")
    
    # Always return pixel, even on error
    return _get_tracking_pixel()


@router.get("/track/click")
async def track_email_click(
    c: str = Query(..., description="Campaign ID"),
    r: str = Query(..., description="Recipient ID"),
    t: str = Query(..., description="Tracking token"),
    u: str = Query(..., description="Original URL"),
    request: Request = None
):
    """
    Track email click and redirect to original URL.
    Wrapped links in emails will redirect through this endpoint.
    """
    supabase = get_supabase_client()
    webhook_service = get_webhook_service()
    
    try:
        campaign_id = UUID(c)
        recipient_id = UUID(r)
        
        # Verify token
        if not verify_tracking_token(c, r, t):
            logger.warning(f"Invalid tracking token for click: campaign={c}, recipient={r}")
            return RedirectResponse(url=u)
        
        # Check if already clicked
        recipient_result = supabase.table("recipients").select("clicked_at, email").eq("id", str(recipient_id)).execute()
        
        if recipient_result.data:
            first_click = not recipient_result.data[0].get("clicked_at")
            
            if first_click:
                # First time clicked - update recipient
                supabase.table("recipients").update({
                    "clicked_at": "now()"
                }).eq("id", str(recipient_id)).execute()
                
                # Increment campaign clicked_count
                campaign_data = supabase.table("campaigns").select("clicked_count").eq("id", str(campaign_id)).execute()
                if campaign_data.data:
                    supabase.table("campaigns").update({
                        "clicked_count": campaign_data.data[0]["clicked_count"] + 1
                    }).eq("id", str(campaign_id)).execute()
                
                # Send webhook notification for first click
                webhook_config = await get_campaign_webhooks(campaign_id)
                if webhook_config:
                    await webhook_service.notify_email_clicked(
                        campaign_id=campaign_id,
                        recipient_id=recipient_id,
                        email=recipient_result.data[0].get("email", ""),
                        url=u,
                        webhook_config=webhook_config
                    )
            
            # Log event (log all clicks, not just first)
            supabase.table("email_logs").insert({
                "campaign_id": str(campaign_id),
                "recipient_id": str(recipient_id),
                "email": recipient_result.data[0].get("email", ""),
                "event_type": "clicked",
                "event_data": {
                    "url": u,
                    "user_agent": request.headers.get("user-agent") if request else None,
                    "ip": request.client.host if request and request.client else None
                }
            }).execute()
            
            logger.info(f"Email clicked: campaign={campaign_id}, recipient={recipient_id}, url={u}")
    
    except Exception as e:
        logger.error(f"Error tracking click: {str(e)}")
    
    # Always redirect to original URL
    return RedirectResponse(url=u)


def _get_tracking_pixel():
    """Return a 1-pixel transparent GIF"""
    # Base64 encoded 1x1 transparent GIF
    pixel_data = (
        b'\x47\x49\x46\x38\x39\x61\x01\x00\x01\x00\x80\x00\x00'
        b'\xff\xff\xff\x00\x00\x00\x21\xf9\x04\x01\x00\x00\x00'
        b'\x00\x2c\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02'
        b'\x44\x01\x00\x3b'
    )
    
    return Response(
        content=pixel_data,
        media_type="image/gif",
        headers={
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "Pragma": "no-cache",
            "Expires": "0"
        }
    )


# ============================================
# DNS Validation Endpoints
# ============================================

@router.get("/validate-domain/{domain}")
async def validate_email_domain(
    domain: str,
    _: str = Depends(get_current_user)
):
    """
    Validate DNS configuration for email sending domain.
    Checks SPF, DKIM, DMARC, and MX records.
    """
    validator = get_dns_validator()
    
    try:
        report = validator.validate_domain_full(domain)
        return report
    except Exception as e:
        logger.error(f"Domain validation error for {domain}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to validate domain: {str(e)}"
        )

