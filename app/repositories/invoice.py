"""Invoice template repository"""
from sqlalchemy.orm import Session
from typing import List, Optional
from app.models.invoice import InvoiceTemplate
from app.schemas.invoice import InvoiceTemplateCreate, InvoiceTemplateUpdate


class InvoiceTemplateRepository:
    """Repository for invoice template operations"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create(self, template_data: InvoiceTemplateCreate) -> InvoiceTemplate:
        """Create a new invoice template"""
        # If this template is set as default, unset all other defaults
        if template_data.is_default:
            self.db.query(InvoiceTemplate).update({"is_default": False})
        
        template = InvoiceTemplate(**template_data.model_dump())
        self.db.add(template)
        self.db.commit()
        self.db.refresh(template)
        return template
    
    def get_by_id(self, template_id: str) -> Optional[InvoiceTemplate]:
        """Get an invoice template by ID"""
        return self.db.query(InvoiceTemplate).filter(
            InvoiceTemplate.id == template_id
        ).first()
    
    def get_all(self) -> List[InvoiceTemplate]:
        """Get all invoice templates"""
        return self.db.query(InvoiceTemplate).all()
    
    def get_default(self) -> Optional[InvoiceTemplate]:
        """Get the default invoice template"""
        return self.db.query(InvoiceTemplate).filter(
            InvoiceTemplate.is_default == True
        ).first()
    
    def update(self, template_id: str, template_data: InvoiceTemplateUpdate) -> Optional[InvoiceTemplate]:
        """Update an invoice template"""
        template = self.get_by_id(template_id)
        if not template:
            return None
        
        update_data = template_data.model_dump(exclude_unset=True)
        
        # If setting this as default, unset all other defaults
        if update_data.get("is_default"):
            self.db.query(InvoiceTemplate).filter(
                InvoiceTemplate.id != template_id
            ).update({"is_default": False})
        
        for key, value in update_data.items():
            setattr(template, key, value)
        
        self.db.commit()
        self.db.refresh(template)
        return template
    
    def delete(self, template_id: str) -> bool:
        """Delete an invoice template"""
        template = self.get_by_id(template_id)
        if not template:
            return False
        
        self.db.delete(template)
        self.db.commit()
        return True
