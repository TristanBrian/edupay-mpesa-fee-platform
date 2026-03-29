from sqlalchemy import Column, String, Integer, DateTime, Date, Enum as SQLEnum, ForeignKey, Numeric, Text, JSON, Boolean, Float
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
import enum

Base = declarative_base()


class PaymentStatus(str, enum.Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class StudentStatus(str, enum.Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    GRADUATED = "graduated"


class InvoiceStatus(str, enum.Enum):
    PENDING = "pending"
    PARTIAL = "partial"
    PAID = "paid"
    OVERDUE = "overdue"
    CANCELLED = "cancelled"


class InstallmentStatus(str, enum.Enum):
    SCHEDULED = "scheduled"
    PENDING = "pending"
    PAID = "paid"
    OVERDUE = "overdue"
    CANCELLED = "cancelled"


class LoanStatus(str, enum.Enum):
    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved"
    REJECTED = "rejected"
    DISBURSED = "disbursed"
    ACTIVE = "active"
    PAID = "paid"
    DEFAULTED = "defaulted"
    CANCELLED = "cancelled"


class LoanRepaymentStatus(str, enum.Enum):
    SCHEDULED = "scheduled"
    PENDING = "pending"
    PAID = "paid"
    OVERDUE = "overdue"
    PARTIAL = "partial"


class School(Base):
    __tablename__ = "schools"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    code = Column(String(50), unique=True, nullable=False)
    address = Column(Text)
    phone = Column(String(20))
    email = Column(String(100))
    mpesa_shortcode = Column(String(20))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    students = relationship("Student", back_populates="school")
    guardians = relationship("Guardian", back_populates="school")
    invoices = relationship("Invoice")


class Guardian(Base):
    __tablename__ = "guardians"

    id = Column(Integer, primary_key=True, index=True)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    email = Column(String(100), unique=True)
    phone = Column(String(20), nullable=False)
    id_number = Column(String(50))
    relationship_type = Column("relationship", String(50))
    school_id = Column(Integer, ForeignKey("schools.id"))
    address = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    school = relationship("School", back_populates="guardians")
    students = relationship("Student", back_populates="guardian_info")
    invoices = relationship("Invoice", back_populates="guardian_info")
    payments = relationship("Payment", back_populates="guardian_info")


class Student(Base):
    __tablename__ = "students"

    id = Column(Integer, primary_key=True, index=True)
    admission_number = Column(String(50), unique=True, nullable=False)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    date_of_birth = Column(Date)
    gender = Column(String(10))
    class_name = Column(String(50), nullable=False)
    stream = Column(String(20))
    guardian_id = Column(Integer, ForeignKey("guardians.id"))
    school_id = Column(Integer, ForeignKey("schools.id"))
    status = Column(String(20), default="active")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    guardian_info = relationship("Guardian", back_populates="students")
    school = relationship("School", back_populates="students")
    invoices = relationship("Invoice")
    payments = relationship("Payment")


class Invoice(Base):
    __tablename__ = "invoices"

    id = Column(Integer, primary_key=True, index=True)
    invoice_number = Column(String(50), unique=True, nullable=False)
    student_id = Column(Integer, ForeignKey("students.id"))
    guardian_id = Column(Integer, ForeignKey("guardians.id"))
    school_id = Column(Integer, ForeignKey("schools.id"))
    term = Column(String(20))
    year = Column(Integer)
    total_amount = Column(Numeric(12, 2), nullable=False)
    paid_amount = Column(Numeric(12, 2), default=0)
    balance = Column(Numeric(12, 2), nullable=False)
    due_date = Column(Date)
    status = Column(String(20), default="pending")
    description = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    student = relationship("Student")
    guardian_info = relationship("Guardian", back_populates="invoices")
    school = relationship("School")
    items = relationship("InvoiceItem", back_populates="invoice", cascade="all, delete-orphan")
    payments = relationship("Payment")


class InvoiceItem(Base):
    __tablename__ = "invoice_items"

    id = Column(Integer, primary_key=True, index=True)
    invoice_id = Column(Integer, ForeignKey("invoices.id", ondelete="CASCADE"))
    description = Column(String(255), nullable=False)
    quantity = Column(Integer, default=1)
    unit_price = Column(Numeric(12, 2), nullable=False)
    total_price = Column(Numeric(12, 2), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    invoice = relationship("Invoice", back_populates="items")


class Payment(Base):
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True, index=True)
    transaction_id = Column(String(50), unique=True, index=True, nullable=False)
    checkout_request_id = Column(String(100), index=True)
    merchant_request_id = Column(String(100))
    invoice_id = Column(Integer, ForeignKey("invoices.id"))
    student_id = Column(Integer, ForeignKey("students.id"))
    guardian_id = Column(Integer, ForeignKey("guardians.id"))
    school_id = Column(Integer, ForeignKey("schools.id"))
    amount = Column(Numeric(12, 2), nullable=False)
    phone = Column(String(20), nullable=False)
    account_reference = Column(String(100))
    transaction_description = Column(String(255))
    status = Column(String(20), default="pending")
    mpesa_receipt_number = Column(String(50))
    result_code = Column(String(10))
    result_desc = Column(String(255))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at = Column(DateTime)

    invoice = relationship("Invoice")
    student = relationship("Student")
    guardian_info = relationship("Guardian", back_populates="payments")
    school = relationship("School")
    transactions = relationship("PaymentTransaction", back_populates="payment", cascade="all, delete-orphan")


class PaymentTransaction(Base):
    __tablename__ = "payment_transactions"

    id = Column(Integer, primary_key=True, index=True)
    payment_id = Column(Integer, ForeignKey("payments.id"))
    action = Column(String(50), nullable=False)
    status_from = Column(String(20))
    status_to = Column(String(20))
    amount = Column(Numeric(12, 2))
    details = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)

    payment = relationship("Payment", back_populates="transactions")


# ============== INSTALLMENT PLANS ==============

class InstallmentPlan(Base):
    """Flexible fee payment plans allowing students to pay in installments"""
    __tablename__ = "installment_plans"

    id = Column(Integer, primary_key=True, index=True)
    plan_number = Column(String(50), unique=True, nullable=False, index=True)
    invoice_id = Column(Integer, ForeignKey("invoices.id"), nullable=False)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False)
    guardian_id = Column(Integer, ForeignKey("guardians.id"))
    school_id = Column(Integer, ForeignKey("schools.id"))
    
    # Plan details
    total_amount = Column(Numeric(12, 2), nullable=False)
    number_of_installments = Column(Integer, nullable=False)
    installment_amount = Column(Numeric(12, 2), nullable=False)
    frequency = Column(String(20), default="monthly")  # weekly, bi-weekly, monthly
    start_date = Column(Date, nullable=False)
    end_date = Column(Date)
    
    # Tracking
    paid_amount = Column(Numeric(12, 2), default=0)
    remaining_amount = Column(Numeric(12, 2))
    paid_installments = Column(Integer, default=0)
    status = Column(String(20), default="active")
    
    # Interest/Fees
    interest_rate = Column(Numeric(5, 2), default=0)  # Annual interest rate percentage
    late_fee = Column(Numeric(10, 2), default=0)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    invoice = relationship("Invoice")
    student = relationship("Student")
    guardian = relationship("Guardian")
    school = relationship("School")
    installments = relationship("Installment", back_populates="plan", cascade="all, delete-orphan")


