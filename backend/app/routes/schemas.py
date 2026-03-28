import re
from datetime import datetime, date
from typing import Optional, List
from decimal import Decimal, InvalidOperation
from pydantic import BaseModel, Field, field_validator, model_validator, ConfigDict
import logging

logger = logging.getLogger(__name__)


def sanitize_string(value: str) -> str:
    if not value:
        return value
    return re.sub(r'[<>\'\"%;()&+]', '', value.strip())


def validate_phone(phone: str) -> str:
    cleaned = re.sub(r'[\s\-\(\)]', '', phone)
    if not re.match(r'^254\d{9}$', cleaned):
        if re.match(r'^0\d{9}$', cleaned):
            cleaned = '254' + cleaned[1:]
        else:
            raise ValueError('Invalid phone number format. Use 254... or 07... format.')
    return cleaned


def validate_email(email: str) -> str:
    if not email:
        return email
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(pattern, email):
        raise ValueError('Invalid email format')
    return email.lower()


class SchoolBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=255, description="School name")
    code: str = Field(..., min_length=2, max_length=50, description="School code")
    address: Optional[str] = Field(None, max_length=500, description="School address")
    phone: Optional[str] = Field(None, max_length=20, description="Contact phone")
    email: Optional[str] = Field(None, max_length=100, description="Contact email")
    mpesa_shortcode: Optional[str] = Field(None, max_length=20, description="M-Pesa shortcode")

    @field_validator('name', 'code')
    @classmethod
    def sanitize_name(cls, v: str) -> str:
        return sanitize_string(v)

    @field_validator('email')
    @classmethod
    def validate_email_format(cls, v: Optional[str]) -> Optional[str]:
        if v:
            return validate_email(v)
        return v

    model_config = ConfigDict(str_strip_whitespace=True)


class SchoolCreate(SchoolBase):
    @field_validator('code')
    @classmethod
    def uppercase_code(cls, v: str) -> str:
        return v.upper()


