from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, or_
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db
from ..deps import require_roles, get_current_user

router = APIRouter()


@router.get("/", response_model=List[schemas.ProductOut])
def list_products(q: Optional[str] = Query(None),
                  kind: Optional[str] = Query(None),
                  db: Session = Depends(get_db), _=Depends(get_current_user)):
    stmt = select(models.Product).order_by(models.Product.id.desc())
    if q:
        like = f"%{q}%"
        stmt = stmt.where(or_(models.Product.name.ilike(like), models.Product.sku.ilike(like)))
    if kind:
        stmt = stmt.where(models.Product.kind == kind)
    return db.scalars(stmt).all()


@router.post("/", response_model=schemas.ProductOut, status_code=201)
def create_product(payload: schemas.ProductCreate, db: Session = Depends(get_db),
                   _=Depends(require_roles("admin", "warehouse"))):
    p = models.Product(**payload.model_dump())
    db.add(p); db.flush()
    if payload.kind == "part":
        db.add(models.Stock(product_id=p.id, quantity=0))
    db.commit(); db.refresh(p)
    return p


@router.put("/{product_id}", response_model=schemas.ProductOut)
def update_product(product_id: int, payload: schemas.ProductUpdate, db: Session = Depends(get_db),
                   _=Depends(require_roles("admin", "warehouse"))):
    p = db.get(models.Product, product_id)
    if not p:
        raise HTTPException(404, "Не найден")
    for k, v in payload.model_dump().items():
        setattr(p, k, v)
    db.commit(); db.refresh(p)
    return p


@router.delete("/{product_id}", status_code=204)
def delete_product(product_id: int, db: Session = Depends(get_db),
                   _=Depends(require_roles("admin"))):
    p = db.get(models.Product, product_id)
    if not p:
        return
    p.is_active = False
    db.commit()
