"""Invoice service for generating and sending invoices"""
from sqlalchemy.orm import Session
from typing import Optional
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_RIGHT
from decimal import Decimal
from datetime import datetime

from app.repositories.invoice import InvoiceTemplateRepository
from app.repositories.order import OrderRepository
from app.services.email_service import EmailService
from app.schemas.invoice import InvoiceTemplateCreate, InvoiceTemplateUpdate, InvoiceTemplateResponse
from app.models.invoice import InvoiceTemplate
from app.models.order import Order
from app.core.config import settings


class InvoiceService:
    """Service for invoice template management and invoice generation"""
    
    def __init__(self, db: Session):
        self.db = db
        self.repository = InvoiceTemplateRepository(db)
        self.order_repository = OrderRepository(db)
        self.email_service = EmailService()
    
    def create_template(self, template_data: InvoiceTemplateCreate) -> InvoiceTemplateResponse:
        """Create a new invoice template"""
        template = self.repository.create(template_data)
        return InvoiceTemplateResponse.model_validate(template)
    
    def get_template(self, template_id: str) -> Optional[InvoiceTemplateResponse]:
        """Get an invoice template by ID"""
        template = self.repository.get_by_id(template_id)
        if not template:
            return None
        return InvoiceTemplateResponse.model_validate(template)
    
    def get_all_templates(self) -> list[InvoiceTemplateResponse]:
        """Get all invoice templates"""
        templates = self.repository.get_all()
        return [InvoiceTemplateResponse.model_validate(t) for t in templates]
    
    def get_default_template(self) -> Optional[InvoiceTemplateResponse]:
        """Get the default invoice template"""
        template = self.repository.get_default()
        if not template:
            return None
        return InvoiceTemplateResponse.model_validate(template)
    
    def update_template(self, template_id: str, template_data: InvoiceTemplateUpdate) -> Optional[InvoiceTemplateResponse]:
        """Update an invoice template"""
        template = self.repository.update(template_id, template_data)
        if not template:
            return None
        return InvoiceTemplateResponse.model_validate(template)
    
    def delete_template(self, template_id: str) -> bool:
        """Delete an invoice template"""
        return self.repository.delete(template_id)
    
    def generate_invoice_pdf(self, order_id: str) -> Optional[bytes]:
        """
        Generate a PDF invoice for an order
        
        Args:
            order_id: The order ID
            
        Returns:
            PDF content as bytes, or None if order not found
        """
        order = self.order_repository.get_by_id(order_id)
        if not order:
            return None
        
        # Create PDF in memory
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        elements = []
        
        # Styles
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor(settings.BRAND_COLOR_PRIMARY),
            alignment=TA_CENTER,
            spaceAfter=30
        )
        
        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=14,
            textColor=colors.HexColor(settings.BRAND_COLOR_PRIMARY),
            spaceAfter=12
        )
        
        # Title
        elements.append(Paragraph("INVOICE", title_style))
        elements.append(Spacer(1, 0.2 * inch))
        
        # Invoice details
        invoice_data = [
            ["Invoice Number:", order.order_number],
            ["Invoice Date:", datetime.now().strftime("%Y-%m-%d")],
            ["Order Date:", order.order_date.strftime("%Y-%m-%d")],
            ["Status:", order.status.value.replace("_", " ").title()],
        ]
        
        invoice_table = Table(invoice_data, colWidths=[2*inch, 3*inch])
        invoice_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor(settings.BRAND_COLOR_DARK)),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        elements.append(invoice_table)
        elements.append(Spacer(1, 0.3 * inch))
        
        # Customer information
        elements.append(Paragraph("Bill To:", heading_style))
        customer_data = [
            ["Name:", order.customer.name],
            ["Email:", order.customer.email or "N/A"],
            ["Phone:", order.customer.phone or "N/A"],
            ["Address:", f"{order.customer.address or ''}, {order.customer.city or ''}"],
        ]
        
        customer_table = Table(customer_data, colWidths=[1.5*inch, 4*inch])
        customer_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        elements.append(customer_table)
        elements.append(Spacer(1, 0.3 * inch))
        
        # Order items
        elements.append(Paragraph("Order Items:", heading_style))
        
        items_data = [["Item", "Quantity", "Unit Price", "Discount", "Total"]]
        for item in order.items:
            items_data.append([
                item.product_name,
                str(item.quantity),
                f"LKR {item.unit_price:.2f}",
                f"LKR {item.discount_amount:.2f}" if item.discount_amount else "LKR 0.00",
                f"LKR {item.total_price:.2f}"
            ])
        
        items_table = Table(items_data, colWidths=[2.5*inch, 1*inch, 1.2*inch, 1*inch, 1.2*inch])
        items_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor(settings.BRAND_COLOR_SECONDARY)),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor(settings.BRAND_COLOR_DARK)),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 11),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
            ('ALIGN', (0, 0), (0, -1), 'LEFT'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
        ]))
        elements.append(items_table)
        elements.append(Spacer(1, 0.2 * inch))
        
        # Totals
        totals_data = [
            ["Subtotal:", f"LKR {order.subtotal:.2f}"],
        ]

        if order.discount_amount and order.discount_amount > 0:
            totals_data.append([
                f"Discount ({order.discount_reason or 'N/A'}):",
                f"-LKR {order.discount_amount:.2f}"
            ])

        totals_data.extend([
            ["Total Amount:", f"LKR {order.total_amount:.2f}"],
            ["Paid Amount:", f"LKR {order.paid_amount:.2f}"],
            ["Balance Due:", f"LKR {order.balance:.2f}"],
        ])
        
        totals_table = Table(totals_data, colWidths=[4.5*inch, 2*inch])
        totals_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (1, 0), (1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -2), 10),
            ('FONTSIZE', (0, -1), (-1, -1), 12),
            ('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
            ('TEXTCOLOR', (0, -1), (-1, -1), colors.HexColor(settings.BRAND_COLOR_PRIMARY)),
            ('LINEABOVE', (0, -1), (-1, -1), 2, colors.HexColor(settings.BRAND_COLOR_PRIMARY)),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        elements.append(totals_table)
        
        # Payment information
        if order.payments:
            elements.append(Spacer(1, 0.3 * inch))
            elements.append(Paragraph("Payment History:", heading_style))
            
            payment_data = [["Date", "Method", "Amount", "Commission"]]
            for payment in order.payments:
                payment_data.append([
                    payment.payment_date.strftime("%Y-%m-%d"),
                    payment.payment_method.name,
                    f"LKR {payment.amount:.2f}",
                    f"LKR {payment.commission_amount:.2f}"
                ])
            
            payment_table = Table(payment_data, colWidths=[1.5*inch, 2*inch, 1.5*inch, 1.5*inch])
            payment_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor(settings.BRAND_COLOR_SECONDARY)),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor(settings.BRAND_COLOR_DARK)),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 11),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 10),
                ('ALIGN', (2, 0), (-1, -1), 'RIGHT'),
                ('ALIGN', (0, 0), (1, -1), 'LEFT'),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                ('TOPPADDING', (0, 0), (-1, -1), 8),
            ]))
            elements.append(payment_table)
        
        # Notes
        if order.notes:
            elements.append(Spacer(1, 0.3 * inch))
            elements.append(Paragraph("Notes:", heading_style))
            elements.append(Paragraph(order.notes, styles['Normal']))
        
        # Build PDF
        doc.build(elements)
        
        # Get PDF content
        pdf_content = buffer.getvalue()
        buffer.close()
        
        return pdf_content
    
    async def send_invoice_email(self, order_id: str, template_id: Optional[str] = None) -> bool:
        """
        Send an invoice email for an order
        
        Args:
            order_id: The order ID
            template_id: Optional template ID (uses default if not provided)
            
        Returns:
            True if email sent successfully, False otherwise
        """
        order = self.order_repository.get_by_id(order_id)
        if not order:
            return False
        
        # Get template
        if template_id:
            template = self.repository.get_by_id(template_id)
        else:
            template = self.repository.get_default()
        
        if not template:
            return False
        
        # Generate PDF
        pdf_content = self.generate_invoice_pdf(order_id)
        if not pdf_content:
            return False
        
        # Prepare email content
        subject = template.subject.replace("{order_number}", order.order_number)
        body_html = template.body_html.replace("{customer_name}", order.customer.name)
        body_html = body_html.replace("{order_number}", order.order_number)
        body_html = body_html.replace("{total_amount}", f"LKR {order.total_amount:.2f}")
        body_html = body_html.replace("{balance}", f"LKR {order.balance:.2f}")
        
        # Send email
        return await self.email_service.send_invoice_email(
            to_email=order.customer.email,
            subject=subject,
            body_html=body_html,
            pdf_attachment=pdf_content,
            pdf_filename=f"invoice_{order.order_number}.pdf"
        )
    
    def create_default_template(self) -> InvoiceTemplateResponse:
        """Create a default invoice template with branding"""
        default_template = InvoiceTemplateCreate(
            name="Default Invoice Template",
            subject="Invoice #{order_number} from Miniatures.lk",
            body_html=f"""
            <html>
            <head>
                <style>
                    body {{
                        font-family: Arial, sans-serif;
                        color: {settings.BRAND_COLOR_DARK};
                        line-height: 1.6;
                    }}
                    .header {{
                        background-color: {settings.BRAND_COLOR_PRIMARY};
                        color: white;
                        padding: 20px;
                        text-align: center;
                    }}
                    .content {{
                        padding: 20px;
                    }}
                    .footer {{
                        background-color: {settings.BRAND_COLOR_SECONDARY};
                        padding: 15px;
                        text-align: center;
                        margin-top: 30px;
                    }}
                    .highlight {{
                        color: {settings.BRAND_COLOR_PRIMARY};
                        font-weight: bold;
                    }}
                </style>
            </head>
            <body>
                <div class="header">
                    <h1>Miniatures.lk</h1>
                    <p>Custom 3D Printed Miniatures</p>
                </div>
                <div class="content">
                    <p>Dear {{customer_name}},</p>
                    
                    <p>Thank you for your order! Please find attached your invoice for order <span class="highlight">{{order_number}}</span>.</p>
                    
                    <p><strong>Order Summary:</strong></p>
                    <ul>
                        <li>Total Amount: <span class="highlight">{{total_amount}}</span></li>
                        <li>Balance Due: <span class="highlight">{{balance}}</span></li>
                    </ul>
                    
                    <p>If you have any questions about this invoice, please don't hesitate to contact us.</p>
                    
                    <p>Best regards,<br>
                    The Miniatures.lk Team</p>
                </div>
                <div class="footer">
                    <p>Miniatures.lk | Custom 3D Printed Miniatures</p>
                    <p>Contact us: info@miniatures.lk</p>
                </div>
            </body>
            </html>
            """,
            is_default=True
        )
        
        return self.create_template(default_template)
