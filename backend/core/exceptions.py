"""
Custom exceptions for the email campaign application
"""

from fastapi import HTTPException, status


class CampaignNotFoundError(HTTPException):
    """Campaign not found"""
    def __init__(self, campaign_id: str):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Campaign with ID {campaign_id} not found"
        )


class RecipientNotFoundError(HTTPException):
    """Recipient not found"""
    def __init__(self, recipient_id: str):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Recipient with ID {recipient_id} not found"
        )


class TemplateNotFoundError(HTTPException):
    """Template not found"""
    def __init__(self, template_id: str):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Template with ID {template_id} not found"
        )


class InvalidCampaignStatusError(HTTPException):
    """Invalid campaign status for operation"""
    def __init__(self, current_status: str, allowed_statuses: list):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot perform operation on campaign with status '{current_status}'. "
                   f"Allowed statuses: {', '.join(allowed_statuses)}"
        )


class EmailAlreadyUnsubscribedError(HTTPException):
    """Email address is already unsubscribed"""
    def __init__(self, email: str):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Email address {email} is already unsubscribed"
        )


class InvalidEmailFormatError(HTTPException):
    """Invalid email format"""
    def __init__(self, email: str):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid email format: {email}"
        )


class CSVImportError(HTTPException):
    """Error during CSV import"""
    def __init__(self, message: str):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"CSV import failed: {message}"
        )


class EmailProviderError(HTTPException):
    """Error with email provider"""
    def __init__(self, provider: str, message: str):
        super().__init__(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Email provider '{provider}' error: {message}"
        )


class TemplateRenderError(HTTPException):
    """Error rendering email template"""
    def __init__(self, message: str):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Template rendering failed: {message}"
        )


class RateLimitExceededError(HTTPException):
    """Rate limit exceeded"""
    def __init__(self, retry_after: int = 60):
        super().__init__(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded. Please try again later.",
            headers={"Retry-After": str(retry_after)}
        )


class InsufficientPermissionsError(HTTPException):
    """Insufficient permissions"""
    def __init__(self, action: str):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Insufficient permissions to {action}"
        )
