"""WooCommerce integration API endpoints"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.services.woocommerce_integration import WooCommerceIntegrationService
from pydantic import BaseModel


router = APIRouter(prefix="/woocommerce", tags=["woocommerce"])


class SyncResponse(BaseModel):
    """Response model for sync operations"""
    created: int
    updated: int
    message: str


class StatusSyncResponse(BaseModel):
    """Response model for status sync"""
    success: bool
    message: str


@router.post("/sync/customers", response_model=SyncResponse)
def sync_customers(db: Session = Depends(get_db)):
    """
    Sync customers from WooCommerce
    
    Imports all customers from WooCommerce and creates or updates them in the ERP system.
    Existing customers are identified by their WooCommerce ID.
    """
    try:
        service = WooCommerceIntegrationService(db)
        created, updated = service.sync_customers()
        return SyncResponse(
            created=created,
            updated=updated,
            message=f"Successfully synced customers: {created} created, {updated} updated"
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"WooCommerce sync failed: {str(e)}"
        )


@router.post("/sync/products", response_model=SyncResponse)
def sync_products(db: Session = Depends(get_db)):
    """
    Sync products from WooCommerce
    
    Imports all products from WooCommerce and creates or updates them in the ERP system.
    Existing products are identified by their WooCommerce ID.
    """
    try:
        service = WooCommerceIntegrationService(db)
        created, updated = service.sync_products()
        return SyncResponse(
            created=created,
            updated=updated,
            message=f"Successfully synced products: {created} created, {updated} updated"
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"WooCommerce sync failed: {str(e)}"
        )


@router.post("/sync/orders", response_model=SyncResponse)
def sync_orders(db: Session = Depends(get_db)):
    """
    Sync orders from WooCommerce
    
    Imports all orders from WooCommerce and creates or updates them in the ERP system.
    Existing orders are identified by their WooCommerce ID.
    """
    try:
        service = WooCommerceIntegrationService(db)
        created, updated = service.sync_orders()
        return SyncResponse(
            created=created,
            updated=updated,
            message=f"Successfully synced orders: {created} created, {updated} updated"
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"WooCommerce sync failed: {str(e)}"
        )


@router.put("/orders/{order_id}/status", response_model=StatusSyncResponse)
def sync_order_status(order_id: str, db: Session = Depends(get_db)):
    """
    Sync order status to WooCommerce
    
    Updates the order status in WooCommerce to match the ERP system.
    Only syncs orders that originated from the website.
    """
    try:
        service = WooCommerceIntegrationService(db)
        synced = service.sync_order_status_to_woocommerce(order_id)
        
        if synced:
            return StatusSyncResponse(
                success=True,
                message="Order status synced to WooCommerce"
            )
        else:
            return StatusSyncResponse(
                success=False,
                message="Order not synced (not a website order)"
            )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"WooCommerce sync failed: {str(e)}"
        )
