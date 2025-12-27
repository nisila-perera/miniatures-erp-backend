"""Invoice API endpoints"""
from fastapi import APIRouter, Depends, HTTPException, Response
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import List, Optional
from io import BytesIO

from app.core.database import get_db
from app.services.invoice_service import InvoiceService
from app.schemas.invoice import (
    InvoiceTemplateCreate,
    InvoiceTemplateUpdate,
    InvoiceTemplateResponse
)

router = APIRouter(prefix="/api", tags=["invoices"])


# Invoice Template Management
@router.post("/invoice-templates", response_model=InvoiceTemplateResponse, status_code=201)
def create_invoice_template(
    template_data: InvoiceTemplateCreate,
    db: Session = Depends(get_db)
):
    """Create a new invoice template"""
    service = InvoiceService(db)
    template = service.create_template(template_data)
    return template


@router.get("/invoice-templates", response_model=List[InvoiceTemplateResponse])
def get_invoice_templates(
    db: Session = Depends(get_db)
):
    """Get all invoice templates"""
    service = InvoiceService(db)
    templates = service.get_all_templates()
    return templates


@router.get("/invoice-templates/default", response_model=InvoiceTemplateResponse)
def get_default_invoice_template(
    db: Session = Depends(get_db)
):
    """Get the default invoice template"""
    service = InvoiceService(db)
    template = service.get_default_template()
    if not template:
        raise HTTPException(status_code=404, detail="No default template found")
    return template


@router.get("/invoice-templates/{template_id}", response_model=InvoiceTemplateResponse)
def get_invoice_template(
    template_id: str,
    db: Session = Depends(get_db)
):
    """Get an invoice template by ID"""
    service = InvoiceService(db)
    template = service.get_template(template_id)
    if not template:
        raise HTTPException(status_code=404, detail="Invoice template not found")
    return template


@router.put("/invoice-templates/{template_id}", response_model=InvoiceTemplateResponse)
def update_invoice_template(
    template_id: str,
    template_data: InvoiceTemplateUpdate,
    db: Session = Depends(get_db)
):
    """Update an invoice template"""
    service = InvoiceService(db)
    template = service.update_template(template_id, template_data)
    if not template:
        raise HTTPException(status_code=404, detail="Invoice template not found")
    return template


@router.delete("/invoice-templates/{template_id}", status_code=204)
def delete_invoice_template(
    template_id: str,
    db: Session = Depends(get_db)
):
    """Delete an invoice template"""
    service = InvoiceService(db)
    success = service.delete_template(template_id)
    if not success:
        raise HTTPException(status_code=404, detail="Invoice template not found")


@router.post("/invoice-templates/default", response_model=InvoiceTemplateResponse, status_code=201)
def create_default_invoice_template(
    db: Session = Depends(get_db)
):
    """Create a default invoice template with branding"""
    service = InvoiceService(db)
    template = service.create_default_template()
    return template


# Invoice Generation and Sending
@router.get("/orders/{order_id}/invoice/pdf")
def generate_invoice_pdf(
    order_id: str,
    db: Session = Depends(get_db)
):
    """Generate and download invoice PDF for an order"""
    service = InvoiceService(db)
    pdf_content = service.generate_invoice_pdf(order_id)
    
    if not pdf_content:
        raise HTTPException(status_code=404, detail="Order not found")
    
    # Return PDF as streaming response
    return StreamingResponse(
        BytesIO(pdf_content),
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename=invoice_{order_id}.pdf"
        }
    )


@router.post("/orders/{order_id}/invoice/send", status_code=200)
async def send_invoice_email(
    order_id: str,
    template_id: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Send invoice email for an order"""
    service = InvoiceService(db)
    success = await service.send_invoice_email(order_id, template_id)
    
    if not success:
        raise HTTPException(
            status_code=400,
            detail="Failed to send invoice email. Check order exists and email configuration."
        )
    
    return {"message": "Invoice email sent successfully"}
