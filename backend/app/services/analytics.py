"""
Analytics & Reporting Service
Provides payment pattern analysis, collection metrics, and predictive insights.
Designed for data science team integration.
"""

from datetime import datetime, timedelta, date
from decimal import Decimal
from typing import Optional, Dict, Any, List, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_, case
from sqlalchemy.orm import selectinload
import logging

from ..models.payment import (
    Payment, PaymentStatus, Invoice, InvoiceStatus, Student, Guardian, School,
    Loan, LoanStatus, InstallmentPlan, Installment, PaymentAnalytics,
    LoanRepayment
)

logger = logging.getLogger(__name__)


class AnalyticsService:
    """
    Analytics engine for payment pattern analysis and reporting.
    Provides metrics for schools, collection efficiency, and predictions.
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    # ============== COLLECTION METRICS ==============

    async def get_collection_overview(
        self,
        school_id: Optional[int] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> Dict[str, Any]:
        """
        Get comprehensive collection overview metrics.
        """
        if not start_date:
            start_date = datetime.utcnow().date() - timedelta(days=30)
        if not end_date:
            end_date = datetime.utcnow().date()

        # Base query filters
        date_filter = and_(
            Payment.created_at >= datetime.combine(start_date, datetime.min.time()),
            Payment.created_at <= datetime.combine(end_date, datetime.max.time())
        )

        # Total collections
        collections_query = select(
            func.count(Payment.id).label("total_transactions"),
            func.sum(case(
                (Payment.status == PaymentStatus.COMPLETED, Payment.amount),
                else_=Decimal("0")
            )).label("total_collected"),
            func.count(case(
                (Payment.status == PaymentStatus.COMPLETED, 1)
            )).label("successful_transactions"),
            func.count(case(
                (Payment.status == PaymentStatus.FAILED, 1)
            )).label("failed_transactions")
        ).where(date_filter)

        if school_id:
            collections_query = collections_query.where(Payment.school_id == school_id)

        result = await self.db.execute(collections_query)
        collection_stats = result.fetchone()

        # Outstanding invoices
        outstanding_query = select(
            func.sum(Invoice.balance).label("total_outstanding"),
            func.count(Invoice.id).label("outstanding_invoices")
        ).where(
            Invoice.status.in_([InvoiceStatus.PENDING, InvoiceStatus.PARTIAL, InvoiceStatus.OVERDUE])
        )

        if school_id:
            outstanding_query = outstanding_query.where(Invoice.school_id == school_id)

        outstanding_result = await self.db.execute(outstanding_query)
        outstanding_stats = outstanding_result.fetchone()

        # Total invoiced
        invoiced_query = select(
            func.sum(Invoice.total_amount).label("total_invoiced")
        )
        if school_id:
            invoiced_query = invoiced_query.where(Invoice.school_id == school_id)

        invoiced_result = await self.db.execute(invoiced_query)
        total_invoiced = invoiced_result.scalar() or Decimal("0")

        # Calculate collection rate
        total_collected = collection_stats.total_collected or Decimal("0")
        collection_rate = (total_collected / total_invoiced * 100) if total_invoiced > 0 else Decimal("0")

        return {
            "period": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat()
            },
            "collections": {
                "total_collected": float(total_collected),
                "total_transactions": collection_stats.total_transactions or 0,
                "successful_transactions": collection_stats.successful_transactions or 0,
                "failed_transactions": collection_stats.failed_transactions or 0,
                "success_rate": round(
                    (collection_stats.successful_transactions or 0) / 
                    max(collection_stats.total_transactions or 1, 1) * 100, 2
                )
            },
            "invoices": {
                "total_invoiced": float(total_invoiced),
                "total_outstanding": float(outstanding_stats.total_outstanding or 0),
                "outstanding_count": outstanding_stats.outstanding_invoices or 0,
                "collection_rate": round(float(collection_rate), 2)
            }
        }

    async def get_payment_trends(
        self,
        school_id: Optional[int] = None,
        period: str = "daily",  # daily, weekly, monthly
        num_periods: int = 30
    ) -> List[Dict[str, Any]]:
        """
        Get payment trends over time.
        """
        end_date = datetime.utcnow()
        
        if period == "daily":
            start_date = end_date - timedelta(days=num_periods)
            date_trunc = func.date(Payment.created_at)
        elif period == "weekly":
            start_date = end_date - timedelta(weeks=num_periods)
            date_trunc = func.date(func.datetime(Payment.created_at, 'weekday 0'))
        else:  # monthly
            start_date = end_date - timedelta(days=num_periods * 30)
            date_trunc = func.strftime('%Y-%m-01', Payment.created_at)

        query = select(
            date_trunc.label("period"),
            func.count(Payment.id).label("transaction_count"),
            func.sum(case(
                (Payment.status == PaymentStatus.COMPLETED, Payment.amount),
                else_=Decimal("0")
            )).label("amount_collected"),
            func.count(case(
                (Payment.status == PaymentStatus.COMPLETED, 1)
            )).label("successful"),
            func.count(case(
                (Payment.status == PaymentStatus.FAILED, 1)
            )).label("failed")
        ).where(
            Payment.created_at >= start_date
        ).group_by(date_trunc).order_by(date_trunc)

        if school_id:
            query = query.where(Payment.school_id == school_id)

        result = await self.db.execute(query)
        trends = result.fetchall()

        return [
            {
                "period": str(row.period),
                "transaction_count": row.transaction_count,
                "amount_collected": float(row.amount_collected or 0),
                "successful": row.successful or 0,
                "failed": row.failed or 0,
                "success_rate": round((row.successful or 0) / max(row.transaction_count, 1) * 100, 2)
            }
            for row in trends
        ]

    # ============== PAYMENT PATTERN ANALYSIS ==============

    async def analyze_payment_patterns(
        self,
        school_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Analyze payment patterns for data science insights.
        Includes timing patterns, amount distributions, and behavior analysis.
        """
        # Get completed payments
        query = select(Payment).where(
            Payment.status == PaymentStatus.COMPLETED
        )
        if school_id:
            query = query.where(Payment.school_id == school_id)

        result = await self.db.execute(query)
        payments = result.scalars().all()

        if not payments:
            return {"message": "No payment data available"}

        # Analyze payment timing
        hour_distribution = {}
        day_distribution = {}
        amount_buckets = {"<1000": 0, "1000-5000": 0, "5000-10000": 0, "10000-50000": 0, ">50000": 0}
        
        amounts = []
        days_to_pay = []

        for payment in payments:
            # Hour distribution
            hour = payment.created_at.hour
            hour_distribution[hour] = hour_distribution.get(hour, 0) + 1
            
            # Day of week distribution
            day = payment.created_at.strftime("%A")
            day_distribution[day] = day_distribution.get(day, 0) + 1
            
            # Amount distribution
            amount = float(payment.amount)
            amounts.append(amount)
            
            if amount < 1000:
                amount_buckets["<1000"] += 1
            elif amount < 5000:
                amount_buckets["1000-5000"] += 1
            elif amount < 10000:
                amount_buckets["5000-10000"] += 1
            elif amount < 50000:
                amount_buckets["10000-50000"] += 1
            else:
                amount_buckets[">50000"] += 1

            # Days to payment (if linked to invoice)
            if payment.invoice_id and payment.completed_at:
                invoice_result = await self.db.execute(
                    select(Invoice).where(Invoice.id == payment.invoice_id)
                )
                invoice = invoice_result.scalar_one_or_none()
                if invoice and invoice.created_at:
                    days = (payment.completed_at - invoice.created_at).days
                    days_to_pay.append(days)

        # Calculate statistics
        avg_amount = sum(amounts) / len(amounts) if amounts else 0
        median_amount = sorted(amounts)[len(amounts) // 2] if amounts else 0
        avg_days_to_pay = sum(days_to_pay) / len(days_to_pay) if days_to_pay else 0

        # Find peak hours and days
        peak_hour = max(hour_distribution, key=hour_distribution.get) if hour_distribution else None
        peak_day = max(day_distribution, key=day_distribution.get) if day_distribution else None

        return {
            "summary": {
                "total_payments": len(payments),
                "average_amount": round(avg_amount, 2),
                "median_amount": round(median_amount, 2),
                "average_days_to_payment": round(avg_days_to_pay, 1)
            },
            "timing_patterns": {
                "peak_hour": peak_hour,
                "peak_day": peak_day,
                "hour_distribution": hour_distribution,
                "day_distribution": day_distribution
            },
            "amount_distribution": amount_buckets,
            "insights": self._generate_pattern_insights(
                hour_distribution, day_distribution, avg_days_to_pay, amount_buckets
            )
        }

    def _generate_pattern_insights(
        self,
        hour_dist: Dict,
        day_dist: Dict,
        avg_days: float,
        amount_dist: Dict
    ) -> List[str]:
        """Generate actionable insights from payment patterns."""
        insights = []
        
        if hour_dist:
            peak_hour = max(hour_dist, key=hour_dist.get)
            if 9 <= peak_hour <= 17:
                insights.append(f"Most payments occur during business hours (peak: {peak_hour}:00)")
            else:
                insights.append(f"Significant after-hours payment activity (peak: {peak_hour}:00)")
        
        if day_dist:
            peak_day = max(day_dist, key=day_dist.get)
            insights.append(f"Highest payment activity on {peak_day}s")
        
        if avg_days > 30:
            insights.append("High average days to payment - consider earlier reminders")
        elif avg_days < 7:
            insights.append("Excellent payment response time")
        
        large_payments = amount_dist.get(">50000", 0)
        if large_payments > 0:
            insights.append(f"{large_payments} large payments (>50,000) - consider installment plans")
        
        return insights

    # ============== ON-TIME VS LATE ANALYSIS ==============

    async def get_payment_timeliness_report(
        self,
        school_id: Optional[int] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> Dict[str, Any]:
        """
        Analyze on-time vs late payment patterns.
        Critical for credit scoring model.
        """
        if not start_date:
            start_date = datetime.utcnow().date() - timedelta(days=365)
        if not end_date:
            end_date = datetime.utcnow().date()

        # Get invoices with payments
        query = select(Invoice).options(selectinload(Invoice.payments)).where(
            Invoice.created_at >= datetime.combine(start_date, datetime.min.time()),
            Invoice.created_at <= datetime.combine(end_date, datetime.max.time())
        )
        
        if school_id:
            query = query.where(Invoice.school_id == school_id)

        result = await self.db.execute(query)
        invoices = result.scalars().all()

        on_time = 0
        late = 0
        very_late = 0
        unpaid = 0
        total_late_days = 0
        late_by_days = {"1-7 days": 0, "8-14 days": 0, "15-30 days": 0, ">30 days": 0}

        for invoice in invoices:
            if not invoice.due_date:
                continue

            completed_payments = [p for p in invoice.payments if p.status == PaymentStatus.COMPLETED]
            
            if not completed_payments:
                if invoice.status in [InvoiceStatus.PENDING, InvoiceStatus.PARTIAL, InvoiceStatus.OVERDUE]:
                    unpaid += 1
                continue

            # Get earliest completion
            first_payment = min(completed_payments, key=lambda p: p.completed_at or p.created_at)
            payment_date = (first_payment.completed_at or first_payment.created_at).date()

            if payment_date <= invoice.due_date:
                on_time += 1
            else:
                days_late = (payment_date - invoice.due_date).days
                total_late_days += days_late
                
                if days_late <= 7:
                    late_by_days["1-7 days"] += 1
                    late += 1
                elif days_late <= 14:
                    late_by_days["8-14 days"] += 1
                    late += 1
                elif days_late <= 30:
                    late_by_days["15-30 days"] += 1
                    late += 1
                else:
                    late_by_days[">30 days"] += 1
                    very_late += 1

        total_paid = on_time + late + very_late
        avg_late_days = total_late_days / (late + very_late) if (late + very_late) > 0 else 0

        return {
            "period": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat()
            },
            "summary": {
                "total_invoices": len(invoices),
                "on_time_payments": on_time,
                "late_payments": late,
                "very_late_payments": very_late,
                "unpaid": unpaid,
                "on_time_rate": round(on_time / max(total_paid, 1) * 100, 2),
                "average_days_late": round(avg_late_days, 1)
            },
            "late_breakdown": late_by_days,
            "predictions": {
                "expected_late_rate": round((late + very_late) / max(total_paid, 1) * 100, 2),
                "high_risk_threshold": "15+ days late"
            }
        }

    # ============== LOAN ANALYTICS ==============

    async def get_loan_portfolio_analysis(
        self,
        school_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Analyze loan portfolio health and performance.
        """
        query = select(Loan)
        if school_id:
            query = query.where(Loan.school_id == school_id)

        result = await self.db.execute(query)
        loans = result.scalars().all()

        if not loans:
            return {"message": "No loan data available"}

        # Portfolio metrics
        total_loans = len(loans)
        total_disbursed = sum(l.disbursed_amount or Decimal("0") for l in loans)
        total_outstanding = sum(l.outstanding_amount or Decimal("0") for l in loans)
        total_repaid = sum(l.repaid_amount or Decimal("0") for l in loans)

        # Status breakdown
        status_counts = {}
        for loan in loans:
            status = loan.status.value if hasattr(loan.status, 'value') else loan.status
            status_counts[status] = status_counts.get(status, 0) + 1

        active_loans = [l for l in loans if l.status in [LoanStatus.ACTIVE, LoanStatus.DISBURSED]]
        defaulted_loans = [l for l in loans if l.status == LoanStatus.DEFAULTED]

        # Calculate rates
        default_rate = len(defaulted_loans) / total_loans * 100 if total_loans > 0 else 0
        repayment_rate = float(total_repaid / total_disbursed * 100) if total_disbursed > 0 else 0

        # Average loan metrics
        avg_loan_amount = float(sum(l.principal_amount for l in loans) / total_loans) if total_loans > 0 else 0
        avg_interest_rate = float(sum(l.interest_rate for l in loans) / total_loans) if total_loans > 0 else 0

        return {
            "portfolio_summary": {
                "total_loans": total_loans,
                "total_disbursed": float(total_disbursed),
                "total_outstanding": float(total_outstanding),
                "total_repaid": float(total_repaid),
                "active_loans": len(active_loans),
                "defaulted_loans": len(defaulted_loans)
            },
            "rates": {
                "default_rate": round(default_rate, 2),
                "repayment_rate": round(repayment_rate, 2),
                "average_interest_rate": round(avg_interest_rate, 2)
            },
            "averages": {
                "average_loan_amount": round(avg_loan_amount, 2),
                "average_tenure_months": round(sum(l.tenure_months for l in loans) / total_loans, 1) if total_loans > 0 else 0
            },
            "status_breakdown": status_counts,
            "risk_indicators": {
                "at_risk_loans": len([l for l in active_loans if l.outstanding_amount and l.outstanding_amount > l.principal_amount * Decimal("0.8")]),
                "early_default_warning": len(defaulted_loans) > total_loans * 0.1
            }
        }

    # ============== INSTALLMENT PLAN ANALYTICS ==============

    async def get_installment_performance(
        self,
        school_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Analyze installment plan performance.
        """
        query = select(InstallmentPlan)
        if school_id:
            query = query.where(InstallmentPlan.school_id == school_id)

        result = await self.db.execute(query)
        plans = result.scalars().all()

        if not plans:
            return {"message": "No installment plan data available"}

        total_plans = len(plans)
        active_plans = [p for p in plans if p.status == "active"]
        completed_plans = [p for p in plans if p.status == "completed"]

        total_planned = sum(p.total_amount for p in plans)
        total_collected = sum(p.paid_amount or Decimal("0") for p in plans)

        # Get installment details
        installment_query = select(Installment)
        installment_result = await self.db.execute(installment_query)
        installments = installment_result.scalars().all()

        paid_installments = [i for i in installments if i.status == "paid"]
        overdue_installments = [i for i in installments if i.status == "overdue"]

        return {
            "summary": {
                "total_plans": total_plans,
                "active_plans": len(active_plans),
                "completed_plans": len(completed_plans),
                "total_planned_amount": float(total_planned),
                "total_collected": float(total_collected),
                "collection_rate": round(float(total_collected / total_planned * 100), 2) if total_planned > 0 else 0
            },
            "installment_metrics": {
                "total_installments": len(installments),
                "paid_installments": len(paid_installments),
                "overdue_installments": len(overdue_installments),
                "payment_rate": round(len(paid_installments) / max(len(installments), 1) * 100, 2)
            },
            "average_metrics": {
                "average_plan_amount": round(float(total_planned / total_plans), 2) if total_plans > 0 else 0,
                "average_installments_per_plan": round(len(installments) / total_plans, 1) if total_plans > 0 else 0
            }
        }

    # ============== PREDICTIVE ANALYTICS ==============

    async def predict_monthly_collections(
        self,
        school_id: Optional[int] = None,
        months_ahead: int = 3
    ) -> List[Dict[str, Any]]:
        """
        Predict future collections based on historical patterns.
        Simple moving average model.
        """
        # Get historical monthly collections
        twelve_months_ago = datetime.utcnow() - timedelta(days=365)
        
        query = select(
            func.strftime('%Y-%m', Payment.created_at).label("month"),
            func.sum(case(
                (Payment.status == PaymentStatus.COMPLETED, Payment.amount),
                else_=Decimal("0")
            )).label("collected")
        ).where(
            Payment.created_at >= twelve_months_ago
        ).group_by(func.strftime('%Y-%m', Payment.created_at)).order_by(func.strftime('%Y-%m', Payment.created_at))

        if school_id:
            query = query.where(Payment.school_id == school_id)

        result = await self.db.execute(query)
        historical = result.fetchall()

        if len(historical) < 3:
            return [{"message": "Insufficient historical data for prediction"}]

        # Calculate 3-month moving average
        amounts = [float(row.collected or 0) for row in historical]
        moving_avg = sum(amounts[-3:]) / 3 if len(amounts) >= 3 else sum(amounts) / len(amounts)

        # Calculate trend
        if len(amounts) >= 6:
            recent_avg = sum(amounts[-3:]) / 3
            older_avg = sum(amounts[-6:-3]) / 3
            trend = (recent_avg - older_avg) / older_avg if older_avg > 0 else 0
        else:
            trend = 0

        # Generate predictions
        predictions = []
        current_date = datetime.utcnow()
        
        for i in range(1, months_ahead + 1):
            future_date = current_date + timedelta(days=30 * i)
            predicted_amount = moving_avg * (1 + trend * i * 0.5)  # Dampen trend effect
            
            predictions.append({
                "month": future_date.strftime("%Y-%m"),
                "predicted_collection": round(predicted_amount, 2),
                "confidence": "medium" if len(historical) >= 6 else "low",
                "trend": "increasing" if trend > 0.05 else "decreasing" if trend < -0.05 else "stable"
            })

        return predictions

    async def get_student_risk_assessment(
        self,
        school_id: Optional[int] = None,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Identify students at risk of defaulting.
        """
        # Get students with overdue invoices
        query = select(Student).options(
            selectinload(Student.invoices),
            selectinload(Student.payments)
        ).where(Student.status == "active")

        if school_id:
            query = query.where(Student.school_id == school_id)

        result = await self.db.execute(query)
        students = result.scalars().all()

        risk_assessments = []
        
        for student in students:
            overdue_invoices = [i for i in student.invoices if i.status == InvoiceStatus.OVERDUE]
            total_balance = sum(i.balance for i in student.invoices if i.status in [InvoiceStatus.PENDING, InvoiceStatus.PARTIAL, InvoiceStatus.OVERDUE])
            
            completed_payments = [p for p in student.payments if p.status == PaymentStatus.COMPLETED]
            failed_payments = [p for p in student.payments if p.status == PaymentStatus.FAILED]
            
            # Calculate risk score (0-100, higher = more risk)
            risk_score = 0
            risk_factors = []
            
            if overdue_invoices:
                risk_score += min(len(overdue_invoices) * 20, 40)
                risk_factors.append(f"{len(overdue_invoices)} overdue invoices")
            
            if total_balance > Decimal("50000"):
                risk_score += 20
                risk_factors.append("High outstanding balance")
            
            if len(failed_payments) > len(completed_payments) * 0.3:
                risk_score += 20
                risk_factors.append("High payment failure rate")
            
            if not completed_payments and student.invoices:
                risk_score += 20
                risk_factors.append("No payment history")
            
            if risk_score > 0:
                risk_assessments.append({
                    "student_id": student.id,
                    "admission_number": student.admission_number,
                    "name": f"{student.first_name} {student.last_name}",
                    "risk_score": min(risk_score, 100),
                    "risk_level": "high" if risk_score >= 60 else "medium" if risk_score >= 30 else "low",
                    "outstanding_balance": float(total_balance),
                    "overdue_invoices": len(overdue_invoices),
                    "risk_factors": risk_factors
                })

        # Sort by risk score and return top risks
        risk_assessments.sort(key=lambda x: x["risk_score"], reverse=True)
        return risk_assessments[:limit]


# Service factory
def get_analytics_service(db: AsyncSession) -> AnalyticsService:
    return AnalyticsService(db)
