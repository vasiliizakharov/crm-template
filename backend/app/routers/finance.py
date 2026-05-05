from datetime import datetime, date
from decimal import Decimal
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db
from ..deps import require_roles, get_current_user

router = APIRouter()


@router.get("/", response_model=List[schemas.TransactionOut])
def list_tx(type: Optional[str] = None, order_id: Optional[int] = None,
            limit: int = 200, offset: int = 0,
            db: Session = Depends(get_db), _=Depends(get_current_user)):
    stmt = select(models.Transaction).order_by(models.Transaction.id.desc()).limit(limit).offset(offset)
    if type:
        stmt = stmt.where(models.Transaction.type == type)
    if order_id:
        stmt = stmt.where(models.Transaction.order_id == order_id)
    return db.scalars(stmt).all()


@router.post("/", response_model=schemas.TransactionOut, status_code=201)
def create_tx(payload: schemas.TransactionIn, db: Session = Depends(get_db),
              user: models.User = Depends(require_roles("admin", "manager", "accountant"))):
    if payload.order_id and not db.get(models.Order, payload.order_id):
        raise HTTPException(400, "Заказ не найден")
    tx = models.Transaction(user_id=user.id, **payload.model_dump())
    db.add(tx); db.flush()

    # обновить paid_amount/payment_status для заказа
    if payload.order_id and payload.type == "income":
        order = db.get(models.Order, payload.order_id)
        order.paid_amount = (order.paid_amount or Decimal('0')) + payload.amount
        if order.paid_amount >= order.total_amount and order.total_amount > 0:
            order.payment_status = "paid"
        elif order.paid_amount > 0:
            order.payment_status = "partial"
        db.add(models.OrderHistory(order_id=order.id, user_id=user.id, action="payment",
                                    after_state={"paid_amount": str(order.paid_amount),
                                                 "payment_status": order.payment_status}))
    db.commit(); db.refresh(tx)
    return tx


@router.delete("/{tx_id}", status_code=204)
def delete_tx(tx_id: int, db: Session = Depends(get_db),
              _=Depends(require_roles("admin"))):
    tx = db.get(models.Transaction, tx_id)
    if tx:
        db.delete(tx); db.commit()


@router.get("/balance")
def balance(period_start: Optional[date] = Query(None),
            period_end: Optional[date] = Query(None),
            db: Session = Depends(get_db), _=Depends(get_current_user)):
    base = select(func.coalesce(func.sum(models.Transaction.amount), 0))
    if period_start:
        base = base.where(models.Transaction.created_at >= period_start)
    if period_end:
        base = base.where(models.Transaction.created_at < period_end)
    income = db.scalar(base.where(models.Transaction.type == "income")) or Decimal('0')
    expense = db.scalar(base.where(models.Transaction.type == "expense")) or Decimal('0')
    return {
        "income": income,
        "expense": expense,
        "profit": income - expense,
    }
