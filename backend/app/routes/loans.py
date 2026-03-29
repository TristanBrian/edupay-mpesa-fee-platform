"""
Micro-Loans API Routes
Embedded finance for school fee loans with credit scoring.
"""

from datetime import datetime, timedelta, date
from typing import Optional, List
from decimal import Decimal
import secrets

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.exc import SQLAlchemyError
from pydantic import BaseModel, Field, field_validator

from ..models.database import get_db
from ..models.payment import (
    Loan, LoanStatus, LoanRepayment, LoanRepaymentStatus,
    CreditScore, Guardian, Invoice, Payment, PaymentStatus
)
from ..services.credit_scoring import get_credit_scoring_service

router = APIRouter(prefix="/loans", tags=["loans"])


# ============== SCHEMAS ==============

class LoanApplicationRequest(BaseModel):
    guardian_id: int = Field(..., gt=0, description="Guardian ID")
    student_id: Optional[int] = Field(None, gt=0, description="Student ID")
    school_id: Optional[int] = Field(None, gt=0, description="School ID")
    invoice_id: Optional[int] = Field(None, gt=0, description="Invoice to pay")
    principal_amount: Decimal = Field(..., gt=0, le=500000, description="Loan amount")
    tenure_months: int = Field(..., ge=1, le=24, description="Loan duration in months")
    purpose: Optional[str] = Field("School fees", max_length=255)


class LoanResponse(BaseModel):
    id: int
    loan_number: str
    guardian_id: int
    student_id: Optional[int]
    principal_amount: Decimal
    interest_rate: Decimal
    processing_fee: Decimal
    total_amount: Decimal
    tenure_months: int
    monthly_repayment: Decimal
    repayment_start_date: Optional[date]
    disbursed_amount: Decimal
    repaid_amount: Decimal
    outstanding_amount: Optional[Decimal]
    status: str
    credit_score_at_application: Optional[int]
    approval_notes: Optional[str]
    rejection_reason: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class LoanRepaymentResponse(BaseModel):
    id: int
    loan_id: int
    repayment_number: int
    scheduled_amount: Decimal
    principal_component: Optional[Decimal]
    interest_component: Optional[Decimal]
    due_date: date
    paid_amount: Decimal
    paid_date: Optional[datetime]
    late_fee: Decimal
    days_overdue: int
    status: str

    class Config:
        from_attributes = True


class CreditScoreResponse(BaseModel):
    guardian_id: int
    credit_score: int
    risk_level: str
    max_loan_amount: Decimal
    recommended_interest_rate: Decimal
    payment_history_score: int
    total_payments: int
    on_time_payments: int
    late_payments: int
    total_loans: int
    active_loans: int
    defaulted_loans: int
    last_calculated: datetime

    class Config:
        from_attributes = True


class LoanApprovalRequest(BaseModel):
    approved: bool
    notes: Optional[str] = Field(None, max_length=500)
    adjusted_interest_rate: Optional[Decimal] = Field(None, ge=0, le=50)
    approved_by: Optional[str] = Field(None, max_length=100)


class RepaymentRequest(BaseModel):
    amount: int = Field(..., gt=0, le=150000, description="Payment amount")
    phone: str = Field(..., description="M-Pesa phone number")


# ============== HELPER FUNCTIONS ==============

def generate_loan_number() -> str:
    """Generate unique loan number."""
    timestamp = datetime.now().strftime("%Y%m%d")
    random_part = secrets.token_hex(4).upper()
    return f"LN-{timestamp}-{random_part}"


def calculate_monthly_repayment(
    principal: Decimal,
    annual_rate: Decimal,
    months: int
) -> Decimal:
    """
    Calculate monthly repayment using reducing balance method.
    EMI = P * r * (1+r)^n / ((1+r)^n - 1)
    """
    if annual_rate == 0:
        return principal / months
    
    monthly_rate = annual_rate / Decimal("100") / Decimal("12")
    
    # Calculate EMI
    factor = (1 + monthly_rate) ** months
    emi = principal * monthly_rate * factor / (factor - 1)
    
    return round(emi, 2)


