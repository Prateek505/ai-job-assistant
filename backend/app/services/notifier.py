"""
Notification service — sends emails via SendGrid.
Falls back to console logging when no API key is configured.
"""

import logging
from ..config import settings

logger = logging.getLogger(__name__)


async def send_email_notification(to_email: str, subject: str, body: str) -> bool:
    """
    Send an email notification.
    Uses SendGrid if API key is available, otherwise logs to console.
    """
    if settings.SENDGRID_API_KEY:
        return _send_via_sendgrid(to_email, subject, body)
    return _log_fallback(to_email, subject, body)


def _send_via_sendgrid(to_email: str, subject: str, body: str) -> bool:
    """Send email using SendGrid API."""
    try:
        from sendgrid import SendGridAPIClient
        from sendgrid.helpers.mail import Mail

        message = Mail(
            from_email=settings.SENDGRID_FROM_EMAIL,
            to_emails=to_email,
            subject=subject,
            html_content=body,
        )
        sg = SendGridAPIClient(settings.SENDGRID_API_KEY)
        response = sg.send(message)
        logger.info(f"Email sent to {to_email}: status {response.status_code}")
        return response.status_code in (200, 201, 202)
    except Exception as e:
        logger.error(f"SendGrid error: {e}")
        return False


def _log_fallback(to_email: str, subject: str, body: str) -> bool:
    """Log email to console when SendGrid is not configured."""
    logger.info(
        f"[EMAIL STUB] To: {to_email} | Subject: {subject} | Body: {body[:200]}..."
    )
    print(f"\n📧 Email Notification (stub):\n  To: {to_email}\n  Subject: {subject}\n  Body: {body[:200]}...\n")
    return True
