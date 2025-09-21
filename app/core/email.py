import logging
import os
from typing import Dict, Optional

from fastapi_mail import ConnectionConfig, FastMail, MessageSchema, MessageType
from jinja2 import Environment, FileSystemLoader, select_autoescape
from pydantic import EmailStr

from app.core.config import settings

logger = logging.getLogger(__name__)

# ----------------------------
# Jinja2 template setup
# ----------------------------
TEMPLATE_DIR = os.path.join(os.path.dirname(__file__), "..", "templates", "emails")
jinja_env = Environment(
    loader=FileSystemLoader(TEMPLATE_DIR),
    autoescape=select_autoescape(["html", "xml"]),
)

# ----------------------------
# Mail config
# ----------------------------
conf = ConnectionConfig(
    MAIL_USERNAME=settings.MAIL_USERNAME,
    MAIL_PASSWORD=settings.MAIL_PASSWORD,
    MAIL_PORT=settings.MAIL_PORT,
    MAIL_SERVER=settings.MAIL_SERVER,
    MAIL_STARTTLS=settings.MAIL_STARTTLS,
    MAIL_SSL_TLS=settings.MAIL_SSL_TLS,
    MAIL_FROM=settings.MAIL_FROM,
    MAIL_FROM_NAME=settings.MAIL_FROM_NAME,
    MAIL_DEBUG=0,
)


# ----------------------------
# Core send_email function
# ----------------------------
async def send_email(
    to_email: EmailStr,
    subject: str,
    template: str,
    context: Optional[Dict] = None,
):
    """
    Render Jinja2 template and send an email.
    :param to_email: recipient
    :param subject: subject line
    :param template: template filename (e.g. 'email_verification.html')
    :param context: variables for the template
    """
    try:
        # Render template
        template_obj = jinja_env.get_template(template)
        html_content = template_obj.render(**(context or {}))

        # Build message
        message = MessageSchema(
            subject=subject,
            recipients=[to_email],
            body=html_content,
            subtype=MessageType.html,
        )

        fm = FastMail(conf)
        await fm.send_message(message)

        logger.info(f"Email '{subject}' sent to {to_email}")
        return True

    except Exception as e:
        logger.error(f"Failed to send email '{subject}' to {to_email}: {str(e)}")
        return False


# ----------------------------
# Convenience wrappers
# ----------------------------
async def send_verification_email(
    to_email: EmailStr, verification_url: str, name: Optional[str] = None
):
    return await send_email(
        to_email=to_email,
        subject="Verify your email address",
        template="email_verification.html",
        context={
            "verification_url": verification_url,
            "name": name or "User",
            "expires_in_hours": settings.EMAIL_VERIFICATION_EXPIRE_HOURS,
        },
    )


async def send_password_reset_email(to_email: EmailStr, reset_url: str, name: Optional[str] = None):
    return await send_email(
        to_email=to_email,
        subject="Reset your password",
        template="password_reset.html",
        context={
            "reset_url": reset_url,
            "name": name or "User",
            "expires_in_minutes": settings.PASSWORD_RESET_EXPIRE_MINUTES,
        },
    )


async def send_password_changed_email(to_email: EmailStr, name: Optional[str] = None):
    return await send_email(
        to_email=to_email,
        subject="Your password has been changed",
        template="password_changed.html",
        context={"name": name or "User"},
    )


async def send_welcome_email(to_email: EmailStr, name: Optional[str] = None):
    return await send_email(
        to_email=to_email,
        subject="Welcome to ZSPRD Portfolio Analytics 🎉",
        template="welcome.html",
        context={
            "name": name or "User",
            "frontend_url": settings.FRONTEND_URL,
        },
    )