def generate_repayment_schedule(
    loan_id: int,
    principal: Decimal,
    annual_rate: Decimal,
    months: int,
    start_date: date
) -> List[LoanRepayment]:
    """Generate amortization schedule for a loan."""
    repayments = []
    monthly_rate = annual_rate / Decimal("100") / Decimal("12")
    emi = calculate_monthly_repayment(principal, annual_rate, months)
    balance = principal
    
    current_date = start_date
    
    for i in range(1, months + 1):
        interest_component = balance * monthly_rate
        principal_component = emi - interest_component
        
        # Adjust for final payment rounding
        if i == months:
            principal_component = balance
            emi = principal_component + interest_component
        
        repayment = LoanRepayment(
            loan_id=loan_id,
            repayment_number=i,
            scheduled_amount=round(emi, 2),
            principal_component=round(principal_component, 2),
            interest_component=round(interest_component, 2),
            due_date=current_date,
            status="scheduled"
        )
        repayments.append(repayment)
        
        balance -= principal_component
        
        # Move to next month
        if current_date.month == 12:
            current_date = current_date.replace(year=current_date.year + 1, month=1)
        else:
            try:
                current_date = current_date.replace(month=current_date.month + 1)
            except ValueError:
                current_date = current_date.replace(month=current_date.month + 2, day=1) - timedelta(days=1)
    
    return repayments


# ============== CREDIT SCORING ROUTES ==============

@router.get("/credit-score/{guardian_id}", response_model=CreditScoreResponse)
async def get_credit_score(guardian_id: int, db: AsyncSession = Depends(get_db)):
    """
    Get or calculate credit score for a guardian.
    Used to determine loan eligibility and terms.
    """
    credit_service = get_credit_scoring_service(db)
    credit_score = await credit_service.calculate_credit_score(guardian_id)
    
    return credit_score


@router.get("/credit-score/{guardian_id}/default-prediction")
async def predict_default(guardian_id: int, db: AsyncSession = Depends(get_db)):
    """
    Predict probability of loan default for a guardian.
    Used for risk assessment and loan approval decisions.
    """
    credit_service = get_credit_scoring_service(db)
    prediction = await credit_service.predict_default_probability(guardian_id)
    
    return prediction


@router.get("/eligibility/{guardian_id}")
async def check_loan_eligibility(
    guardian_id: int,
    amount: Decimal = Query(..., gt=0),
    tenure_months: int = Query(..., ge=1, le=24),
    db: AsyncSession = Depends(get_db)
):
    """
    Check if a guardian is eligible for a loan of the specified amount.
    Returns eligibility status, recommended terms, and any issues.
    """
    credit_service = get_credit_scoring_service(db)
    credit_score = await credit_service.calculate_credit_score(guardian_id)
    
    # Check eligibility
    eligible = True
    issues = []
    
    if credit_score.risk_level == "very_high":
        eligible = False
        issues.append("Credit score too low for loan approval")
    
    if amount > credit_score.max_loan_amount:
        eligible = False
        issues.append(f"Requested amount exceeds maximum eligible amount of {credit_score.max_loan_amount}")
    
    if credit_score.active_loans >= 3:
        eligible = False
        issues.append("Maximum number of active loans reached")
    
    if credit_score.defaulted_loans > 0:
        issues.append("Previous loan default on record - manual review required")
        if credit_score.defaulted_loans >= 2:
            eligible = False
    
    # Calculate terms if eligible
    monthly_payment = None
    total_repayment = None
    
    if eligible:
        monthly_payment = float(calculate_monthly_repayment(
            amount,
            credit_score.recommended_interest_rate,
            tenure_months
        ))
        total_repayment = round(monthly_payment * tenure_months, 2)
    
    return {
        "eligible": eligible,
        "guardian_id": guardian_id,
        "requested_amount": float(amount),
        "tenure_months": tenure_months,
        "credit_score": credit_score.credit_score,
        "risk_level": credit_score.risk_level,
        "max_eligible_amount": float(credit_score.max_loan_amount),
        "recommended_interest_rate": float(credit_score.recommended_interest_rate),
        "estimated_monthly_payment": monthly_payment,
        "estimated_total_repayment": total_repayment,
        "issues": issues,
        "active_loans": credit_score.active_loans
    }


