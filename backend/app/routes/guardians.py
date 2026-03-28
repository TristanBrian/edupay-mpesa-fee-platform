from typing import Optional, List
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError

from ..models.database import get_db
from ..models.payment import Guardian
from .schemas import GuardianCreate, GuardianResponse

router = APIRouter(prefix="/guardians", tags=["guardians"])


@router.post("/", response_model=GuardianResponse)
async def create_guardian(guardian: GuardianCreate, db: AsyncSession = Depends(get_db)):
    try:
        db_guardian = Guardian(**guardian.model_dump())
        db.add(db_guardian)
        await db.commit()
        await db.refresh(db_guardian)
        return db_guardian
    except SQLAlchemyError as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/", response_model=List[GuardianResponse])
async def list_guardians(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    school_id: Optional[int] = None,
    phone: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    query = select(Guardian)
    if school_id:
        query = query.where(Guardian.school_id == school_id)
    if phone:
        query = query.where(Guardian.phone.like(f"%{phone}%"))
    query = query.offset(skip).limit(limit)

    result = await db.execute(query)
    guardians = result.scalars().all()
    return guardians


@router.get("/{guardian_id}", response_model=GuardianResponse)
async def get_guardian(guardian_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Guardian).where(Guardian.id == guardian_id))
    guardian = result.scalar_one_or_none()
    if not guardian:
        raise HTTPException(status_code=404, detail="Guardian not found")
    return guardian


@router.put("/{guardian_id}", response_model=GuardianResponse)
async def update_guardian(
    guardian_id: int,
    guardian_data: GuardianCreate,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Guardian).where(Guardian.id == guardian_id))
    guardian = result.scalar_one_or_none()
    if not guardian:
        raise HTTPException(status_code=404, detail="Guardian not found")

    for key, value in guardian_data.model_dump().items():
        setattr(guardian, key, value)

    await db.commit()
    await db.refresh(guardian)
    return guardian


@router.delete("/{guardian_id}")
async def delete_guardian(guardian_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Guardian).where(Guardian.id == guardian_id))
    guardian = result.scalar_one_or_none()
    if not guardian:
        raise HTTPException(status_code=404, detail="Guardian not found")

    await db.delete(guardian)
    await db.commit()
    return {"message": "Guardian deleted successfully"}
