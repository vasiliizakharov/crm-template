from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, or_
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db
from ..deps import require_roles, get_current_user

router = APIRouter()


@router.get("/", response_model=List[schemas.CustomerOut])
def list_customers(q: Optional[str] = Query(None, description="поиск по имени/телефону/email"),
                   limit: int = 200, offset: int = 0,
                   db: Session = Depends(get_db), _=Depends(get_current_user)):
    stmt = select(models.Customer).order_by(models.Customer.id.desc()).limit(limit).offset(offset)
    if q:
        like = f"%{q}%"
        stmt = stmt.where(or_(
            models.Customer.full_name.ilike(like),
            models.Customer.phone.ilike(like),
            models.Customer.email.ilike(like),
        ))
    return db.scalars(stmt).all()


@router.get("/{cust_id}", response_model=schemas.CustomerOut)
def get_customer(cust_id: int, db: Session = Depends(get_db), _=Depends(get_current_user)):
    c = db.get(models.Customer, cust_id)
    if not c:
        raise HTTPException(404, "Не найден")
    return c


@router.post("/", response_model=schemas.CustomerOut, status_code=201)
def create_customer(payload: schemas.CustomerCreate, db: Session = Depends(get_db),
                    _=Depends(require_roles("admin", "manager"))):
    c = models.Customer(**payload.model_dump())
    db.add(c); db.commit(); db.refresh(c)
    return c


@router.put("/{cust_id}", response_model=schemas.CustomerOut)
def update_customer(cust_id: int, payload: schemas.CustomerUpdate, db: Session = Depends(get_db),
                    _=Depends(require_roles("admin", "manager"))):
    c = db.get(models.Customer, cust_id)
    if not c:
        raise HTTPException(404, "Не найден")
    for k, v in payload.model_dump().items():
        setattr(c, k, v)
    db.commit(); db.refresh(c)
    return c


@router.delete("/{cust_id}", status_code=204)
def delete_customer(cust_id: int, db: Session = Depends(get_db),
                    _=Depends(require_roles("admin"))):
    c = db.get(models.Customer, cust_id)
    if c:
        db.delete(c); db.commit()
