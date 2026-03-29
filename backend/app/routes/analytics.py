"""
Analytics & Reporting API Routes
Data science integration endpoints for payment analysis and predictions.
"""

from datetime import datetime, date
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.database import get_db
from ..services.analytics import get_analytics_service

router = APIRouter(prefix="/analytics", tags=["analytics"])


# ============== COLLECTION ANALYTICS ==============

@router.get("/collections/overview")
async def get_collection_overview(
    school_id: Optional[int] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    db: AsyncSession = Depends(get_db)
):
    """
    Get comprehensive collection overview metrics.
    Includes total collections, success rates, and outstanding amounts.
    
    Useful for:
    - Dashboard displays
    - Executive reporting
    - Performance monitoring
    """
    analytics = get_analytics_service(db)
    return await analytics.get_collection_overview(school_id, start_date, end_date)


@router.get("/collections/trends")
async def get_collection_trends(
    school_id: Optional[int] = None,
    period: str = Query("daily", regex="^(daily|weekly|monthly)$"),
    num_periods: int = Query(30, ge=7, le=365),
    db: AsyncSession = Depends(get_db)
):
    """
    Get payment collection trends over time.
    Returns time-series data for visualizations.
    
    Parameters:
    - period: daily, weekly, or monthly aggregation
    - num_periods: number of periods to return
    
    Useful for:
    - Trend charts
    - Seasonality analysis
    - Performance tracking
    """
    analytics = get_analytics_service(db)
    return await analytics.get_payment_trends(school_id, period, num_periods)


# ============== PAYMENT PATTERN ANALYSIS ==============

@router.get("/patterns/analysis")
async def analyze_payment_patterns(
    school_id: Optional[int] = None,
    db: AsyncSession = Depends(get_db)
):
    """
    Deep analysis of payment patterns.
    
    Returns:
    - Payment timing patterns (peak hours, peak days)
    - Amount distribution analysis
    - Average days to payment
    - Actionable insights
    
    Useful for:
    - Data science team analysis
    - Collection strategy optimization
    - Reminder scheduling
    """
    analytics = get_analytics_service(db)
    return await analytics.analyze_payment_patterns(school_id)


@router.get("/patterns/timeliness")
async def get_payment_timeliness(
    school_id: Optional[int] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    db: AsyncSession = Depends(get_db)
):
    """
    On-time vs late payment analysis.
    Critical for credit scoring model development.
    
    Returns:
    - On-time payment rate
    - Late payment breakdown (by days overdue)
    - Average days late
    - Prediction data for ML models
    
    Useful for:
    - Credit scoring model training
    - Risk assessment
    - Collection policy refinement
    """
    analytics = get_analytics_service(db)
    return await analytics.get_payment_timeliness_report(school_id, start_date, end_date)


# ============== LOAN ANALYTICS ==============

@router.get("/loans/portfolio")
async def get_loan_portfolio(
    school_id: Optional[int] = None,
    db: AsyncSession = Depends(get_db)
):
    """
    Loan portfolio health analysis.
    
    Returns:
    - Portfolio summary (total loans, amounts, active vs defaulted)
    - Default rate and repayment rate
    - Average loan metrics
    - Risk indicators
    
    Useful for:
    - Loan program evaluation
    - Risk management
    - Financial reporting
    """
    analytics = get_analytics_service(db)
    return await analytics.get_loan_portfolio_analysis(school_id)


# ============== INSTALLMENT ANALYTICS ==============

@router.get("/installments/performance")
async def get_installment_performance(
    school_id: Optional[int] = None,
    db: AsyncSession = Depends(get_db)
):
    """
    Installment plan performance metrics.
    
    Returns:
    - Active and completed plans
    - Collection rate
    - Installment payment statistics
    - Average plan metrics
    
    Useful for:
    - Installment program evaluation
    - Collection optimization
    - Default risk identification
    """
    analytics = get_analytics_service(db)
    return await analytics.get_installment_performance(school_id)


# ============== PREDICTIVE ANALYTICS ==============

@router.get("/predictions/collections")
async def predict_collections(
    school_id: Optional[int] = None,
    months_ahead: int = Query(3, ge=1, le=12),
    db: AsyncSession = Depends(get_db)
):
    """
    Predict future collections based on historical patterns.
    Uses moving average and trend analysis.
    
    Parameters:
    - months_ahead: number of months to predict
    
    Returns:
    - Monthly collection predictions
    - Confidence levels
    - Trend direction
    
    Useful for:
    - Budget planning
    - Cash flow forecasting
    - Resource allocation
    """
    analytics = get_analytics_service(db)
    return await analytics.predict_monthly_collections(school_id, months_ahead)


