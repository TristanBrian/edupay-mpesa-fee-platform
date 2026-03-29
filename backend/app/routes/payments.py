"""
Payment Routes - M-Pesa STK Push Integration
Handles payment initiation, callbacks, and status queries
"""
from datetime import datetime
from typing import Optional, List
import secrets
import logging

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from sqlalchemy.exc import SQLAlchemyError

from ..models.database import get_db
from ..models.payment import Payment, PaymentStatus, Invoice
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
logger = logging.getLogger(__name__)


def generate_mock_response():
    """Generate mock M-Pesa response for testing without API"""
    return {
        "response_code": "0",
        "response_desc": "Success. Request accepted for processing",
        "merchant_id": f"MOCK-{secrets.token_hex(8).upper()}",
        "checkout_id": f"ws_CO_{datetime.now().strftime('%Y%m%d%H%M%S')}{secrets.token_hex(4).upper()}",
        "customer_message": "Success. Request accepted for processing. Check your phone.",
        "transaction_id": f"TXN{secrets.token_hex(8).upper()}",
    }


@router.post("/initiate", response_model=PaymentInitiateResponse)
async def initiate_payment(
    request: PaymentInitiateRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Initiate M-Pesa STK Push payment
    
    Sends an STK Push to the provided phone number.
    Customer will see a prompt on their phone to enter M-Pesa PIN.
    """
    try:
        # Format phone number
        phone = request.phone
        if not phone.startswith("254"):
            phone = f"254{phone.lstrip('+0')}"
        
        logger.info(f"Initiating payment: {phone}, KES {request.amount}, Ref: {request.account_reference}")

        # Create payment record
        payment = Payment(
            transaction_id=f"TXN{secrets.token_hex(8).upper()}",
            amount=request.amount,
            phone=phone,
            account_reference=request.account_reference,
            transaction_description=request.transaction_desc or "School Fee Payment",
            status=PaymentStatus.PENDING,
            invoice_id=request.invoice_id,
            student_id=request.student_id,
        )

        db.add(payment)
        await db.commit()
        await db.refresh(payment)

        # Use mock or real M-Pesa
        if settings.mock_mpesa:
            logger.info("Using MOCK M-Pesa mode")
            result = generate_mock_response()
        else:
            logger.info("Using LIVE M-Pesa API")
            result = await mpesa_service.stk_push(
                amount=request.amount,
                phone=phone,
                account_reference=request.account_reference,
                transaction_desc=request.transaction_desc or "School Fee Payment",
            )

        # Update payment with M-Pesa references
        payment.checkout_request_id = result.get("checkout_id")
        payment.merchant_request_id = result.get("merchant_id")
        await db.commit()

        if result.get("response_code") == "0":
            logger.info(f"STK Push successful: checkout_id={result.get('checkout_id')}")
            return PaymentInitiateResponse(
                success=True,
                message=result.get("customer_message", "Payment request sent. Check your phone."),
                transaction_id=payment.transaction_id,
                checkout_id=result.get("checkout_id"),
            )
        else:
            # Update payment status to failed
            payment.status = PaymentStatus.FAILED
            payment.result_code = result.get("response_code")
            payment.result_desc = result.get("response_desc")
            await db.commit()
            
            logger.warning(f"STK Push failed: {result.get('response_desc')}")
            return PaymentInitiateResponse(
                success=False,
                message=result.get("response_desc", "Payment initiation failed"),
                transaction_id=payment.transaction_id,
            )

    except SQLAlchemyError as e:
        await db.rollback()
        logger.error(f"Database error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    except ValueError as e:
        logger.error(f"Validation error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        await db.rollback()
        logger.error(f"Payment error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Payment error: {str(e)}")


@router.post("/callback")
async def mpesa_callback(
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """
    M-Pesa callback endpoint
    
    This endpoint receives payment confirmations from Safaricom.
    Must be publicly accessible (use ngrok for localhost testing).
    """
    try:
        # Get raw callback data
        callback_data = await request.json()
        logger.info(f"Received M-Pesa callback: {callback_data}")
        
        # Parse callback using service
        parsed = mpesa_service.parse_callback(callback_data)
        checkout_request_id = parsed.get("checkout_request_id")
        
        if not checkout_request_id:
            logger.error("Callback missing CheckoutRequestID")
            return JSONResponse(
                content={"ResultCode": 1, "ResultDesc": "Missing CheckoutRequestID"},
                status_code=200
            )
        
        # Find payment by checkout_request_id
        result = await db.execute(
            select(Payment).where(Payment.checkout_request_id == checkout_request_id)
        )
        payment = result.scalar_one_or_none()
        
        if not payment:
            logger.error(f"Payment not found for checkout_id: {checkout_request_id}")
            return JSONResponse(
                content={"ResultCode": 1, "ResultDesc": "Payment not found"},
                status_code=200
            )
        
        # Update payment based on callback
        payment.result_code = str(parsed.get("result_code"))
        payment.result_desc = parsed.get("result_desc")
        
        if parsed.get("success"):
            payment.status = PaymentStatus.COMPLETED
            payment.completed_at = datetime.utcnow()
            payment.mpesa_receipt_number = parsed.get("mpesa_receipt")
            
            # Update related invoice if exists
            if payment.invoice_id:
                await _update_invoice_payment(db, payment.invoice_id, payment.amount)
            
            logger.info(f"Payment completed: {payment.mpesa_receipt_number}")
        else:
            payment.status = PaymentStatus.FAILED
            logger.warning(f"Payment failed: {parsed.get('result_desc')}")
        
        payment.updated_at = datetime.utcnow()
        await db.commit()
        
        # Return success to Safaricom
        return JSONResponse(
            content={"ResultCode": 0, "ResultDesc": "Callback received successfully"},
            status_code=200
        )

    except SQLAlchemyError as e:
        await db.rollback()
        logger.error(f"Database error in callback: {str(e)}")
        return JSONResponse(
            content={"ResultCode": 1, "ResultDesc": f"Database error: {str(e)}"},
            status_code=200
        )
    except Exception as e:
        logger.error(f"Callback processing error: {str(e)}")
        return JSONResponse(
            content={"ResultCode": 1, "ResultDesc": f"Processing error: {str(e)}"},
            status_code=200
        )


async def _update_invoice_payment(db: AsyncSession, invoice_id: int, amount: float):
    """Update invoice paid amount after successful payment"""
    try:
        result = await db.execute(
            select(Invoice).where(Invoice.id == invoice_id)
        )
        invoice = result.scalar_one_or_none()
        
        if invoice:
            invoice.paid_amount = (invoice.paid_amount or 0) + amount
            invoice.balance = invoice.total_amount - invoice.paid_amount
            
            if invoice.balance <= 0:
                invoice.status = "paid"
            elif invoice.paid_amount > 0:
                invoice.status = "partial"
            
            invoice.updated_at = datetime.utcnow()
            logger.info(f"Invoice {invoice_id} updated: paid={invoice.paid_amount}, balance={invoice.balance}")
    except Exception as e:
        logger.error(f"Error updating invoice: {str(e)}")


@router.get("/status/{transaction_id}", response_model=PaymentStatusResponse)
async def get_payment_status(
    transaction_id: str,
    db: AsyncSession = Depends(get_db),
):
    """
    Get payment status by transaction ID
    
    If payment is still pending, queries M-Pesa API for latest status.
    """
    result = await db.execute(
        select(Payment).where(Payment.transaction_id == transaction_id)
    )
    payment = result.scalar_one_or_none()

    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")

    # If pending and has checkout_id, query M-Pesa for status
    if payment.status == PaymentStatus.PENDING and payment.checkout_request_id:
        if not settings.mock_mpesa:
            try:
                logger.info(f"Querying M-Pesa status for: {payment.checkout_request_id}")
                stk_status = await mpesa_service.stk_query(payment.checkout_request_id)
                
                result_code = stk_status.get("ResultCode")
                result_desc = stk_status.get("ResultDesc", "")
                
                payment.result_code = str(result_code) if result_code is not None else None
                payment.result_desc = result_desc
                
                if result_code == 0:
                    payment.status = PaymentStatus.COMPLETED
                    payment.completed_at = datetime.utcnow()
                    logger.info(f"Payment confirmed via query: {transaction_id}")
                elif result_code is not None and result_code != 0:
                    # Only mark as failed if we get a definitive failure code
                    # Code 1032 = cancelled by user
                    # Code 1 = insufficient balance
                    if result_code in [1, 1032, 1037]:
                        payment.status = PaymentStatus.FAILED
                        logger.info(f"Payment failed via query: {result_desc}")
                
                await db.commit()
                
            except Exception as e:
                logger.warning(f"Could not query M-Pesa status: {str(e)}")
        else:
            # Mock mode - simulate completion after some time
            logger.debug("Mock mode: status query skipped")

    return PaymentStatusResponse(
        success=payment.status == PaymentStatus.COMPLETED,
        message=payment.result_desc or _get_status_message(payment.status),
        status=payment.status.value,
        transaction_id=payment.transaction_id,
        checkout_id=payment.checkout_request_id or "",
        mpesa_receipt=payment.mpesa_receipt_number,
        result_code=payment.result_code,
        result_desc=payment.result_desc,
    )


def _get_status_message(status: PaymentStatus) -> str:
    """Get user-friendly status message"""
    messages = {
        PaymentStatus.PENDING: "Waiting for payment confirmation. Check your phone.",
        PaymentStatus.COMPLETED: "Payment received successfully.",
        PaymentStatus.FAILED: "Payment failed. Please try again.",
        PaymentStatus.CANCELLED: "Payment was cancelled.",
    }
    return messages.get(status, "Unknown status")


@router.post("/simulate-callback/{checkout_id}")
async def simulate_callback(
    checkout_id: str,
    success: bool = True,
    db: AsyncSession = Depends(get_db),
):
    """
    Simulate M-Pesa callback for testing (only works in mock mode)
    
    Use this endpoint to test callback handling without real M-Pesa.
    """
    if not settings.mock_mpesa:
        raise HTTPException(status_code=403, detail="Simulation only available in mock mode")
    
    # Find payment
    result = await db.execute(
        select(Payment).where(Payment.checkout_request_id == checkout_id)
    )
    payment = result.scalar_one_or_none()
    
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")
    
    # Simulate callback
    if success:
        payment.status = PaymentStatus.COMPLETED
        payment.completed_at = datetime.utcnow()
        payment.mpesa_receipt_number = f"SIM{secrets.token_hex(5).upper()}"
        payment.result_code = "0"
        payment.result_desc = "The service request is processed successfully."
        
        if payment.invoice_id:
            await _update_invoice_payment(db, payment.invoice_id, float(payment.amount))
    else:
        payment.status = PaymentStatus.FAILED
        payment.result_code = "1032"
        payment.result_desc = "Request cancelled by user"
    
    payment.updated_at = datetime.utcnow()
    await db.commit()
    
    return {
        "message": f"Callback simulated: {'success' if success else 'failed'}",
        "transaction_id": payment.transaction_id,
        "status": payment.status.value,
        "mpesa_receipt": payment.mpesa_receipt_number,
    }


@router.get("/", response_model=List[PaymentRecord])
async def list_payments(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    status: Optional[PaymentStatus] = None,
    phone: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    """List all payments with optional filters"""
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
    """Get payment by ID"""
    result = await db.execute(select(Payment).where(Payment.id == payment_id))
    payment = result.scalar_one_or_none()

    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")

    return payment
