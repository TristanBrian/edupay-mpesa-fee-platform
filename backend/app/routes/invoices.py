from typing import Optional, List
from datetime import datetime
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError

from ..models.database import get_db
from ..models.payment import Invoice, InvoiceItem
from .schemas import InvoiceCreate, InvoiceResponse, InvoiceItemCreate

router = APIRouter(prefix="/invoices", tags=["invoices"])


@router.post("/", response_model=InvoiceResponse)
async def create_invoice(invoice: InvoiceCreate, db: AsyncSession = Depends(get_db)):
    try:
        invoice_data = invoice.model_dump()
        items_data = invoice_data.pop("items", [])

        db_invoice = Invoice(**invoice_data)
        db.add(db_invoice)
        await db.flush()

        for item_data in items_data:
            item = InvoiceItem(invoice_id=db_invoice.id, **item_data)
            db.add(item)

        await db.commit()
        await db.refresh(db_invoice)
        return db_invoice
    except SQLAlchemyError as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/", response_model=List[InvoiceResponse])
async def list_invoices(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    student_id: Optional[int] = None,
    guardian_id: Optional[int] = None,
    school_id: Optional[int] = None,
    status: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    query = select(Invoice)
    if student_id:
        query = query.where(Invoice.student_id == student_id)
    if guardian_id:
        query = query.where(Invoice.guardian_id == guardian_id)
    if school_id:
        query = query.where(Invoice.school_id == school_id)
    if status:
        query = query.where(Invoice.status == status)
    query = query.offset(skip).limit(limit)

    result = await db.execute(query)
    invoices = result.scalars().all()
    return invoices


@router.get("/{invoice_id}", response_model=InvoiceResponse)
async def get_invoice(invoice_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Invoice).where(Invoice.id == invoice_id))
    invoice = result.scalar_one_or_none()
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    return invoice


@router.put("/{invoice_id}", response_model=InvoiceResponse)
async def update_invoice(
    invoice_id: int,
    invoice_data: InvoiceCreate,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Invoice).where(Invoice.id == invoice_id))
    invoice = result.scalar_one_or_none()
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")

    invoice_data_dict = invoice_data.model_dump()
    invoice_data_dict.pop("items", None)

    for key, value in invoice_data_dict.items():
        setattr(invoice, key, value)

    await db.commit()
    await db.refresh(invoice)
    return invoice


@router.delete("/{invoice_id}")
async def delete_invoice(invoice_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Invoice).where(Invoice.id == invoice_id))
    invoice = result.scalar_one_or_none()
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")

    await db.delete(invoice)
    await db.commit()
    return {"message": "Invoice deleted successfully"}


@router.post("/{invoice_id}/items")
async def add_invoice_item(
    invoice_id: int,
    item: InvoiceItemCreate,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Invoice).where(Invoice.id == invoice_id))
    invoice = result.scalar_one_or_none()
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")

    db_item = InvoiceItem(invoice_id=invoice_id, **item.model_dump())
    db.add(db_item)
    await db.commit()
    await db.refresh(db_item)
    return db_item


@router.get("/{invoice_id}/items")
async def get_invoice_items(invoice_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(InvoiceItem).where(InvoiceItem.invoice_id == invoice_id))
    items = result.scalars().all()
    return items