class SchoolResponse(SchoolBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class GuardianBase(BaseModel):
    first_name: str = Field(..., min_length=1, max_length=100, description="First name")
    last_name: str = Field(..., min_length=1, max_length=100, description="Last name")
    email: Optional[str] = Field(None, max_length=100, description="Email address")
    phone: str = Field(..., min_length=10, max_length=20, description="Phone number")
    id_number: Optional[str] = Field(None, max_length=50, description="ID number")
    relationship_type: Optional[str] = Field(None, max_length=50, description="Relationship to student")
    school_id: Optional[int] = Field(None, gt=0, description="School ID")
    address: Optional[str] = Field(None, max_length=500, description="Address")

    @field_validator('first_name', 'last_name')
    @classmethod
    def sanitize_name(cls, v: str) -> str:
        return sanitize_string(v)

    @field_validator('email')
    @classmethod
    def validate_email_format(cls, v: Optional[str]) -> Optional[str]:
        if v:
            return validate_email(v)
        return v

    @field_validator('phone')
    @classmethod
    def validate_phone_format(cls, v: str) -> str:
        return validate_phone(v)

    @field_validator('id_number')
    @classmethod
    def sanitize_id_number(cls, v: Optional[str]) -> Optional[str]:
        if v:
            return sanitize_string(v)
        return v

    model_config = ConfigDict(str_strip_whitespace=True)


class GuardianCreate(GuardianBase):
    pass


class GuardianResponse(GuardianBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class StudentBase(BaseModel):
    admission_number: str = Field(..., min_length=1, max_length=50, description="Admission number")
    first_name: str = Field(..., min_length=1, max_length=100, description="First name")
    last_name: str = Field(..., min_length=1, max_length=100, description="Last name")
    date_of_birth: Optional[date] = Field(None, description="Date of birth")
    gender: Optional[str] = Field(None, max_length=10, description="Gender")
    class_name: str = Field(..., min_length=1, max_length=50, description="Class/Grade")
    stream: Optional[str] = Field(None, max_length=20, description="Stream")
    guardian_id: Optional[int] = Field(None, gt=0, description="Guardian ID")
    school_id: Optional[int] = Field(None, gt=0, description="School ID")
    status: str = Field("active", max_length=20, description="Student status")

    @field_validator('first_name', 'last_name', 'admission_number', 'class_name')
    @classmethod
    def sanitize_fields(cls, v: str) -> str:
        return sanitize_string(v)

    @field_validator('status')
    @classmethod
    def validate_status(cls, v: str) -> str:
        allowed = ['active', 'inactive', 'suspended', 'graduated']
        if v.lower() not in allowed:
            raise ValueError(f'Status must be one of: {", ".join(allowed)}')
        return v.lower()

    @field_validator('date_of_birth')
    @classmethod
    def validate_dob(cls, v: Optional[date]) -> Optional[date]:
        if v and v > date.today():
            raise ValueError('Date of birth cannot be in the future')
        return v

    model_config = ConfigDict(str_strip_whitespace=True)


class StudentCreate(StudentBase):
    @field_validator('admission_number')
    @classmethod
    def uppercase_admission(cls, v: str) -> str:
        return v.upper()


class StudentResponse(StudentBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class InvoiceItemBase(BaseModel):
    description: str = Field(..., min_length=1, max_length=255, description="Item description")
    quantity: int = Field(1, ge=1, le=1000, description="Quantity")
    unit_price: Decimal = Field(..., ge=Decimal("0"), le=Decimal("999999999.99"), description="Unit price")
    total_price: Decimal = Field(..., ge=Decimal("0"), le=Decimal("999999999.99"), description="Total price")

    @field_validator('description')
    @classmethod
    def sanitize_description(cls, v: str) -> str:
        return sanitize_string(v)

    @model_validator(mode='after')
    def validate_prices(self):
        expected_total = self.unit_price * self.quantity
        if abs(self.total_price - expected_total) > Decimal("0.01"):
            raise ValueError(f'Total price ({self.total_price}) must equal quantity ({self.quantity}) x unit_price ({self.unit_price}) = {expected_total}')
        return self

    model_config = ConfigDict(str_strip_whitespace=True)


class InvoiceItemCreate(InvoiceItemBase):
    pass


class InvoiceItemResponse(InvoiceItemBase):
    id: int
    invoice_id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class InvoiceBase(BaseModel):
    invoice_number: str = Field(..., min_length=1, max_length=50, description="Invoice number")
    student_id: Optional[int] = Field(None, gt=0, description="Student ID")
    guardian_id: Optional[int] = Field(None, gt=0, description="Guardian ID")
    school_id: Optional[int] = Field(None, gt=0, description="School ID")
    term: Optional[str] = Field(None, max_length=20, description="Term")
    year: Optional[int] = Field(None, ge=2020, le=2100, description="Year")
    total_amount: Decimal = Field(..., ge=Decimal("0"), description="Total amount")
    paid_amount: Decimal = Field(Decimal("0"), ge=Decimal("0"), description="Paid amount")
    balance: Decimal = Field(..., ge=Decimal("0"), description="Balance")
    due_date: Optional[date] = Field(None, description="Due date")
    status: str = Field("pending", max_length=20, description="Invoice status")
    description: Optional[str] = Field(None, max_length=500, description="Description")

    @field_validator('invoice_number')
    @classmethod
    def sanitize_invoice_number(cls, v: str) -> str:
        return sanitize_string(v.upper())

    @field_validator('status')
    @classmethod
    def validate_status(cls, v: str) -> str:
        allowed = ['pending', 'partial', 'paid', 'overdue', 'cancelled']
        if v.lower() not in allowed:
            raise ValueError(f'Status must be one of: {", ".join(allowed)}')
        return v.lower()

    @model_validator(mode='after')
    def validate_amounts(self):
        if self.paid_amount > self.total_amount:
            raise ValueError('Paid amount cannot exceed total amount')
        expected_balance = self.total_amount - self.paid_amount
        if abs(self.balance - expected_balance) > Decimal("0.01"):
            raise ValueError(f'Balance ({self.balance}) must equal total_amount ({self.total_amount}) - paid_amount ({self.paid_amount}) = {expected_balance}')
        return self

    model_config = ConfigDict(str_strip_whitespace=True)


class InvoiceCreate(InvoiceBase):
    items: Optional[List[InvoiceItemCreate]] = Field(default_factory=list, max_length=50)


class InvoiceResponse(InvoiceBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PaymentInitiateRequest(BaseModel):
    amount: int = Field(..., gt=0, le=150000, description="Amount in KES (max 150,000)")
    phone: str = Field(..., description="M-Pesa phone number")
    account_reference: str = Field(..., min_length=1, max_length=100, description="Invoice/Student ID")
    transaction_desc: Optional[str] = Field("School Fee Payment", max_length=255)
    invoice_id: Optional[int] = Field(None, gt=0, description="Invoice ID")
    student_id: Optional[int] = Field(None, gt=0, description="Student ID")

    @field_validator('phone')
    @classmethod
    def validate_phone_format(cls, v: str) -> str:
        return validate_phone(v)

    @field_validator('account_reference')
    @classmethod
    def sanitize_reference(cls, v: str) -> str:
        return sanitize_string(v)

    @field_validator('transaction_desc')
    @classmethod
    def sanitize_description(cls, v: Optional[str]) -> str:
        if v:
            return sanitize_string(v)
        return "School Fee Payment"

    model_config = ConfigDict(str_strip_whitespace=True)


class PaymentInitiateResponse(BaseModel):
    success: bool
    message: str
    transaction_id: str
    checkout_id: Optional[str] = None


class PaymentStatusResponse(BaseModel):
    success: bool
    message: str
    status: str
    transaction_id: str
    checkout_id: str
    mpesa_receipt: Optional[str] = None
    result_code: Optional[str] = None
    result_desc: Optional[str] = None


class MpesaCallbackRequest(BaseModel):
    Body: dict


class PaymentRecord(BaseModel):
    id: int
    transaction_id: str
    checkout_request_id: Optional[str]
    merchant_request_id: Optional[str]
    amount: Decimal
    phone: str
    account_reference: Optional[str]
    status: str
    mpesa_receipt_number: Optional[str]
    created_at: datetime
    completed_at: Optional[datetime]

    model_config = ConfigDict(from_attributes=True)


class ErrorResponse(BaseModel):
    detail: str
    error_code: Optional[str] = None
    field: Optional[str] = None

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "detail": "Validation error",
                "error_code": "VALIDATION_ERROR",
                "field": "phone"
            }
        }
    )


class SuccessResponse(BaseModel):
    message: str
    data: Optional[dict] = None

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "message": "Operation successful",
                "data": {"id": 1}
            }
        }
    )
