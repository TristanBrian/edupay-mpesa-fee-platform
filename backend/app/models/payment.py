from sqlalchemy import Column, String, Integer, DateTime, Date, Enum as SQLEnum, ForeignKey, Numeric, Text, JSON
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
