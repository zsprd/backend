import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Optional

from app.core.config import settings

logger = logging.getLogger(__name__)


class EmailService:
    """
    Email service for sending verification and password reset emails.
    Currently configured for Gmail SMTP for development.
    """

    def __init__(self):
        # Email configuration (add these to your .env file)
        self.smtp_server = settings.SMTP_HOST
        self.smtp_port = settings.SMTP_PORT
        self.smtp_username = settings.SMTP_USERNAME
        self.smtp_password = settings.SMTP_PASSWORD
        self.from_email = settings.FROM_EMAIL
        self.from_name = settings.FROM_NAME

        # Frontend URL for links
        self.frontend_url = settings.FRONTEND_URL

    def send_email(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        text_content: Optional[str] = None,
    ) -> bool:
        """
        Send an email with both HTML and text content.

        Args:
            to_email: Recipient email address
            subject: Email subject
            html_content: HTML email content
            text_content: Plain text email content (optional)

        Returns:
            bool: True if email sent successfully, False otherwise
        """
        try:
            # Create message
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = f"{self.from_name} <{self.from_email}>"
            msg["To"] = to_email

            # Add text content if provided
            if text_content:
                text_part = MIMEText(text_content, "plain")
                msg.attach(text_part)

            # Add HTML content
            html_part = MIMEText(html_content, "html")
            msg.attach(html_part)

            # Send email
            if not self.smtp_server or not self.smtp_port:
                raise ValueError("SMTP server and port must be set in the configuration.")
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                if self.smtp_username and self.smtp_password:
                    server.login(self.smtp_username, self.smtp_password)
                server.send_message(msg)

            logger.info(f"Email sent successfully to {to_email}")
            return True

        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {str(e)}")
            return False

    def get_verification_email_template(self, name: str, verification_link: str) -> tuple[str, str]:
        """
        Get email verification template.

        Returns:
            tuple: (html_content, text_content)
        """
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>Verify Your Email - ZSPRD Portfolio Analytics</title>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: #1976d2; color: white; padding: 20px; text-align: center; }}
                .content {{ padding: 30px 20px; background: #f9f9f9; }}
                .button {{ 
                    display: inline-block; 
                    background: #1976d2; 
                    color: white; 
                    padding: 12px 30px; 
                    text-decoration: none; 
                    border-radius: 5px; 
                    margin: 20px 0;
                }}
                .footer {{ padding: 20px; text-align: center; color: #666; font-size: 12px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🎯 ZSPRD Portfolio Analytics</h1>
                </div>
                <div class="content">
                    <h2>Welcome, {name}!</h2>
                    <p>Thank you for signing up for ZSPRD Portfolio Analytics. To complete your registration and start tracking your investments, please verify your email address.</p>
                    
                    <p style="text-align: center;">
                        <a href="{verification_link}" class="button">Verify My Email</a>
                    </p>
                    
                    <p>If the button above doesn't work, copy and paste this link into your browser:</p>
                    <p style="word-break: break-all; background: #f0f0f0; padding: 10px; border-radius: 3px;">
                        {verification_link}
                    </p>
                    
                    <p><strong>This link will expire in 24 hours.</strong></p>
                    
                    <p>If you didn't create an account with us, please ignore this email.</p>
                </div>
                <div class="footer">
                    <p>ZSPRD Portfolio Analytics - Professional Investment Analytics</p>
                    <p>This is an automated message, please do not reply to this email.</p>
                </div>
            </div>
        </body>
        </html>
        """

        text_content = f"""
        Welcome to ZSPRD Portfolio Analytics!
        
        Hi {name},
        
        Thank you for signing up for ZSPRD Portfolio Analytics. To complete your registration and start tracking your investments, please verify your email address.
        
        Click this link to verify your email:
        {verification_link}
        
        This link will expire in 24 hours.
        
        If you didn't create an account with us, please ignore this email.
        
        --
        ZSPRD Portfolio Analytics Team
        """

        return html_content, text_content

    def get_password_reset_email_template(self, name: str, reset_link: str) -> tuple[str, str]:
        """
        Get password reset email template.

        Returns:
            tuple: (html_content, text_content)
        """
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>Reset Your Password - ZSPRD Portfolio Analytics</title>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: #d32f2f; color: white; padding: 20px; text-align: center; }}
                .content {{ padding: 30px 20px; background: #f9f9f9; }}
                .button {{ 
                    display: inline-block; 
                    background: #d32f2f; 
                    color: white;
                    padding: 12px 30px; 
                    text-decoration: none; 
                    border-radius: 5px; 
                    margin: 20px 0;
                }}
                .footer {{ padding: 20px; text-align: center; color: #666; font-size: 12px; }}
                .warning {{ background: #fff3cd; border: 1px solid #ffeaa7; padding: 15px; border-radius: 5px; margin: 15px 0; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🔐 Password Reset Request</h1>
                </div>
                <div class="content">
                    <h2>Hi {name},</h2>
                    <p>We received a request to reset your password for your ZSPRD Portfolio Analytics account.</p>
                    
                    <p style="text-align: center;">
                        <a href="{reset_link}" class="button">Reset My Password</a>
                    </p>
                    
                    <p>If the button above doesn't work, copy and paste this link into your browser:</p>
                    <p style="word-break: break-all; background: #f0f0f0; padding: 10px; border-radius: 3px;">
                        {reset_link}
                    </p>
                    
                    <div class="warning">
                        <strong>⚠️ Security Notice:</strong>
                        <ul>
                            <li>This link will expire in 1 hour for your security</li>
                            <li>If you didn't request this reset, please ignore this email</li>
                            <li>Your password will remain unchanged unless you click the link above</li>
                        </ul>
                    </div>
                </div>
                <div class="footer">
                    <p>ZSPRD Portfolio Analytics - Professional Investment Analytics</p>
                    <p>This is an automated message, please do not reply to this email.</p>
                </div>
            </div>
        </body>
        </html>
        """

        text_content = f"""
        Password Reset Request - ZSPRD Portfolio Analytics
        
        Hi {name},
        
        We received a request to reset your password for your ZSPRD Portfolio Analytics account.
        
        Click this link to reset your password:
        {reset_link}
        
        SECURITY NOTICE:
        - This link will expire in 1 hour for your security
        - If you didn't request this reset, please ignore this email
        - Your password will remain unchanged unless you click the link above
        
        --
        ZSPRD Portfolio Analytics Team
        """

        return html_content, text_content


# Create email service instance
email_service = EmailService()


# Convenience functions for the auth endpoints
async def send_verification_email(email: str, name: str, token: str) -> bool:
    """
    Send email verification email.

    Args:
        email: UserProfile's email address
        name: UserProfile's name
        token: Verification token

    Returns:
        bool: True if email sent successfully
    """
    verification_link = f"{email_service.frontend_url}/auth/confirm?token={token}"

    html_content, text_content = email_service.get_verification_email_template(
        name=name, verification_link=verification_link
    )

    return email_service.send_email(
        to_email=email,
        subject="Please verify your email - ZSPRD Portfolio Analytics",
        html_content=html_content,
        text_content=text_content,
    )


async def send_password_reset_email(email: str, name: str, token: str) -> bool:
    """
    Send password reset email.

    Args:
        email: UserProfile's email address
        name: UserProfile's name
        token: Password reset token

    Returns:
        bool: True if email sent successfully
    """
    reset_link = f"{email_service.frontend_url}/auth/reset-password?token={token}"

    html_content, text_content = email_service.get_password_reset_email_template(
        name=name, reset_link=reset_link
    )

    return email_service.send_email(
        to_email=email,
        subject="Reset your password - ZSPRD Portfolio Analytics",
        html_content=html_content,
        text_content=text_content,
    )


async def send_welcome_email(email: str, name: str) -> bool:
    """
    Send welcome email after email verification.

    Args:
        email: UserProfile's email address
        name: UserProfile's name

    Returns:
        bool: True if email sent successfully
    """
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <title>Welcome to ZSPRD Portfolio Analytics</title>
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
            .header {{ background: #4caf50; color: white; padding: 20px; text-align: center; }}
            .content {{ padding: 30px 20px; background: #f9f9f9; }}
            .button {{ 
                display: inline-block; 
                background: #1976d2; 
                color: white; 
                padding: 12px 30px; 
                text-decoration: none; 
                border-radius: 5px; 
                margin: 20px 0;
            }}
            .footer {{ padding: 20px; text-align: center; color: #666; font-size: 12px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🎉 Welcome to ZSPRD!</h1>
            </div>
            <div class="content">
                <h2>Congratulations, {name}!</h2>
                <p>Your email has been verified and your ZSPRD Portfolio Analytics account is now active.</p>
                
                <p>You can now start:</p>
                <ul>
                    <li>📊 Tracking your investment portfolios</li>
                    <li>📈 Analyzing performance metrics</li>
                    <li>🎯 Setting up portfolios alerts</li>
                    <li>📋 Generating professional reports</li>
                </ul>
                
                <p style="text-align: center;">
                    <a href="{email_service.frontend_url}/dashboard" class="button">Go to Dashboard</a>
                </p>
                
                <p>Need help getting started? Check out our <a href="{email_service.frontend_url}/help">help center</a> or reach out to our support team.</p>
            </div>
            <div class="footer">
                <p>ZSPRD Portfolio Analytics - Professional Investment Analytics</p>
                <p>This is an automated message, please do not reply to this email.</p>
            </div>
        </div>
    </body>
    </html>
    """

    return email_service.send_email(
        to_email=email,
        subject="Welcome to ZSPRD Portfolio Analytics! 🎉",
        html_content=html_content,
    )
