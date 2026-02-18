"""Main FastAPI application entry point"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.database import engine
from app.models import base
from app.api import product_categories, products, customers, payment_methods, painters, orders, payments, inventory, expenses, woocommerce, invoices, reports

# Create database tables
base.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Miniatures.lk ERP System",
    description="Enterprise Resource Planning system for custom 3D-printed miniatures business",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_origin_regex=settings.CORS_ORIGIN_REGEX or None,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(product_categories.router)
app.include_router(products.router)
app.include_router(customers.router)
app.include_router(payment_methods.router)
app.include_router(painters.router)
app.include_router(orders.router)
app.include_router(payments.router)
app.include_router(inventory.router)
app.include_router(expenses.router)
app.include_router(woocommerce.router)
app.include_router(invoices.router)
app.include_router(reports.router)

@app.get("/")
async def root():
    """Health check endpoint"""
    return {"status": "ok", "message": "Miniatures.lk ERP System API"}

@app.get("/health")
async def health_check():
    """Detailed health check endpoint"""
    return {
        "status": "healthy",
        "database": "connected",
        "version": "1.0.0"
    }
