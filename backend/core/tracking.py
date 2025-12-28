"""
Email Tracking Service
Handles open tracking (pixel) and click tracking (URL wrapping)
"""

import hashlib
import logging
import re
from typing import Optional
from urllib.parse import urlencode, quote
from uuid import UUID

from core.config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)


def generate_tracking_token(campaign_id: UUID, recipient_id: UUID) -> str:
    """
    Generate a unique tracking token for a campaign-recipient pair.
    Uses HMAC-like approach for security.
    """
    data = f"{campaign_id}:{recipient_id}:{settings.jwt_secret}"
    return hashlib.sha256(data.encode()).hexdigest()[:32]


def verify_tracking_token(campaign_id: UUID, recipient_id: UUID, token: str) -> bool:
    """Verify a tracking token is valid"""
    expected = generate_tracking_token(campaign_id, recipient_id)
    return token == expected


def get_tracking_pixel_url(campaign_id: UUID, recipient_id: UUID) -> str:
    """
    Generate tracking pixel URL for email opens.
    
    Returns URL like: https://api.example.com/v1/track/open?c=xxx&r=xxx&t=xxx
    """
    token = generate_tracking_token(campaign_id, recipient_id)
    params = {
        "c": str(campaign_id),
        "r": str(recipient_id),
        "t": token
    }
    return f"{settings.api_base_url}/v1/track/open?{urlencode(params)}"


def get_tracking_pixel_html(campaign_id: UUID, recipient_id: UUID) -> str:
    """
    Generate HTML for 1x1 invisible tracking pixel.
    Should be inserted at the end of email body.
    """
    url = get_tracking_pixel_url(campaign_id, recipient_id)
    return f'<img src="{url}" width="1" height="1" alt="" style="display:none;" />'


def wrap_url_for_tracking(
    original_url: str,
    campaign_id: UUID,
    recipient_id: UUID
) -> str:
    """
    Wrap a URL for click tracking.
    
    Original: https://example.com/page
    Wrapped: https://api.example.com/v1/track/click?c=xxx&r=xxx&t=xxx&u=https%3A%2F%2Fexample.com%2Fpage
    """
    token = generate_tracking_token(campaign_id, recipient_id)
    params = {
        "c": str(campaign_id),
        "r": str(recipient_id),
        "t": token,
        "u": original_url
    }
    return f"{settings.api_base_url}/v1/track/click?{urlencode(params)}"


def inject_tracking_into_html(
    html_content: str,
    campaign_id: UUID,
    recipient_id: UUID,
    enable_click_tracking: bool = True,
    enable_open_tracking: bool = True
) -> str:
    """
    Inject tracking into HTML email:
    1. Wrap all <a href="..."> links with tracking redirects
    2. Add tracking pixel before </body> tag
    
    Args:
        html_content: Original HTML content
        campaign_id: Campaign UUID
        recipient_id: Recipient UUID
        enable_click_tracking: Whether to track clicks
        enable_open_tracking: Whether to track opens
    
    Returns:
        Modified HTML with tracking injected
    """
    modified_html = html_content
    
    # 1. Wrap links for click tracking
    if enable_click_tracking:
        # Find all href attributes and wrap them
        def wrap_link(match):
            full_tag = match.group(0)
            url = match.group(1)
            
            # Skip mailto:, tel:, javascript:, #anchors, and unsubscribe links
            if (url.startswith(('mailto:', 'tel:', 'javascript:', '#')) or
                'unsubscribe' in url.lower() or
                'track/click' in url):  # Don't double-wrap
                return full_tag
            
            # Wrap the URL
            tracked_url = wrap_url_for_tracking(url, campaign_id, recipient_id)
            return full_tag.replace(url, tracked_url, 1)
        
        # Match href="..." and href='...'
        modified_html = re.sub(
            r'href=["\']([^"\']+)["\']',
            wrap_link,
            modified_html
        )
    
    # 2. Add tracking pixel for opens
    if enable_open_tracking:
        tracking_pixel = get_tracking_pixel_html(campaign_id, recipient_id)
        
        # Try to insert before </body>
        if '</body>' in modified_html.lower():
            modified_html = re.sub(
                r'</body>',
                f'{tracking_pixel}</body>',
                modified_html,
                count=1,
                flags=re.IGNORECASE
            )
        # If no </body>, append to end
        else:
            modified_html += tracking_pixel
    
    return modified_html


def extract_url_from_tracking_link(tracking_url: str) -> Optional[str]:
    """Extract original URL from tracking redirect URL"""
    from urllib.parse import urlparse, parse_qs
    
    parsed = urlparse(tracking_url)
    params = parse_qs(parsed.query)
    
    if 'u' in params:
        return params['u'][0]
    
    return None
