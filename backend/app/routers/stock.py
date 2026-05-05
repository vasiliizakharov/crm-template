from typing import List
from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text, select
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db
from ..deps import require_roles, get_current_user

router = APIRouter()


@router.get("/", response_model=List[schemas.StockOut])
def list_stock(db: Session = Depends(get_db), _=Depends(get_current_user)):
    rows = db.execute(text("""
        SELECT product_id, sku, name, unit, cost, price, quantity, reserved, available
        FROM v_stock
        ORDER BY name
    """)).mappings().all()
    return [dict(r) for r in rows]


@router.post("/movement", response_model=schemas.StockMovementOut, status_code=201)
def create_movement(payload: schemas.StockMovementIn, db: Session = Depends(get_db),
                    user: models.User = Depends(require_roles("admin", "warehouse"))):
    p = db.get(models.Product, payload.product_id)
    if not p or not p.is_active:
        raise HTTPException(400, "Товар не найден или отключён")
    if p.kind != "part":
        raise HTTPException(400, "Складские движения только для запчастей (part)")

    stock = db.get(models.Stock, payload.product_id)
    if not stock:
        stock = models.Stock(product_id=p.id, quantity=Decimal('0'))
        db.add(stock); db.flush()

    qty = Decimal(payload.quantity)
    if payload.type == "in":
        stock.quantity = (stock.quantity or Decimal('0')) + qty
    elif payload.type in ("out", "writeoff"):
        if (stock.quantity or 0) < qty:
            raise HTTPException(400, f"Недостаточно остатков: {stock.quantity} < {qty}")
        stock.quantity -= qty
    elif payload.type == "adjust":
        # adjust = установить остаток в значение
        stock.quantity = qty
    else:
        raise HTTPException(400, "Неподдерживаемый тип движения")

    mv = models.StockMovement(
        product_id=p.id, user_id=user.id,
        type=payload.type, quantity=qty, cost=payload.cost or p.cost,
        note=payload.note,
    )
    db.add(mv); db.commit(); db.refresh(mv)
    return mv


@router.get("/movements", response_model=List[schemas.StockMovementOut])
def list_movements(limit: int = 200, db: Session = Depends(get_db),
                   _=Depends(require_roles("admin", "warehouse", "manager"))):
    return db.scalars(
        select(models.StockMovement).order_by(models.StockMovement.id.desc()).limit(limit)
    ).all()