class Installment(Base):
    """Individual installment within a payment plan"""
    __tablename__ = "installments"

    id = Column(Integer, primary_key=True, index=True)
    plan_id = Column(Integer, ForeignKey("installment_plans.id", ondelete="CASCADE"), nullable=False)
    installment_number = Column(Integer, nullable=False)
    
    amount = Column(Numeric(12, 2), nullable=False)
    due_date = Column(Date, nullable=False)
    paid_amount = Column(Numeric(12, 2), default=0)
    paid_date = Column(DateTime)
    
    status = Column(String(20), default="scheduled")
    late_fee_applied = Column(Numeric(10, 2), default=0)
    
    # Link to actual payment
    payment_id = Column(Integer, ForeignKey("payments.id"))
    
    reminder_sent = Column(Boolean, default=False)
    reminder_sent_at = Column(DateTime)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    plan = relationship("InstallmentPlan", back_populates="installments")
    payment = relationship("Payment")


# ============== MICRO-LOANS (EMBEDDED FINANCE) ==============

class CreditScore(Base):
    """Credit scoring for students/guardians based on payment history"""
    __tablename__ = "credit_scores"

    id = Column(Integer, primary_key=True, index=True)
    guardian_id = Column(Integer, ForeignKey("guardians.id"), nullable=False, unique=True)
    
    # Credit Score Components (0-1000 scale)
    credit_score = Column(Integer, default=500)
    payment_history_score = Column(Integer, default=0)  # 35% weight
    credit_utilization_score = Column(Integer, default=0)  # 30% weight
    length_of_history_score = Column(Integer, default=0)  # 15% weight
    payment_consistency_score = Column(Integer, default=0)  # 20% weight
    
    # Risk Assessment
    risk_level = Column(String(20), default="medium")  # low, medium, high, very_high
    max_loan_amount = Column(Numeric(12, 2), default=0)
    recommended_interest_rate = Column(Numeric(5, 2), default=15.0)
    
    # Historical Data
    total_payments = Column(Integer, default=0)
    on_time_payments = Column(Integer, default=0)
    late_payments = Column(Integer, default=0)
    missed_payments = Column(Integer, default=0)
    average_days_late = Column(Float, default=0)
    
    # Loan History
    total_loans = Column(Integer, default=0)
    active_loans = Column(Integer, default=0)
    defaulted_loans = Column(Integer, default=0)
    total_loan_amount = Column(Numeric(14, 2), default=0)
    total_repaid_amount = Column(Numeric(14, 2), default=0)
    
    last_calculated = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    guardian = relationship("Guardian")


