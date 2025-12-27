"""Email service for sending invoices"""
import aiosmtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from typing import Optional
from app.core.config import settings


class EmailService:
    """Service for sending emails"""
    
    @staticmethod
    async def send_invoice_email(
        to_email: str,
        subject: str,
        body_html: str,
        pdf_attachment: Optional[bytes] = None,
        pdf_filename: str = "invoice.pdf"
    ) -> bool:
        """
        Send an invoice email with optional PDF attachment
        
        Args:
            to_email: Recipient email address
            subject: Email subject
            body_html: HTML body content
            pdf_attachment: PDF file content as bytes
            pdf_filename: Name for the PDF attachment
            
        Returns:
            True if email sent successfully, False otherwise
        """
        if not settings.SMTP_HOST or not settings.SMTP_FROM_EMAIL:
            raise ValueError("Email configuration is not set")
        
        # Create message
        message = MIMEMultipart()
        message["From"] = settings.SMTP_FROM_EMAIL
        message["To"] = to_email
        message["Subject"] = subject
        
        # Add HTML body
        html_part = MIMEText(body_html, "html")
        message.attach(html_part)
        
        # Add PDF attachment if provided
        if pdf_attachment:
            pdf_part = MIMEApplication(pdf_attachment, _subtype="pdf")
            pdf_part.add_header("Content-Disposition", "attachment", filename=pdf_filename)
            message.attach(pdf_part)
        
        try:
            # Send email
            await aiosmtplib.send(
                message,
                hostname=settings.SMTP_HOST,
                port=settings.SMTP_PORT,
                username=settings.SMTP_USER,
                password=settings.SMTP_PASSWORD,
                start_tls=True
            )
            return True
        except Exception as e:
            print(f"Failed to send email: {e}")
            return False
