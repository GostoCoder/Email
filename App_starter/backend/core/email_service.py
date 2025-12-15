"""
Email Provider Service
Abstraction layer for sending emails via multiple providers (SendGrid, Mailgun, AWS SES)
"""

import asyncio
import logging
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from core.config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)


class EmailMessage:
    """Email message structure"""
    
    def __init__(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        from_email: str,
        from_name: str,
        reply_to: Optional[str] = None,
        custom_args: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None
    ):
        self.to_email = to_email
        self.subject = subject
        self.html_content = html_content
        self.from_email = from_email
        self.from_name = from_name
        self.reply_to = reply_to or from_email
        self.custom_args = custom_args or {}
        self.headers = headers or {}


class EmailProviderBase(ABC):
    """Base class for email providers"""
    
    @abstractmethod
    async def send_email(self, message: EmailMessage) -> Dict[str, Any]:
        """Send a single email"""
        pass
    
    @abstractmethod
    async def send_batch(self, messages: List[EmailMessage]) -> List[Dict[str, Any]]:
        """Send multiple emails"""
        pass


class SendGridProvider(EmailProviderBase):
    """SendGrid email provider"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        try:
            from sendgrid import SendGridAPIClient
            from sendgrid.helpers.mail import Mail, Header
            self.sg_client = SendGridAPIClient(api_key)
            self.Mail = Mail
            self.Header = Header
        except ImportError:
            raise ImportError("SendGrid library not installed. Run: pip install sendgrid")
    
    async def send_email(self, message: EmailMessage) -> Dict[str, Any]:
        """Send email via SendGrid"""
        try:
            mail = self.Mail(
                from_email=(message.from_email, message.from_name),
                to_emails=message.to_email,
                subject=message.subject,
                html_content=message.html_content
            )
            
            # Add reply-to
            if message.reply_to:
                mail.reply_to = message.reply_to
            
            # Add custom headers (including List-Unsubscribe)
            if message.headers:
                for key, value in message.headers.items():
                    mail.add_header(self.Header(key, value))
            
            # Add custom args for tracking
            if message.custom_args:
                for key, value in message.custom_args.items():
                    mail.add_custom_arg(key, str(value))
            
            response = self.sg_client.send(mail)
            
            return {
                "success": True,
                "provider": "sendgrid",
                "status_code": response.status_code,
                "message_id": response.headers.get("X-Message-Id"),
                "to_email": message.to_email
            }
        except Exception as e:
            logger.error(f"SendGrid error: {str(e)}")
            return {
                "success": False,
                "provider": "sendgrid",
                "error": str(e),
                "to_email": message.to_email
            }
    
    async def send_batch(self, messages: List[EmailMessage]) -> List[Dict[str, Any]]:
        """Send batch of emails via SendGrid"""
        tasks = [self.send_email(msg) for msg in messages]
        return await asyncio.gather(*tasks)


class MailgunProvider(EmailProviderBase):
    """Mailgun email provider"""
    
    def __init__(self, api_key: str, domain: str):
        self.api_key = api_key
        self.domain = domain
        self.base_url = f"https://api.mailgun.net/v3/{domain}/messages"
    
    async def send_email(self, message: EmailMessage) -> Dict[str, Any]:
        """Send email via Mailgun"""
        try:
            import httpx
            
            data = {
                "from": f"{message.from_name} <{message.from_email}>",
                "to": message.to_email,
                "subject": message.subject,
                "html": message.html_content,
                "h:Reply-To": message.reply_to
            }
            
            # Add custom headers
            if message.headers:
                for key, value in message.headers.items():
                    data[f"h:{key}"] = value
            
            # Add custom variables
            if message.custom_args:
                for key, value in message.custom_args.items():
                    data[f"v:{key}"] = str(value)
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.base_url,
                    auth=("api", self.api_key),
                    data=data,
                    timeout=30.0
                )
                
                result = response.json()
                
                return {
                    "success": response.status_code == 200,
                    "provider": "mailgun",
                    "status_code": response.status_code,
                    "message_id": result.get("id"),
                    "to_email": message.to_email
                }
        except Exception as e:
            logger.error(f"Mailgun error: {str(e)}")
            return {
                "success": False,
                "provider": "mailgun",
                "error": str(e),
                "to_email": message.to_email
            }
    
    async def send_batch(self, messages: List[EmailMessage]) -> List[Dict[str, Any]]:
        """Send batch of emails via Mailgun"""
        tasks = [self.send_email(msg) for msg in messages]
        return await asyncio.gather(*tasks)


class EmailService:
    """
    Main email service with rate limiting and batch processing
    """
    
    def __init__(self):
        self.provider = self._initialize_provider()
        self.rate_limit_per_second = settings.email_rate_limit_per_second
        self.batch_size = settings.email_batch_size
        self._last_send_time = 0
    
    def _initialize_provider(self) -> EmailProviderBase:
        """Initialize the configured email provider"""
        provider_name = settings.email_provider.lower()
        
        if provider_name == "sendgrid":
            if not settings.sendgrid_api_key:
                raise ValueError("SendGrid API key not configured")
            return SendGridProvider(settings.sendgrid_api_key)
        
        elif provider_name == "mailgun":
            if not settings.mailgun_api_key or not settings.mailgun_domain:
                raise ValueError("Mailgun API key or domain not configured")
            return MailgunProvider(settings.mailgun_api_key, settings.mailgun_domain)
        
        else:
            raise ValueError(f"Unsupported email provider: {provider_name}")
    
    async def _apply_rate_limit(self):
        """Apply rate limiting between sends"""
        if self.rate_limit_per_second > 0:
            delay = 1.0 / self.rate_limit_per_second
            await asyncio.sleep(delay)
    
    async def send_single(self, message: EmailMessage) -> Dict[str, Any]:
        """Send a single email with rate limiting"""
        await self._apply_rate_limit()
        return await self.provider.send_email(message)
    
    async def send_batch(
        self,
        messages: List[EmailMessage],
        on_progress: Optional[callable] = None
    ) -> List[Dict[str, Any]]:
        """
        Send emails in batches with rate limiting and progress tracking
        
        Args:
            messages: List of email messages to send
            on_progress: Callback function called after each batch (sent_count, total_count)
        
        Returns:
            List of send results
        """
        results = []
        total = len(messages)
        
        for i in range(0, total, self.batch_size):
            batch = messages[i:i + self.batch_size]
            
            # Send batch with rate limiting
            batch_results = []
            for msg in batch:
                result = await self.send_single(msg)
                batch_results.append(result)
            
            results.extend(batch_results)
            
            # Call progress callback
            if on_progress:
                await on_progress(len(results), total)
            
            logger.info(f"Sent batch {i // self.batch_size + 1}: {len(batch_results)} emails")
        
        return results
    
    def build_unsubscribe_headers(self, unsubscribe_url: str, campaign_email: str) -> Dict[str, str]:
        """
        Build List-Unsubscribe headers for email clients
        
        These headers enable one-click unsubscribe in email clients like Gmail
        """
        return {
            "List-Unsubscribe": f"<{unsubscribe_url}>, <mailto:{campaign_email}?subject=unsubscribe>",
            "List-Unsubscribe-Post": "List-Unsubscribe=One-Click"
        }


# Global email service instance
_email_service: Optional[EmailService] = None


def get_email_service() -> EmailService:
    """Get or create email service singleton"""
    global _email_service
    if _email_service is None:
        _email_service = EmailService()
    return _email_service
