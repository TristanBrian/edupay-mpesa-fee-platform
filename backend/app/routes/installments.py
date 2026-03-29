"""
Installment Plans API Routes
Flexible fee payment plans with automated scheduling.
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
    InstallmentPlan, Installment, Invoice, Student, Guardian,
    Payment, PaymentStatus
)

router = APIRouter(prefix="/installments", tags=["installments"])


# ============== SCHEMAS ==============

class InstallmentPlanCreate(BaseModel):
    invoice_id: int = Field(..., gt=0, description="Invoice ID")
    student_id: int = Field(..., gt=0, description="Student ID")
    guardian_id: Optional[int] = Field(None, gt=0, description="Guardian ID")
    school_id: Optional[int] = Field(None, gt=0, description="School ID")
    number_of_installments: int = Field(..., ge=2, le=12, description="Number of installments (2-12)")
    frequency: str = Field("monthly", description="Payment frequency")
    start_date: date = Field(..., description="First installment date")
    interest_rate: Decimal = Field(Decimal("0"), ge=0, le=30, description="Annual interest rate %")
    late_fee: Decimal = Field(Decimal("0"), ge=0, description="Late payment fee")

    @field_validator('frequency')
    @classmethod
    def validate_frequency(cls, v: str) -> str:
        allowed = ['weekly', 'bi-weekly', 'monthly']
        if v.lower() not in allowed:
            raise ValueError(f'Frequency must be one of: {", ".join(allowed)}')
        return v.lower()


class InstallmentPlanResponse(BaseModel):
    id: int
    plan_number: str
    invoice_id: int
    student_id: int
    total_amount: Decimal
    number_of_installments: int
    installment_amount: Decimal
    frequency: str
    start_date: date
    end_date: Optional[date]
    paid_amount: Decimal
    remaining_amount: Decimal
    paid_installments: int
    status: str
    interest_rate: Decimal
    late_fee: Decimal
    created_at: datetime

    class Config:
        from_attributes = True


class InstallmentResponse(BaseModel):
    id: int
    plan_id: int
    installment_number: int
    amount: Decimal
    due_date: date
    paid_amount: Decimal
    paid_date: Optional[datetime]
    status: str
    late_fee_applied: Decimal
    reminder_sent: bool

    class Config:
        from_attributes = True


class InstallmentPaymentRequest(BaseModel):
    amount: int = Field(..., gt=0, le=150000, description="Payment amount")
    phone: str = Field(..., description="M-Pesa phone number")


# ============== HELPER FUNCTIONS ==============

def generate_plan_number() -> str:
    """Generate unique installment plan number."""
    timestamp = datetime.now().strftime("%Y%m%d")
    random_part = secrets.token_hex(4).upper()
    return f"IP-{timestamp}-{random_part}"


def calculate_installment_dates(
    start_date: date,
    num_installments: int,
    frequency: str
) -> List[date]:
    """Calculate installment due dates based on frequency."""
    dates = [start_date]
    current = start_date
    
    for _ in range(num_installments - 1):
        if frequency == "weekly":
            current = current + timedelta(days=7)
        elif frequency == "bi-weekly":
            current = current + timedelta(days=14)
        else:  # monthly
            # Add roughly one month
            if current.month == 12:
                current = current.replace(year=current.year + 1, month=1)
            else:
                try:
                    current = current.replace(month=current.month + 1)
                except ValueError:
                    # Handle months with different number of days
                    current = current.replace(month=current.month + 2, day=1) - timedelta(days=1)
        dates.append(current)
    
    return dates


# ============== ROUTES ==============

@router.post("/plans", response_model=InstallmentPlanResponse)
async def create_installment_plan(
    plan_data: InstallmentPlanCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new installment plan for an invoice.
    Automatically generates individual installment records.
    """
    try:
        # Verify invoice exists and get amount
        invoice_result = await db.execute(
            select(Invoice).where(Invoice.id == plan_data.invoice_id)
        )
        invoice = invoice_result.scalar_one_or_none()
        
        if not invoice:
            raise HTTPException(status_code=404, detail="Invoice not found")
        
        # Calculate amounts
        total_amount = invoice.balance or invoice.total_amount
        
        # Apply interest if specified
        if plan_data.interest_rate > 0:
            interest_amount = total_amount * (plan_data.interest_rate / 100) * (plan_data.number_of_installments / 12)
            total_amount += interest_amount
        
        installment_amount = total_amount / plan_data.number_of_installments
        
        # Calculate end date
        installment_dates = calculate_installment_dates(
            plan_data.start_date,
            plan_data.number_of_installments,
            plan_data.frequency
        )
        end_date = installment_dates[-1]
        
        # Create the plan
        plan = InstallmentPlan(
            plan_number=generate_plan_number(),
            invoice_id=plan_data.invoice_id,
            student_id=plan_data.student_id,
            guardian_id=plan_data.guardian_id,
            school_id=plan_data.school_id or invoice.school_id,
            total_amount=total_amount,
            number_of_installments=plan_data.number_of_installments,
            installment_amount=installment_amount,
            frequency=plan_data.frequency,
            start_date=plan_data.start_date,
            end_date=end_date,
            remaining_amount=total_amount,
            interest_rate=plan_data.interest_rate,
            late_fee=plan_data.late_fee,
            status="active"
        )
        
        db.add(plan)
        await db.flush()
        
        # Create individual installments
        for i, due_date in enumerate(installment_dates, 1):
            installment = Installment(
                plan_id=plan.id,
                installment_number=i,
                amount=installment_amount,
                due_date=due_date,
                status="scheduled" if i > 1 else "pending"
            )
            db.add(installment)
        
        # Update invoice status
        invoice.status = "partial"
        
        await db.commit()
        await db.refresh(plan)
        
        return plan
        
    except SQLAlchemyError as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@router.get("/plans", response_model=List[InstallmentPlanResponse])
