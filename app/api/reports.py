"""Report API endpoints"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.services.report import ReportService
from app.schemas.report import (
    SalesReportRequest,
    SalesReportResponse,
    ProfitLossRequest,
    ProfitLossResponse,
    MaterialUsageRequest,
    MaterialUsageResponse,
    BestSellersRequest,
    BestSellersResponse,
    CustomerAnalyticsRequest,
    CustomerAnalyticsResponse
)

router = APIRouter(prefix="/api/reports", tags=["reports"])


@router.post("/sales", response_model=SalesReportResponse)
def get_sales_report(
    request: SalesReportRequest,
    db: Session = Depends(get_db)
):
    """Generate sales report with optional grouping by category or payment method"""
    service = ReportService(db)
    report = service.generate_sales_report(request)
    return report


@router.post("/profit-loss", response_model=ProfitLossResponse)
def get_profit_loss_report(
    request: ProfitLossRequest,
    db: Session = Depends(get_db)
):
    """Generate profit and loss report with expense breakdown by category"""
    service = ReportService(db)
    report = service.generate_profit_loss_report(request)
    return report


@router.post("/materials", response_model=MaterialUsageResponse)
def get_material_usage_report(
    request: MaterialUsageRequest,
    db: Session = Depends(get_db)
):
    """Generate material usage report with resin grouped by color and paint bottles"""
    service = ReportService(db)
    report = service.generate_material_usage_report(request)
    return report


@router.post("/best-sellers", response_model=BestSellersResponse)
def get_best_sellers_report(
    request: BestSellersRequest,
    db: Session = Depends(get_db)
):
    """Generate best-selling products report ranked by quantity sold"""
    service = ReportService(db)
    report = service.generate_best_sellers_report(request)
    return report


@router.post("/customer-analytics", response_model=CustomerAnalyticsResponse)
def get_customer_analytics_report(
    request: CustomerAnalyticsRequest,
    db: Session = Depends(get_db)
):
    """Generate customer analytics report with customer count, average order value, repeat rate, and top customers"""
    service = ReportService(db)
    report = service.generate_customer_analytics_report(request)
    return report
