"""
Credit Scoring Service
Calculates credit scores based on payment history and behavior patterns.
Used for micro-loan eligibility and risk assessment.
"""

from datetime import datetime, timedelta
from decimal import Decimal
from typing import Optional, Dict, Any, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
import logging

from ..models.payment import (
    Payment, PaymentStatus, Invoice, Guardian, CreditScore,
    Loan, LoanStatus, InstallmentPlan, Installment
)

logger = logging.getLogger(__name__)


# Credit Score Weights
PAYMENT_HISTORY_WEIGHT = 0.35
CREDIT_UTILIZATION_WEIGHT = 0.30
HISTORY_LENGTH_WEIGHT = 0.15
CONSISTENCY_WEIGHT = 0.20

# Score Ranges
MIN_SCORE = 300
MAX_SCORE = 850

# Risk Level Thresholds
RISK_THRESHOLDS = {
    "low": 700,
    "medium": 550,
    "high": 400,
    "very_high": 0
}

# Loan Amount Multipliers based on risk
LOAN_MULTIPLIERS = {
    "low": 3.0,
    "medium": 1.5,
    "high": 0.5,
    "very_high": 0.0
}

# Interest Rate Ranges based on risk
INTEREST_RATES = {
    "low": Decimal("10.0"),
    "medium": Decimal("15.0"),
    "high": Decimal("22.0"),
    "very_high": Decimal("30.0")
}