class Loan(Base):
    """Micro-loans for school fees"""
    __tablename__ = "loans"

    id = Column(Integer, primary_key=True, index=True)
    loan_number = Column(String(50), unique=True, nullable=False, index=True)
    
    # Applicant Info
    guardian_id = Column(Integer, ForeignKey("guardians.id"), nullable=False)
    student_id = Column(Integer, ForeignKey("students.id"))
    school_id = Column(Integer, ForeignKey("schools.id"))
    invoice_id = Column(Integer, ForeignKey("invoices.id"))
    
    # Loan Details
    principal_amount = Column(Numeric(12, 2), nullable=False)
    interest_rate = Column(Numeric(5, 2), nullable=False)  # Annual percentage
    processing_fee = Column(Numeric(10, 2), default=0)
    total_amount = Column(Numeric(12, 2), nullable=False)  # Principal + interest + fees
    
    # Repayment Terms
    tenure_months = Column(Integer, nullable=False)  # Loan duration in months
    monthly_repayment = Column(Numeric(12, 2), nullable=False)
    repayment_start_date = Column(Date)
    repayment_end_date = Column(Date)
    
    # Tracking
    disbursed_amount = Column(Numeric(12, 2), default=0)
    repaid_amount = Column(Numeric(12, 2), default=0)
    outstanding_amount = Column(Numeric(12, 2))
    
    status = Column(String(30), default="pending_approval")
    
    # Approval/Rejection
    credit_score_at_application = Column(Integer)
    approval_notes = Column(Text)
    rejection_reason = Column(Text)
    approved_by = Column(String(100))
    approved_at = Column(DateTime)
    
    # Disbursement
    disbursed_at = Column(DateTime)
    disbursement_method = Column(String(50))  # direct_to_school, to_guardian
    disbursement_reference = Column(String(100))
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    guardian = relationship("Guardian")
    student = relationship("Student")
    school = relationship("School")
    invoice = relationship("Invoice")
    repayments = relationship("LoanRepayment", back_populates="loan", cascade="all, delete-orphan")


