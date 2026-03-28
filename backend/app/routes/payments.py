from datetime import datetime
from typing import Optional, List
import secrets

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError

from ..models.database import get_db
from ..models.payment import Payment, PaymentStatus
from ..services.mpesa import mpesa_service
from ..config import get_settings
from .schemas import (
    PaymentInitiateRequest,
    PaymentInitiateResponse,
    PaymentStatusResponse,
    PaymentRecord,
)

router = APIRouter(prefix="/payments", tags=["payments"])
settings = get_settings()


def generate_mock_response():
    return {
        "response_code": "0",
        "response_desc": "Success. Request accepted for processing",
        "merchant_id": f"MERCHANT_{secrets.token_hex(8).upper()}",
        "checkout_id": f"ws_CO_{datetime.now().strftime('%Y%m%d%H%M%S')}{secrets.token_hex(4).upper()}",
        "customer_message": "Success. Request accepted for processing",
    }


@router.post("/initiate", response_model=PaymentInitiateResponse)
async def initiate_payment(
    request: PaymentInitiateRequest,
    db: AsyncSession = Depends(get_db),
):
    try:
        phone = request.phone
        if not phone.startswith("254"):
            phone = f"254{phone.lstrip('+0')}"

        payment = Payment(
            transaction_id=secrets.token_hex(10).upper(),
            amount=request.amount,
            phone=phone,
            account_reference=request.account_reference,
            transaction_description=request.transaction_desc,
            status=PaymentStatus.PENDING,
        )

        db.add(payment)
        await db.commit()
        await db.refresh(payment)

        if settings.mock_mpesa:
            result = generate_mock_response()
        else:
            result = await mpesa_service.stk_push(
                amount=request.amount,
                phone=phone,
                account_reference=request.account_reference,
                transaction_desc=request.transaction_desc or "School Fee Payment",
            )

        payment.checkout_request_id = result.get("checkout_id")
        payment.merchant_request_id = result.get("merchant_id")
        await db.commit()

        if result.get("response_code") == "0":
            return PaymentInitiateResponse(
                success=True,
                message=result.get("customer_message", "Payment initiated successfully"),
                transaction_id=payment.transaction_id,
                checkout_id=result.get("checkout_id"),
            )
        else:
            payment.status = PaymentStatus.FAILED
            payment.result_code = result.get("response_code")
            payment.result_desc = result.get("response_desc")
            await db.commit()

            return PaymentInitiateResponse(
                success=False,
                message=result.get("response_desc", "Payment initiation failed"),
                transaction_id=payment.transaction_id,
            )

    except SQLAlchemyError as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Payment error: {str(e)}")


@router.post("/callback")
async def mpesa_callback(callback_data: dict, db: AsyncSession = Depends(get_db)):
    try:
        body = callback_data.get("Body", {})
        stk_callback = body.get("stkCallback", {})

        checkout_request_id = stk_callback.get("CheckoutRequestID")
        result_code = stk_callback.get("ResultCode")
        result_desc = stk_callback.get("ResultDesc")
        callback_items = stk_callback.get("CallbackMetadata", {}).get("Item", [])

        payment = await db.execute(
            select(Payment).where(Payment.checkout_request_id == checkout_request_id)
        )
        payment = payment.scalar_one_or_none()

        if not payment:
            return {"ResultCode": 1, "ResultDesc": "Payment not found"}

        payment.result_code = str(result_code)
        payment.result_desc = result_desc

        if result_code == 0:
            payment.status = PaymentStatus.COMPLETED
            payment.completed_at = datetime.utcnow()

            for item in callback_items:
                if item.get("Name") == "Amount":
                    pass
                elif item.get("Name") == "MpesaReceiptNumber":
                    payment.mpesa_receipt_number = item.get("Value")
        else:
            payment.status = PaymentStatus.FAILED

        payment.updated_at = datetime.utcnow()
        await db.commit()

        return {"ResultCode": 0, "ResultDesc": "Callback processed successfully"}

    except SQLAlchemyError as e:
        await db.rollback()
        return {"ResultCode": 1, "ResultDesc": f"Database error: {str(e)}"}
    except Exception as e:
        return {"ResultCode": 1, "ResultDesc": f"Callback error: {str(e)}"}


@router.get("/status/{transaction_id}", response_model=PaymentStatusResponse)
async def get_payment_status(
    transaction_id: str,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Payment).where(Payment.transaction_id == transaction_id)
    )
    payment = result.scalar_one_or_none()

    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")

    if payment.status == PaymentStatus.PENDING and payment.checkout_request_id and not settings.mock_mpesa:
        try:
            stk_status = await mpesa_service.stk_status(payment.checkout_request_id)

            result_code = stk_status.get("ResultCode")
            result_desc = stk_status.get("ResultDesc", "")

            if result_code == 0:
                payment.status = PaymentStatus.COMPLETED
                payment.completed_at = datetime.utcnow()
            elif "failed" in result_desc.lower() or result_code != 0:
                payment.status = PaymentStatus.FAILED

            payment.result_code = str(result_code)
            payment.result_desc = result_desc
            await db.commit()

        except Exception:
            pass

    return PaymentStatusResponse(
        success=payment.status == PaymentStatus.COMPLETED,
        message=payment.result_desc or "Payment processed",
        status=payment.status.value,
        transaction_id=payment.transaction_id,
        checkout_id=payment.checkout_request_id or "",
        mpesa_receipt=payment.mpesa_receipt_number,
        result_code=payment.result_code,
        result_desc=payment.result_desc,
    )


@router.get("/", response_model=List[PaymentRecord])
async def list_payments(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    status: Optional[PaymentStatus] = None,
    phone: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    query = select(Payment)

    if status:
        query = query.where(Payment.status == status)
    if phone:
        query = query.where(Payment.phone.like(f"%{phone}%"))

    query = query.order_by(Payment.created_at.desc()).offset(skip).limit(limit)

    result = await db.execute(query)
    payments = result.scalars().all()

    return payments


@router.get("/{payment_id}", response_model=PaymentRecord)
async def get_payment(payment_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Payment).where(Payment.id == payment_id))
    payment = result.scalar_one_or_none()

    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")

    return payment
