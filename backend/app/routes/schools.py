from typing import Optional, List
from datetime import date, datetime
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError

from ..models.database import get_db
from ..models.payment import School
from .schemas import SchoolCreate, SchoolResponse

router = APIRouter(prefix="/schools", tags=["schools"])


@router.post("/", response_model=SchoolResponse)
async def create_school(school: SchoolCreate, db: AsyncSession = Depends(get_db)):
    try:
        db_school = School(**school.model_dump())
        db.add(db_school)
        await db.commit()
        await db.refresh(db_school)
        return db_school
    except SQLAlchemyError as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/", response_model=List[SchoolResponse])
async def list_schools(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(School).offset(skip).limit(limit))
    schools = result.scalars().all()
    return schools


@router.get("/{school_id}", response_model=SchoolResponse)
async def get_school(school_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(School).where(School.id == school_id))
    school = result.scalar_one_or_none()
    if not school:
        raise HTTPException(status_code=404, detail="School not found")
    return school


@router.put("/{school_id}", response_model=SchoolResponse)
async def update_school(
    school_id: int,
    school_data: SchoolCreate,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(School).where(School.id == school_id))
    school = result.scalar_one_or_none()
    if not school:
        raise HTTPException(status_code=404, detail="School not found")

    for key, value in school_data.model_dump().items():
        setattr(school, key, value)

    await db.commit()
    await db.refresh(school)
    return school


@router.delete("/{school_id}")
async def delete_school(school_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(School).where(School.id == school_id))
    school = result.scalar_one_or_none()
    if not school:
        raise HTTPException(status_code=404, detail="School not found")

    await db.delete(school)
    await db.commit()
    return {"message": "School deleted successfully"}