class LoanRepayment(Base):
    """Scheduled and actual loan repayments"""
    __tablename__ = "loan_repayments"

    id = Column(Integer, primary_key=True, index=True)
    loan_id = Column(Integer, ForeignKey("loans.id", ondelete="CASCADE"), nullable=False)
    repayment_number = Column(Integer, nullable=False)
    
    # Scheduled
    scheduled_amount = Column(Numeric(12, 2), nullable=False)
    principal_component = Column(Numeric(12, 2))
    interest_component = Column(Numeric(12, 2))
    due_date = Column(Date, nullable=False)
    
    # Actual
    paid_amount = Column(Numeric(12, 2), default=0)
    paid_date = Column(DateTime)
    payment_id = Column(Integer, ForeignKey("payments.id"))
    
    # Penalties
    late_fee = Column(Numeric(10, 2), default=0)
    days_overdue = Column(Integer, default=0)
    
    status = Column(String(20), default="scheduled")
    
    reminder_sent = Column(Boolean, default=False)
    reminder_sent_at = Column(DateTime)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    loan = relationship("Loan", back_populates="repayments")
    payment = relationship("Payment")


# ============== ANALYTICS & REPORTING ==============

class PaymentAnalytics(Base):
    """Aggregated payment analytics for reporting"""
    __tablename__ = "payment_analytics"

    id = Column(Integer, primary_key=True, index=True)
    school_id = Column(Integer, ForeignKey("schools.id"))
    
    # Time period
    period_type = Column(String(20), nullable=False)  # daily, weekly, monthly, yearly
    period_start = Column(Date, nullable=False)
    period_end = Column(Date, nullable=False)
    
    # Payment Metrics
    total_invoiced = Column(Numeric(14, 2), default=0)
    total_collected = Column(Numeric(14, 2), default=0)
    total_outstanding = Column(Numeric(14, 2), default=0)
    collection_rate = Column(Numeric(5, 2), default=0)  # Percentage
    
    # Transaction Counts
    total_transactions = Column(Integer, default=0)
    successful_transactions = Column(Integer, default=0)
    failed_transactions = Column(Integer, default=0)
    
    # Student Metrics
    total_students = Column(Integer, default=0)
    paying_students = Column(Integer, default=0)
    defaulting_students = Column(Integer, default=0)
    
    # Payment Patterns
    on_time_payments = Column(Integer, default=0)
    late_payments = Column(Integer, default=0)
    average_days_to_payment = Column(Float, default=0)
    
    # Installment Metrics
    active_installment_plans = Column(Integer, default=0)
    installment_collection_rate = Column(Numeric(5, 2), default=0)
    
    # Loan Metrics
    active_loans = Column(Integer, default=0)
    loan_disbursement_amount = Column(Numeric(14, 2), default=0)
    loan_repayment_rate = Column(Numeric(5, 2), default=0)
    loan_default_rate = Column(Numeric(5, 2), default=0)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    school = relationship("School")


class CollectionSchedule(Base):
    """Automated collection schedules"""
    __tablename__ = "collection_schedules"

    id = Column(Integer, primary_key=True, index=True)
    school_id = Column(Integer, ForeignKey("schools.id"))
    
    name = Column(String(100), nullable=False)
    description = Column(Text)
    
    # Schedule Configuration
    schedule_type = Column(String(20), nullable=False)  # one_time, recurring
    frequency = Column(String(20))  # daily, weekly, monthly
    day_of_week = Column(Integer)  # 0-6 for weekly
    day_of_month = Column(Integer)  # 1-31 for monthly
    time_of_day = Column(String(10))  # HH:MM format
    
    # Target Configuration
    target_type = Column(String(30), nullable=False)  # all_pending, overdue, installments
    min_amount = Column(Numeric(12, 2))
    max_amount = Column(Numeric(12, 2))
    
    # Status
    is_active = Column(Boolean, default=True)
    last_run = Column(DateTime)
    next_run = Column(DateTime)
    total_runs = Column(Integer, default=0)
    successful_collections = Column(Integer, default=0)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    school = relationship("School")


class AuditLog(Base):
    """Security audit logging"""
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    
    # Action Details
    action = Column(String(50), nullable=False)
    resource_type = Column(String(50), nullable=False)
    resource_id = Column(Integer)
    
    # Actor
    actor_type = Column(String(20))  # user, system, api
    actor_id = Column(String(100))
    ip_address = Column(String(50))
    user_agent = Column(String(500))
    
    # Request Details
    request_method = Column(String(10))
    request_path = Column(String(500))
    request_body = Column(JSON)
    
    # Response
    response_status = Column(Integer)
    response_body = Column(JSON)
    
    # Metadata
    details = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = {'sqlite_autoincrement': True}