# ============== LOAN APPLICATION ROUTES ==============

@router.post("/apply", response_model=LoanResponse)
async def apply_for_loan(
    application: LoanApplicationRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Submit a loan application.
    Calculates credit score, determines interest rate, and creates loan record.
    """
    try:
        # Calculate credit score
        credit_service = get_credit_scoring_service(db)
        credit_score = await credit_service.calculate_credit_score(application.guardian_id)
        
        # Check basic eligibility
        if credit_score.risk_level == "very_high":
            raise HTTPException(
                status_code=400,
                detail="Loan application rejected: Credit score does not meet minimum requirements"
            )
        
        if application.principal_amount > credit_score.max_loan_amount:
            raise HTTPException(
                status_code=400,
                detail=f"Requested amount exceeds maximum eligible amount of {credit_score.max_loan_amount}"
            )
        
        # Determine interest rate based on credit score
        interest_rate = credit_score.recommended_interest_rate
        
        # Calculate processing fee (1% of principal, min 500)
        processing_fee = max(application.principal_amount * Decimal("0.01"), Decimal("500"))
        
        # Calculate total amount and monthly repayment
        total_interest = application.principal_amount * interest_rate / 100 * application.tenure_months / 12
        total_amount = application.principal_amount + total_interest + processing_fee
        monthly_repayment = calculate_monthly_repayment(
            application.principal_amount + processing_fee,
            interest_rate,
            application.tenure_months
        )
        
        # Create loan
        loan = Loan(
            loan_number=generate_loan_number(),
            guardian_id=application.guardian_id,
            student_id=application.student_id,
            school_id=application.school_id,
            invoice_id=application.invoice_id,
            principal_amount=application.principal_amount,
            interest_rate=interest_rate,
            processing_fee=processing_fee,
            total_amount=total_amount,
            tenure_months=application.tenure_months,
            monthly_repayment=monthly_repayment,
            outstanding_amount=total_amount,
            status=LoanStatus.PENDING_APPROVAL,
            credit_score_at_application=credit_score.credit_score
        )
        
        db.add(loan)
        await db.commit()
        await db.refresh(loan)
        
        return loan
        
    except SQLAlchemyError as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@router.get("/", response_model=List[LoanResponse])
async def list_loans(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    guardian_id: Optional[int] = None,
    student_id: Optional[int] = None,
    school_id: Optional[int] = None,
    status: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """List loans with optional filters."""
    query = select(Loan)
    
    if guardian_id:
        query = query.where(Loan.guardian_id == guardian_id)
    if student_id:
        query = query.where(Loan.student_id == student_id)
    if school_id:
        query = query.where(Loan.school_id == school_id)
    if status:
        query = query.where(Loan.status == status)
    
    query = query.order_by(Loan.created_at.desc()).offset(skip).limit(limit)
    
    result = await db.execute(query)
    loans = result.scalars().all()
    return loans


@router.get("/{loan_id}", response_model=LoanResponse)
async def get_loan(loan_id: int, db: AsyncSession = Depends(get_db)):
    """Get a specific loan."""
    result = await db.execute(select(Loan).where(Loan.id == loan_id))
    loan = result.scalar_one_or_none()
    
    if not loan:
        raise HTTPException(status_code=404, detail="Loan not found")
    
    return loan


@router.get("/{loan_id}/repayments", response_model=List[LoanRepaymentResponse])
async def get_loan_repayments(loan_id: int, db: AsyncSession = Depends(get_db)):
    """Get repayment schedule for a loan."""
    result = await db.execute(
        select(LoanRepayment)
        .where(LoanRepayment.loan_id == loan_id)
        .order_by(LoanRepayment.repayment_number)
    )
    repayments = result.scalars().all()
    
    if not repayments:
        raise HTTPException(status_code=404, detail="No repayments found for this loan")
    
    return repayments


# ============== LOAN APPROVAL ROUTES ==============

@router.post("/{loan_id}/approve")
async def approve_or_reject_loan(
    loan_id: int,
    decision: LoanApprovalRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Approve or reject a loan application.
    If approved, generates repayment schedule.
    """
    try:
        result = await db.execute(select(Loan).where(Loan.id == loan_id))
        loan = result.scalar_one_or_none()
        
        if not loan:
            raise HTTPException(status_code=404, detail="Loan not found")
        
        if loan.status != LoanStatus.PENDING_APPROVAL:
            raise HTTPException(
                status_code=400,
                detail=f"Loan is not pending approval (current status: {loan.status})"
            )
        
        if decision.approved:
            # Apply adjusted interest rate if provided
            if decision.adjusted_interest_rate is not None:
                loan.interest_rate = decision.adjusted_interest_rate
                # Recalculate monthly payment
                loan.monthly_repayment = calculate_monthly_repayment(
                    loan.principal_amount + loan.processing_fee,
                    decision.adjusted_interest_rate,
                    loan.tenure_months
                )
            
            loan.status = LoanStatus.APPROVED
            loan.approval_notes = decision.notes
            loan.approved_by = decision.approved_by
            loan.approved_at = datetime.utcnow()
            
            await db.commit()
            
            return {
                "success": True,
                "message": "Loan approved successfully",
                "loan_number": loan.loan_number,
                "status": loan.status.value
            }
        else:
            loan.status = LoanStatus.REJECTED
            loan.rejection_reason = decision.notes
            
            await db.commit()
            
            return {
                "success": True,
                "message": "Loan application rejected",
                "loan_number": loan.loan_number,
                "status": loan.status.value,
                "reason": decision.notes
            }
            
    except SQLAlchemyError as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@router.post("/{loan_id}/disburse")
async def disburse_loan(
    loan_id: int,
    disbursement_method: str = Query("direct_to_school"),
    db: AsyncSession = Depends(get_db)
):
    """
    Disburse an approved loan.
    Creates repayment schedule and updates loan status.
    """
    try:
        result = await db.execute(select(Loan).where(Loan.id == loan_id))
        loan = result.scalar_one_or_none()
        
        if not loan:
            raise HTTPException(status_code=404, detail="Loan not found")
        
        if loan.status != LoanStatus.APPROVED:
            raise HTTPException(
                status_code=400,
                detail=f"Loan must be approved before disbursement (current status: {loan.status})"
            )
        
        # Set repayment start date (1 month from now)
        repayment_start = datetime.now().date() + timedelta(days=30)
        repayment_end = repayment_start
        for _ in range(loan.tenure_months - 1):
            if repayment_end.month == 12:
                repayment_end = repayment_end.replace(year=repayment_end.year + 1, month=1)
            else:
                repayment_end = repayment_end.replace(month=repayment_end.month + 1)
        
        # Update loan
        loan.status = LoanStatus.DISBURSED
        loan.disbursed_amount = loan.principal_amount
        loan.disbursed_at = datetime.utcnow()
        loan.disbursement_method = disbursement_method
        loan.disbursement_reference = secrets.token_hex(8).upper()
        loan.repayment_start_date = repayment_start
        loan.repayment_end_date = repayment_end
        
        await db.flush()
        
        # Generate repayment schedule
        repayments = generate_repayment_schedule(
            loan.id,
            loan.principal_amount + loan.processing_fee,
            loan.interest_rate,
            loan.tenure_months,
            repayment_start
        )
        
        for repayment in repayments:
            db.add(repayment)
        
        # Mark first repayment as pending
        repayments[0].status = "pending"
        
        # If linked to invoice, update invoice
        if loan.invoice_id:
            invoice_result = await db.execute(
                select(Invoice).where(Invoice.id == loan.invoice_id)
            )
            invoice = invoice_result.scalar_one_or_none()
            if invoice:
                invoice.paid_amount = (invoice.paid_amount or Decimal("0")) + loan.principal_amount
                invoice.balance = invoice.total_amount - invoice.paid_amount
                if invoice.balance <= 0:
                    invoice.status = "paid"
                else:
                    invoice.status = "partial"
        
        # Update credit score
        credit_result = await db.execute(
            select(CreditScore).where(CreditScore.guardian_id == loan.guardian_id)
        )
        credit_score = credit_result.scalar_one_or_none()
        if credit_score:
            credit_score.active_loans += 1
            credit_score.total_loan_amount = (credit_score.total_loan_amount or Decimal("0")) + loan.principal_amount
        
        await db.commit()
        
        return {
            "success": True,
            "message": "Loan disbursed successfully",
            "loan_number": loan.loan_number,
            "disbursed_amount": float(loan.disbursed_amount),
            "disbursement_reference": loan.disbursement_reference,
            "repayment_start_date": repayment_start.isoformat(),
            "monthly_repayment": float(loan.monthly_repayment),
            "total_repayments": loan.tenure_months
        }
        
    except SQLAlchemyError as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


# ============== REPAYMENT ROUTES ==============

@router.post("/{loan_id}/repayments/{repayment_number}/pay")
async def make_repayment(
    loan_id: int,
    repayment_number: int,
    payment_request: RepaymentRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Make a loan repayment.
    Initiates M-Pesa STK push for the repayment.
    """
    try:
        # Get the repayment
        result = await db.execute(
            select(LoanRepayment).where(
                LoanRepayment.loan_id == loan_id,
                LoanRepayment.repayment_number == repayment_number
            )
        )
        repayment = result.scalar_one_or_none()
        
        if not repayment:
            raise HTTPException(status_code=404, detail="Repayment not found")
        
        if repayment.status == "paid":
            raise HTTPException(status_code=400, detail="Repayment already completed")
        
        # Get the loan
        loan_result = await db.execute(select(Loan).where(Loan.id == loan_id))
        loan = loan_result.scalar_one_or_none()
        
        # Format phone
        phone = payment_request.phone
        if not phone.startswith("254"):
            phone = f"254{phone.lstrip('+0')}"
        
        # Check for late fee
        today = datetime.now().date()
        amount = payment_request.amount
        
        if today > repayment.due_date:
            days_overdue = (today - repayment.due_date).days
            late_fee = min(days_overdue * 100, 5000)  # 100 per day, max 5000
            repayment.late_fee = Decimal(str(late_fee))
            repayment.days_overdue = days_overdue
        
        # Create payment record
        payment = Payment(
            transaction_id=secrets.token_hex(10).upper(),
            amount=Decimal(str(payment_request.amount)),
            phone=phone,
            account_reference=f"{loan.loan_number}-R{repayment_number}",
            transaction_description=f"Loan repayment {repayment_number} of {loan.tenure_months}",
            guardian_id=loan.guardian_id,
            student_id=loan.student_id,
            school_id=loan.school_id,
            status=PaymentStatus.PENDING
        )
        
        db.add(payment)
        await db.flush()
        
        repayment.payment_id = payment.id
        repayment.status = "pending"
        
        await db.commit()
        
        return {
            "success": True,
            "message": "Repayment initiated",
            "transaction_id": payment.transaction_id,
            "amount": amount,
            "repayment_number": repayment_number,
            "loan_number": loan.loan_number,
            "late_fee_applied": float(repayment.late_fee)
        }
        
    except SQLAlchemyError as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@router.post("/{loan_id}/repayments/{repayment_number}/mark-paid")
async def mark_repayment_paid(
    loan_id: int,
    repayment_number: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Mark a repayment as paid (for manual reconciliation).
    """
    try:
        result = await db.execute(
            select(LoanRepayment).where(
                LoanRepayment.loan_id == loan_id,
                LoanRepayment.repayment_number == repayment_number
            )
        )
        repayment = result.scalar_one_or_none()
        
        if not repayment:
            raise HTTPException(status_code=404, detail="Repayment not found")
        
        if repayment.status == "paid":
            raise HTTPException(status_code=400, detail="Repayment already completed")
        
        # Update repayment
        repayment.status = "paid"
        repayment.paid_amount = repayment.scheduled_amount + repayment.late_fee
        repayment.paid_date = datetime.utcnow()
        
        # Update loan
        loan_result = await db.execute(select(Loan).where(Loan.id == loan_id))
        loan = loan_result.scalar_one_or_none()
        
        loan.repaid_amount = (loan.repaid_amount or Decimal("0")) + repayment.paid_amount
        loan.outstanding_amount = loan.total_amount - loan.repaid_amount
        
        # Check if loan is fully repaid
        remaining_repayments = await db.execute(
            select(LoanRepayment).where(
                LoanRepayment.loan_id == loan_id,
                LoanRepayment.status.in_(["scheduled", "pending", "overdue"])
            )
        )
        if not remaining_repayments.scalars().all():
            loan.status = LoanStatus.PAID
            
            # Update credit score
            credit_result = await db.execute(
                select(CreditScore).where(CreditScore.guardian_id == loan.guardian_id)
            )
            credit_score = credit_result.scalar_one_or_none()
            if credit_score:
                credit_score.active_loans = max(0, credit_score.active_loans - 1)
                credit_score.total_repaid_amount = (credit_score.total_repaid_amount or Decimal("0")) + loan.repaid_amount
        else:
            loan.status = LoanStatus.ACTIVE
            
            # Mark next repayment as pending
            next_result = await db.execute(
                select(LoanRepayment).where(
                    LoanRepayment.loan_id == loan_id,
                    LoanRepayment.repayment_number == repayment_number + 1
                )
            )
            next_repayment = next_result.scalar_one_or_none()
            if next_repayment and next_repayment.status == "scheduled":
                next_repayment.status = "pending"
        
        await db.commit()
        
        return {
            "success": True,
            "message": "Repayment marked as paid",
            "repaid_amount": float(loan.repaid_amount),
            "outstanding_amount": float(loan.outstanding_amount),
            "loan_status": loan.status.value
        }
        
    except SQLAlchemyError as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@router.get("/overdue-repayments")
async def get_overdue_repayments(
    school_id: Optional[int] = None,
    days_overdue: int = Query(1, ge=1),
    db: AsyncSession = Depends(get_db)
):
    """Get all overdue loan repayments."""
    cutoff_date = datetime.now().date() - timedelta(days=days_overdue)
    
    query = select(LoanRepayment).where(
        LoanRepayment.due_date < cutoff_date,
        LoanRepayment.status.in_(["pending", "scheduled"])
    )
    
    result = await db.execute(query)
    repayments = result.scalars().all()
    
    # Update status to overdue and calculate fees
    for repayment in repayments:
        if repayment.status != "overdue":
            repayment.status = "overdue"
            days = (datetime.now().date() - repayment.due_date).days
            repayment.days_overdue = days
            repayment.late_fee = Decimal(str(min(days * 100, 5000)))
    
    await db.commit()
    
    return [
        {
            "id": r.id,
            "loan_id": r.loan_id,
            "repayment_number": r.repayment_number,
            "scheduled_amount": float(r.scheduled_amount),
            "due_date": r.due_date.isoformat(),
            "days_overdue": r.days_overdue,
            "late_fee": float(r.late_fee),
            "total_due": float(r.scheduled_amount + r.late_fee)
        }
        for r in repayments
    ]