class CreditScoringService:
    """
    Credit scoring engine for the Smart Student Finance Platform.
    Implements a comprehensive scoring model based on:
    - Payment history (35%)
    - Credit utilization (30%)
    - Length of credit history (15%)
    - Payment consistency (20%)
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def calculate_credit_score(self, guardian_id: int) -> CreditScore:
        """
        Calculate and update the credit score for a guardian.
        Returns the updated CreditScore object.
        """
        # Get or create credit score record
        credit_score = await self._get_or_create_credit_score(guardian_id)
        
        # Calculate component scores
        payment_history = await self._calculate_payment_history_score(guardian_id)
        credit_utilization = await self._calculate_credit_utilization_score(guardian_id)
        history_length = await self._calculate_history_length_score(guardian_id)
        consistency = await self._calculate_consistency_score(guardian_id)
        
        # Calculate weighted total score
        total_score = (
            payment_history["score"] * PAYMENT_HISTORY_WEIGHT +
            credit_utilization["score"] * CREDIT_UTILIZATION_WEIGHT +
            history_length["score"] * HISTORY_LENGTH_WEIGHT +
            consistency["score"] * CONSISTENCY_WEIGHT
        )
        
        # Scale to credit score range (300-850)
        scaled_score = int(MIN_SCORE + (total_score / 1000) * (MAX_SCORE - MIN_SCORE))
        scaled_score = max(MIN_SCORE, min(MAX_SCORE, scaled_score))
        
        # Determine risk level
        risk_level = self._determine_risk_level(scaled_score)
        
        # Calculate max loan amount and recommended interest rate
        avg_payment = await self._get_average_payment_amount(guardian_id)
        max_loan = self._calculate_max_loan_amount(risk_level, avg_payment)
        interest_rate = INTEREST_RATES.get(risk_level, Decimal("20.0"))
        
        # Update credit score record
        credit_score.credit_score = scaled_score
        credit_score.payment_history_score = int(payment_history["score"])
        credit_score.credit_utilization_score = int(credit_utilization["score"])
        credit_score.length_of_history_score = int(history_length["score"])
        credit_score.payment_consistency_score = int(consistency["score"])
        
        credit_score.risk_level = risk_level
        credit_score.max_loan_amount = max_loan
        credit_score.recommended_interest_rate = interest_rate
        
        credit_score.total_payments = payment_history["total_payments"]
        credit_score.on_time_payments = payment_history["on_time"]
        credit_score.late_payments = payment_history["late"]
        credit_score.missed_payments = payment_history["missed"]
        credit_score.average_days_late = payment_history["avg_days_late"]
        
        # Update loan history
        loan_stats = await self._get_loan_statistics(guardian_id)
        credit_score.total_loans = loan_stats["total"]
        credit_score.active_loans = loan_stats["active"]
        credit_score.defaulted_loans = loan_stats["defaulted"]
        credit_score.total_loan_amount = loan_stats["total_amount"]
        credit_score.total_repaid_amount = loan_stats["repaid_amount"]
        
        credit_score.last_calculated = datetime.utcnow()
        
        await self.db.commit()
        await self.db.refresh(credit_score)
        
        logger.info(f"Credit score calculated for guardian {guardian_id}: {scaled_score} ({risk_level})")
        
        return credit_score

    async def _get_or_create_credit_score(self, guardian_id: int) -> CreditScore:
        """Get existing credit score or create a new one."""
        result = await self.db.execute(
            select(CreditScore).where(CreditScore.guardian_id == guardian_id)
        )
        credit_score = result.scalar_one_or_none()
        
        if not credit_score:
            credit_score = CreditScore(
                guardian_id=guardian_id,
                credit_score=500,  # Start with neutral score
                risk_level="medium"
            )
            self.db.add(credit_score)
            await self.db.flush()
        
        return credit_score

    async def _calculate_payment_history_score(self, guardian_id: int) -> Dict[str, Any]:
        """
        Calculate payment history score (35% weight).
        Based on on-time vs late vs missed payments.
        """
        # Get all payments for this guardian
        result = await self.db.execute(
            select(Payment).where(
                Payment.guardian_id == guardian_id,
                Payment.status.in_([PaymentStatus.COMPLETED, PaymentStatus.FAILED])
            )
        )
        payments = result.scalars().all()
        
        if not payments:
            return {
                "score": 500,  # Neutral score for no history
                "total_payments": 0,
                "on_time": 0,
                "late": 0,
                "missed": 0,
                "avg_days_late": 0
            }
        
        total_payments = len(payments)
        completed = [p for p in payments if p.status == PaymentStatus.COMPLETED]
        failed = [p for p in payments if p.status == PaymentStatus.FAILED]
        
        on_time = 0
        late = 0
        total_days_late = 0
        
        for payment in completed:
            if payment.invoice_id:
                # Get invoice to check due date
                invoice_result = await self.db.execute(
                    select(Invoice).where(Invoice.id == payment.invoice_id)
                )
                invoice = invoice_result.scalar_one_or_none()
                
                if invoice and invoice.due_date and payment.completed_at:
                    if payment.completed_at.date() <= invoice.due_date:
                        on_time += 1
                    else:
                        late += 1
                        days_late = (payment.completed_at.date() - invoice.due_date).days
                        total_days_late += days_late
                else:
                    on_time += 1  # Assume on-time if no due date
            else:
                on_time += 1
        
        missed = len(failed)
        avg_days_late = total_days_late / late if late > 0 else 0
        
        # Calculate score
        if total_payments == 0:
            score = 500
        else:
            on_time_ratio = on_time / total_payments
            late_ratio = late / total_payments
            missed_ratio = missed / total_payments
            
            # Scoring formula
            score = 1000 * on_time_ratio
            score -= 300 * late_ratio
            score -= 500 * missed_ratio
            score -= min(avg_days_late, 30) * 5  # Penalty for average days late
            
            score = max(0, min(1000, score))
        
        return {
            "score": score,
            "total_payments": total_payments,
            "on_time": on_time,
            "late": late,
            "missed": missed,
            "avg_days_late": avg_days_late
        }

    async def _calculate_credit_utilization_score(self, guardian_id: int) -> Dict[str, Any]:
        """
        Calculate credit utilization score (30% weight).
        Based on outstanding balances vs total credit.
        """
        # Get total invoiced amount
        total_invoiced_result = await self.db.execute(
            select(func.sum(Invoice.total_amount)).where(
                Invoice.guardian_id == guardian_id
            )
        )
        total_invoiced = total_invoiced_result.scalar() or Decimal("0")
        
        # Get total paid amount
        total_paid_result = await self.db.execute(
            select(func.sum(Invoice.paid_amount)).where(
                Invoice.guardian_id == guardian_id
            )
        )
        total_paid = total_paid_result.scalar() or Decimal("0")
        
        # Get active loan balance
        active_loan_result = await self.db.execute(
            select(func.sum(Loan.outstanding_amount)).where(
                Loan.guardian_id == guardian_id,
                Loan.status.in_([LoanStatus.ACTIVE, LoanStatus.DISBURSED])
            )
        )
        active_loan_balance = active_loan_result.scalar() or Decimal("0")
        
        if total_invoiced == 0:
            return {"score": 500, "utilization_ratio": 0}
        
        # Calculate utilization (lower is better)
        outstanding = total_invoiced - total_paid + active_loan_balance
        utilization_ratio = float(outstanding / total_invoiced) if total_invoiced > 0 else 0
        
        # Score calculation (lower utilization = higher score)
        if utilization_ratio <= 0.3:
            score = 1000
        elif utilization_ratio <= 0.5:
            score = 800
        elif utilization_ratio <= 0.7:
            score = 600
        elif utilization_ratio <= 0.9:
            score = 400
        else:
            score = 200
        
        return {
            "score": score,
            "utilization_ratio": utilization_ratio
        }

    async def _calculate_history_length_score(self, guardian_id: int) -> Dict[str, Any]:
        """
        Calculate length of credit history score (15% weight).
        Longer history = higher score.
        """
        # Get first payment date
        first_payment_result = await self.db.execute(
            select(func.min(Payment.created_at)).where(
                Payment.guardian_id == guardian_id
            )
        )
        first_payment_date = first_payment_result.scalar()
        
        if not first_payment_date:
            return {"score": 300, "months": 0}  # Low score for no history
        
        # Calculate months of history
        months = (datetime.utcnow() - first_payment_date).days / 30
        
        # Score based on history length
        if months >= 24:
            score = 1000
        elif months >= 18:
            score = 850
        elif months >= 12:
            score = 700
        elif months >= 6:
            score = 500
        elif months >= 3:
            score = 350
        else:
            score = 200
        
        return {
            "score": score,
            "months": months
        }

    async def _calculate_consistency_score(self, guardian_id: int) -> Dict[str, Any]:
        """
        Calculate payment consistency score (20% weight).
        Based on regular payment patterns.
        """
        # Get payment dates over last 12 months
        twelve_months_ago = datetime.utcnow() - timedelta(days=365)
        
        result = await self.db.execute(
            select(Payment.created_at).where(
                Payment.guardian_id == guardian_id,
                Payment.status == PaymentStatus.COMPLETED,
                Payment.created_at >= twelve_months_ago
            ).order_by(Payment.created_at)
        )
        payment_dates = [row[0] for row in result.fetchall()]
        
        if len(payment_dates) < 2:
            return {"score": 400, "consistency_ratio": 0}
        
        # Calculate payment intervals
        intervals = []
        for i in range(1, len(payment_dates)):
            interval = (payment_dates[i] - payment_dates[i-1]).days
            intervals.append(interval)
        
        if not intervals:
            return {"score": 400, "consistency_ratio": 0}
        
        # Calculate consistency (lower variance = higher consistency)
        avg_interval = sum(intervals) / len(intervals)
        variance = sum((i - avg_interval) ** 2 for i in intervals) / len(intervals)
        std_dev = variance ** 0.5
        
        # Coefficient of variation (lower is more consistent)
        cv = std_dev / avg_interval if avg_interval > 0 else 1
        
        # Score based on consistency
        if cv <= 0.2:
            score = 1000
        elif cv <= 0.4:
            score = 800
        elif cv <= 0.6:
            score = 600
        elif cv <= 0.8:
            score = 400
        else:
            score = 200
        
        return {
            "score": score,
            "consistency_ratio": 1 - min(cv, 1)
        }

    async def _get_average_payment_amount(self, guardian_id: int) -> Decimal:
        """Get average completed payment amount."""
        result = await self.db.execute(
            select(func.avg(Payment.amount)).where(
                Payment.guardian_id == guardian_id,
                Payment.status == PaymentStatus.COMPLETED
            )
        )
        avg = result.scalar()
        return Decimal(str(avg)) if avg else Decimal("0")

    async def _get_loan_statistics(self, guardian_id: int) -> Dict[str, Any]:
        """Get loan statistics for a guardian."""
        result = await self.db.execute(
            select(Loan).where(Loan.guardian_id == guardian_id)
        )
        loans = result.scalars().all()
        
        total = len(loans)
        active = len([l for l in loans if l.status in [LoanStatus.ACTIVE, LoanStatus.DISBURSED]])
        defaulted = len([l for l in loans if l.status == LoanStatus.DEFAULTED])
        total_amount = sum(l.principal_amount for l in loans)
        repaid_amount = sum(l.repaid_amount or Decimal("0") for l in loans)
        
        return {
            "total": total,
            "active": active,
            "defaulted": defaulted,
            "total_amount": total_amount,
            "repaid_amount": repaid_amount
        }

    def _determine_risk_level(self, score: int) -> str:
        """Determine risk level based on credit score."""
        for level, threshold in RISK_THRESHOLDS.items():
            if score >= threshold:
                return level
        return "very_high"

    def _calculate_max_loan_amount(self, risk_level: str, avg_payment: Decimal) -> Decimal:
        """Calculate maximum loan amount based on risk and payment history."""
        multiplier = LOAN_MULTIPLIERS.get(risk_level, 0)
        
        # Base max loan on average payment * multiplier * 12 (annual capacity)
        max_loan = avg_payment * Decimal(str(multiplier)) * Decimal("12")
        
        # Cap at reasonable limits
        min_cap = Decimal("10000")
        max_cap = Decimal("500000")
        
        if max_loan < min_cap and risk_level != "very_high":
            max_loan = min_cap
        if max_loan > max_cap:
            max_loan = max_cap
        
        return max_loan

    async def predict_default_probability(self, guardian_id: int) -> Dict[str, Any]:
        """
        Predict probability of loan default based on credit score and history.
        Returns probability and risk factors.
        """
        credit_score = await self.calculate_credit_score(guardian_id)
        
        # Base probability on credit score (inverse relationship)
        base_prob = (MAX_SCORE - credit_score.credit_score) / (MAX_SCORE - MIN_SCORE)
        
        # Adjust based on risk factors
        risk_factors = []
        adjustment = 0
        
        # Check recent late payments
        if credit_score.late_payments > credit_score.on_time_payments:
            risk_factors.append("High late payment ratio")
            adjustment += 0.1
        
        # Check defaulted loans
        if credit_score.defaulted_loans > 0:
            risk_factors.append("Previous loan default")
            adjustment += 0.2
        
        # Check active loan burden
        if credit_score.active_loans > 2:
            risk_factors.append("Multiple active loans")
            adjustment += 0.1
        
        # Calculate final probability
        default_probability = min(1.0, base_prob + adjustment)
        
        return {
            "probability": round(default_probability, 4),
            "percentage": f"{default_probability * 100:.1f}%",
            "risk_level": credit_score.risk_level,
            "risk_factors": risk_factors,
            "credit_score": credit_score.credit_score,
            "recommendation": self._get_recommendation(default_probability, risk_factors)
        }

    def _get_recommendation(self, probability: float, risk_factors: list) -> str:
        """Get loan recommendation based on default probability."""
        if probability < 0.1:
            return "Strongly recommended for approval"
        elif probability < 0.25:
            return "Recommended for approval with standard terms"
        elif probability < 0.4:
            return "Consider approval with higher interest rate or shorter tenure"
        elif probability < 0.6:
            return "High risk - consider requiring collateral or guarantor"
        else:
            return "Not recommended for approval due to high default risk"


# Singleton instance creator
def get_credit_scoring_service(db: AsyncSession) -> CreditScoringService:
    return CreditScoringService(db)