@router.get("/predictions/at-risk-students")
async def get_at_risk_students(
    school_id: Optional[int] = None,
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    """
    Identify students at risk of defaulting.
    
    Returns:
    - Risk-ranked list of students
    - Risk scores and factors
    - Outstanding balances
    - Number of overdue invoices
    
    Useful for:
    - Proactive intervention
    - Targeted outreach
    - Collection prioritization
    """
    analytics = get_analytics_service(db)
    return await analytics.get_student_risk_assessment(school_id, limit)


# ============== DATA EXPORT ENDPOINTS ==============

@router.get("/export/payment-data")
async def export_payment_data(
    school_id: Optional[int] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    format: str = Query("json", regex="^(json|csv)$"),
    db: AsyncSession = Depends(get_db)
):
    """
    Export payment data for external analysis.
    
    Returns:
    - Full payment records with details
    - Associated invoice and student info
    - Status and timing information
    
    Useful for:
    - External ML model training
    - Custom analysis
    - Reporting systems
    """
    from sqlalchemy import select
    from ..models.payment import Payment, PaymentStatus
    
    query = select(Payment)
    
    if school_id:
        query = query.where(Payment.school_id == school_id)
    
    if start_date:
        query = query.where(Payment.created_at >= datetime.combine(start_date, datetime.min.time()))
    
    if end_date:
        query = query.where(Payment.created_at <= datetime.combine(end_date, datetime.max.time()))
    
    query = query.order_by(Payment.created_at.desc())
    
    result = await db.execute(query)
    payments = result.scalars().all()
    
    data = [
        {
            "transaction_id": p.transaction_id,
            "amount": float(p.amount),
            "phone": p.phone,
            "status": p.status.value if hasattr(p.status, 'value') else p.status,
            "invoice_id": p.invoice_id,
            "student_id": p.student_id,
            "guardian_id": p.guardian_id,
            "school_id": p.school_id,
            "created_at": p.created_at.isoformat() if p.created_at else None,
            "completed_at": p.completed_at.isoformat() if p.completed_at else None,
            "mpesa_receipt": p.mpesa_receipt_number,
            "result_code": p.result_code,
            "result_desc": p.result_desc
        }
        for p in payments
    ]
    
    if format == "csv":
        import io
        import csv
        
        output = io.StringIO()
        if data:
            writer = csv.DictWriter(output, fieldnames=data[0].keys())
            writer.writeheader()
            writer.writerows(data)
        
        return {
            "format": "csv",
            "record_count": len(data),
            "data": output.getvalue()
        }
    
    return {
        "format": "json",
        "record_count": len(data),
        "data": data
    }


@router.get("/export/credit-scores")
async def export_credit_scores(
    min_score: Optional[int] = None,
    max_score: Optional[int] = None,
    risk_level: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """
    Export credit score data for ML model training.
    
    Returns:
    - Credit scores with all component scores
    - Payment history metrics
    - Loan history
    - Risk levels
    
    Useful for:
    - Credit scoring model training
    - Risk analysis
    - Lending policy development
    """
    from sqlalchemy import select
    from ..models.payment import CreditScore
    
    query = select(CreditScore)
    
    if min_score:
        query = query.where(CreditScore.credit_score >= min_score)
    if max_score:
        query = query.where(CreditScore.credit_score <= max_score)
    if risk_level:
        query = query.where(CreditScore.risk_level == risk_level)
    
    result = await db.execute(query)
    scores = result.scalars().all()
    
    return {
        "record_count": len(scores),
        "data": [
            {
                "guardian_id": s.guardian_id,
                "credit_score": s.credit_score,
                "payment_history_score": s.payment_history_score,
                "credit_utilization_score": s.credit_utilization_score,
                "length_of_history_score": s.length_of_history_score,
                "payment_consistency_score": s.payment_consistency_score,
                "risk_level": s.risk_level,
                "max_loan_amount": float(s.max_loan_amount),
                "recommended_interest_rate": float(s.recommended_interest_rate),
                "total_payments": s.total_payments,
                "on_time_payments": s.on_time_payments,
                "late_payments": s.late_payments,
                "missed_payments": s.missed_payments,
                "average_days_late": s.average_days_late,
                "total_loans": s.total_loans,
                "active_loans": s.active_loans,
                "defaulted_loans": s.defaulted_loans,
                "total_loan_amount": float(s.total_loan_amount or 0),
                "total_repaid_amount": float(s.total_repaid_amount or 0),
                "last_calculated": s.last_calculated.isoformat() if s.last_calculated else None
            }
            for s in scores
        ]
    }


# ============== DASHBOARD SUMMARY ==============

@router.get("/dashboard/summary")
async def get_dashboard_summary(
    school_id: Optional[int] = None,
    db: AsyncSession = Depends(get_db)
):
    """
    Comprehensive dashboard summary combining multiple metrics.
    Single endpoint for dashboard data needs.
    
    Returns:
    - Collection overview
    - Recent trends
    - Active loans and installments
    - At-risk students count
    """
    analytics = get_analytics_service(db)
    
    # Get all relevant data in parallel (in production, use asyncio.gather)
    overview = await analytics.get_collection_overview(school_id)
    trends = await analytics.get_payment_trends(school_id, "daily", 7)
    loan_portfolio = await analytics.get_loan_portfolio_analysis(school_id)
    installments = await analytics.get_installment_performance(school_id)
    at_risk = await analytics.get_student_risk_assessment(school_id, 5)
    
    return {
        "overview": overview,
        "recent_trends": trends,
        "loans": {
            "active": loan_portfolio.get("portfolio_summary", {}).get("active_loans", 0) if isinstance(loan_portfolio, dict) else 0,
            "default_rate": loan_portfolio.get("rates", {}).get("default_rate", 0) if isinstance(loan_portfolio, dict) else 0
        },
        "installments": {
            "active_plans": installments.get("summary", {}).get("active_plans", 0) if isinstance(installments, dict) else 0,
            "collection_rate": installments.get("summary", {}).get("collection_rate", 0) if isinstance(installments, dict) else 0
        },
        "at_risk_students": {
            "count": len(at_risk) if isinstance(at_risk, list) else 0,
            "top_risks": at_risk[:3] if isinstance(at_risk, list) else []
        },
        "generated_at": datetime.utcnow().isoformat()
    }