async def list_installment_plans(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    student_id: Optional[int] = None,
    guardian_id: Optional[int] = None,
    school_id: Optional[int] = None,
    status: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """List installment plans with optional filters."""
    query = select(InstallmentPlan)
    
    if student_id:
        query = query.where(InstallmentPlan.student_id == student_id)
    if guardian_id:
        query = query.where(InstallmentPlan.guardian_id == guardian_id)
    if school_id:
        query = query.where(InstallmentPlan.school_id == school_id)
    if status:
        query = query.where(InstallmentPlan.status == status)
    
    query = query.order_by(InstallmentPlan.created_at.desc()).offset(skip).limit(limit)
    
    result = await db.execute(query)
    plans = result.scalars().all()
    return plans


@router.get("/plans/{plan_id}", response_model=InstallmentPlanResponse)
async def get_installment_plan(plan_id: int, db: AsyncSession = Depends(get_db)):
    """Get a specific installment plan."""
    result = await db.execute(
        select(InstallmentPlan).where(InstallmentPlan.id == plan_id)
    )
    plan = result.scalar_one_or_none()
    
    if not plan:
        raise HTTPException(status_code=404, detail="Installment plan not found")
    
    return plan


@router.get("/plans/{plan_id}/schedule", response_model=List[InstallmentResponse])
async def get_installment_schedule(plan_id: int, db: AsyncSession = Depends(get_db)):
    """Get the installment schedule for a plan."""
    result = await db.execute(
        select(Installment)
        .where(Installment.plan_id == plan_id)
        .order_by(Installment.installment_number)
    )
    installments = result.scalars().all()
    
    if not installments:
        raise HTTPException(status_code=404, detail="No installments found for this plan")
    
    return installments


@router.post("/plans/{plan_id}/installments/{installment_number}/pay")
async def pay_installment(
    plan_id: int,
    installment_number: int,
    payment_request: InstallmentPaymentRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Pay an installment.
    Initiates M-Pesa STK push for the installment.
    """
    try:
        # Get the installment
        result = await db.execute(
            select(Installment).where(
                Installment.plan_id == plan_id,
                Installment.installment_number == installment_number
            )
        )
        installment = result.scalar_one_or_none()
        
        if not installment:
            raise HTTPException(status_code=404, detail="Installment not found")
        
        if installment.status == "paid":
            raise HTTPException(status_code=400, detail="Installment already paid")
        
        # Get the plan for reference
        plan_result = await db.execute(
            select(InstallmentPlan).where(InstallmentPlan.id == plan_id)
        )
        plan = plan_result.scalar_one_or_none()
        
        # Format phone
        phone = payment_request.phone
        if not phone.startswith("254"):
            phone = f"254{phone.lstrip('+0')}"
        
        # Calculate amount with any late fee
        today = datetime.now().date()
        amount = int(installment.amount)
        
        if today > installment.due_date and plan.late_fee > 0:
            late_fee = int(plan.late_fee)
            amount += late_fee
            installment.late_fee_applied = plan.late_fee
        
        # Create payment record
        payment = Payment(
            transaction_id=secrets.token_hex(10).upper(),
            amount=Decimal(str(payment_request.amount)),
            phone=phone,
            account_reference=f"{plan.plan_number}-{installment_number}",
            transaction_description=f"Installment {installment_number} of {plan.number_of_installments}",
            student_id=plan.student_id,
            guardian_id=plan.guardian_id,
            school_id=plan.school_id,
            invoice_id=plan.invoice_id,
            status=PaymentStatus.PENDING
        )
        
        db.add(payment)
        await db.flush()
        
        # Link payment to installment
        installment.payment_id = payment.id
        installment.status = "pending"
        
        await db.commit()
        
        # In production, this would trigger M-Pesa STK push
        # For now, return the payment details
        return {
            "success": True,
            "message": "Payment initiated",
            "transaction_id": payment.transaction_id,
            "amount": amount,
            "installment_number": installment_number,
            "plan_number": plan.plan_number
        }
        
    except SQLAlchemyError as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@router.post("/plans/{plan_id}/installments/{installment_number}/mark-paid")
async def mark_installment_paid(
    plan_id: int,
    installment_number: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Mark an installment as paid (for manual reconciliation).
    Updates plan totals accordingly.
    """
    try:
        # Get the installment
        result = await db.execute(
            select(Installment).where(
                Installment.plan_id == plan_id,
                Installment.installment_number == installment_number
            )
        )
        installment = result.scalar_one_or_none()
        
        if not installment:
            raise HTTPException(status_code=404, detail="Installment not found")
        
        if installment.status == "paid":
            raise HTTPException(status_code=400, detail="Installment already paid")
        
        # Update installment
        installment.status = "paid"
        installment.paid_amount = installment.amount
        installment.paid_date = datetime.utcnow()
        
        # Update plan
        plan_result = await db.execute(
            select(InstallmentPlan).where(InstallmentPlan.id == plan_id)
        )
        plan = plan_result.scalar_one_or_none()
        
        plan.paid_amount = (plan.paid_amount or Decimal("0")) + installment.amount
        plan.remaining_amount = plan.total_amount - plan.paid_amount
        plan.paid_installments += 1
        
        # Check if plan is complete
        if plan.paid_installments >= plan.number_of_installments:
            plan.status = "completed"
        
        # Update next installment to pending
        next_result = await db.execute(
            select(Installment).where(
                Installment.plan_id == plan_id,
                Installment.installment_number == installment_number + 1
            )
        )
        next_installment = next_result.scalar_one_or_none()
        if next_installment and next_installment.status == "scheduled":
            next_installment.status = "pending"
        
        await db.commit()
        
        return {
            "success": True,
            "message": "Installment marked as paid",
            "paid_installments": plan.paid_installments,
            "remaining_installments": plan.number_of_installments - plan.paid_installments,
            "remaining_amount": float(plan.remaining_amount)
        }
        
    except SQLAlchemyError as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@router.get("/overdue", response_model=List[InstallmentResponse])
async def get_overdue_installments(
    school_id: Optional[int] = None,
    days_overdue: int = Query(1, ge=1),
    db: AsyncSession = Depends(get_db)
):
    """Get all overdue installments."""
    cutoff_date = datetime.now().date() - timedelta(days=days_overdue)
    
    query = select(Installment).where(
        Installment.due_date < cutoff_date,
        Installment.status.in_(["pending", "scheduled"])
    )
    
    result = await db.execute(query)
    installments = result.scalars().all()
    
    # Update status to overdue
    for installment in installments:
        if installment.status != "overdue":
            installment.status = "overdue"
    
    await db.commit()
    
    return installments


@router.delete("/plans/{plan_id}")
async def cancel_installment_plan(plan_id: int, db: AsyncSession = Depends(get_db)):
    """Cancel an installment plan."""
    result = await db.execute(
        select(InstallmentPlan).where(InstallmentPlan.id == plan_id)
    )
    plan = result.scalar_one_or_none()
    
    if not plan:
        raise HTTPException(status_code=404, detail="Installment plan not found")
    
    if plan.status == "completed":
        raise HTTPException(status_code=400, detail="Cannot cancel a completed plan")
    
    plan.status = "cancelled"
    
    # Cancel pending installments
    installments_result = await db.execute(
        select(Installment).where(
            Installment.plan_id == plan_id,
            Installment.status.in_(["scheduled", "pending"])
        )
    )
    installments = installments_result.scalars().all()
    
    for installment in installments:
        installment.status = "cancelled"
    
    await db.commit()
    
    return {"message": "Installment plan cancelled successfully"}
