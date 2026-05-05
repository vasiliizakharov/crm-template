from datetime import datetime, timezone, timedelta, date
from decimal import Decimal
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func, text
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db
from ..deps import require_roles, get_current_user

router = APIRouter()


def _next_order_number(db: Session) -> str:
    prefix_row = db.execute(text("SELECT value FROM settings WHERE key='order_number_prefix'")).scalar()
    prefix = (prefix_row or "СЦ-").strip('"') if isinstance(prefix_row, str) else "СЦ-"
    seq = db.execute(text("SELECT COALESCE(MAX(id),0)+1 FROM orders")).scalar() or 1
    return f"{prefix}{seq:06d}"


def _calc_total(items: List[models.OrderItem], discount_amount: Decimal) -> Decimal:
    total = Decimal('0')
    for it in items:
        line = (it.unit_price or Decimal('0')) * (it.quantity or Decimal('0'))
        if it.discount_pct:
            line = line * (Decimal('100') - it.discount_pct) / Decimal('100')
        total += line
    return max(Decimal('0'), total - (discount_amount or Decimal('0')))


@router.get("/", response_model=List[schemas.OrderOut])
def list_orders(status: Optional[str] = None,
                customer_id: Optional[int] = None,
                master_id: Optional[int] = None,
                q: Optional[str] = None,
                limit: int = 100, offset: int = 0,
                db: Session = Depends(get_db), _=Depends(get_current_user)):
    stmt = select(models.Order).order_by(models.Order.id.desc()).limit(limit).offset(offset)
    if status:
        stmt = stmt.where(models.Order.status == status)
    if customer_id:
        stmt = stmt.where(models.Order.customer_id == customer_id)
    if master_id:
        stmt = stmt.where(models.Order.master_id == master_id)
    if q:
        like = f"%{q}%"
        stmt = stmt.where(models.Order.number.ilike(like))
    return db.scalars(stmt).all()


@router.get("/{order_id}", response_model=schemas.OrderOut)
def get_order(order_id: int, db: Session = Depends(get_db), _=Depends(get_current_user)):
    o = db.get(models.Order, order_id)
    if not o:
        raise HTTPException(404, "Не найден")
    return o


@router.post("/", response_model=schemas.OrderOut, status_code=201)
def create_order(payload: schemas.OrderCreate, db: Session = Depends(get_db),
                 user: models.User = Depends(require_roles("admin", "manager"))):
    if not db.get(models.Customer, payload.customer_id):
        raise HTTPException(400, "Клиент не найден")
    o = models.Order(
        number=_next_order_number(db),
        customer_id=payload.customer_id,
        device_id=payload.device_id,
        manager_id=payload.manager_id or user.id,
        master_id=payload.master_id,
        branch_id=payload.branch_id or user.branch_id,
        declared_problem=payload.declared_problem,
        accessories=payload.accessories,
        appearance=payload.appearance,
        estimated_cost=payload.estimated_cost or Decimal('0'),
        deadline_at=payload.deadline_at,
        created_by=user.id,
    )
    db.add(o); db.flush()

    for it in payload.items:
        oi = models.OrderItem(
            order_id=o.id, product_id=it.product_id, kind=it.kind, name=it.name,
            quantity=it.quantity, unit_cost=it.unit_cost, unit_price=it.unit_price,
            discount_pct=it.discount_pct, master_share_pct=it.master_share_pct,
        )
        db.add(oi)
        if it.kind == "part" and it.product_id:
            stock = db.get(models.Stock, it.product_id)
            if not stock:
                raise HTTPException(400, f"Товар {it.product_id} не найден на складе")
            if stock.quantity < it.quantity:
                raise HTTPException(400, f"Недостаточно остатков для {it.name}: {stock.quantity} < {it.quantity}")
            stock.quantity -= it.quantity
            db.add(models.StockMovement(
                product_id=it.product_id, user_id=user.id, order_id=o.id,
                type="out", quantity=it.quantity, cost=it.unit_cost,
                note=f"Заказ {o.number}",
            ))

    db.flush()
    o.total_amount = _calc_total(o.items, o.discount_amount)
    db.add(models.OrderHistory(order_id=o.id, user_id=user.id, action="create",
                                after_state={"status": o.status, "total": str(o.total_amount)}))
    db.commit(); db.refresh(o)
    return o


@router.put("/{order_id}", response_model=schemas.OrderOut)
def update_order(order_id: int, payload: schemas.OrderUpdate, db: Session = Depends(get_db),
                 user: models.User = Depends(require_roles("admin", "manager", "master"))):
    o = db.get(models.Order, order_id)
    if not o:
        raise HTTPException(404, "Не найден")
    before = {k: getattr(o, k) for k in ("diagnosis", "work_done", "estimated_cost", "discount_amount")}
    for fld in ("master_id", "manager_id", "declared_problem", "diagnosis", "work_done",
                "accessories", "appearance", "estimated_cost", "discount_amount",
                "deadline_at", "warranty_until"):
        v = getattr(payload, fld)
        if v is not None:
            setattr(o, fld, v)
    o.total_amount = _calc_total(o.items, o.discount_amount)
    db.add(models.OrderHistory(order_id=o.id, user_id=user.id, action="edit",
                                before_state={k: str(v) if v is not None else None for k, v in before.items()},
                                after_state={"total": str(o.total_amount)}))
    db.commit(); db.refresh(o)
    return o


ALLOWED_TRANSITIONS = {
    "new":        {"diagnosing", "in_repair", "cancelled"},
    "diagnosing": {"awaiting", "in_repair", "ready", "cancelled"},
    "awaiting":   {"in_repair", "diagnosing", "cancelled"},
    "in_repair":  {"ready", "awaiting", "cancelled"},
    "ready":      {"issued", "in_repair"},
    "issued":     {"warranty"},
    "warranty":   {"in_repair", "issued"},
    "cancelled":  set(),
}


@router.patch("/{order_id}/status", response_model=schemas.OrderOut)
def change_status(order_id: int, payload: schemas.OrderStatusIn, db: Session = Depends(get_db),
                  user: models.User = Depends(require_roles("admin", "manager", "master"))):
    o = db.get(models.Order, order_id)
    if not o:
        raise HTTPException(404, "Не найден")
    new = payload.status
    if new not in ALLOWED_TRANSITIONS.get(o.status, set()) and new != o.status:
        raise HTTPException(400, f"Недопустимый переход: {o.status} → {new}")
    before = {"status": o.status}
    o.status = new
    if new == "issued":
        o.issued_at = datetime.now(timezone.utc)
        # warranty по умолчанию +90 дней
        wd_row = db.execute(text("SELECT value FROM settings WHERE key='default_warranty_days'")).scalar()
        try:
            wd = int(wd_row) if wd_row else 90
        except (TypeError, ValueError):
            wd = 90
        if not o.warranty_until:
            o.warranty_until = (datetime.now(timezone.utc) + timedelta(days=wd)).date()
    db.add(models.OrderHistory(order_id=o.id, user_id=user.id, action="status_change",
                                before_state=before, after_state={"status": new}, note=payload.note))
    db.commit(); db.refresh(o)
    return o


@router.get("/{order_id}/history", response_model=List[schemas.OrderHistoryOut])
def order_history(order_id: int, db: Session = Depends(get_db), _=Depends(get_current_user)):
    return db.scalars(
        select(models.OrderHistory).where(models.OrderHistory.order_id == order_id)
        .order_by(models.OrderHistory.id.desc())
    ).all()


@router.post("/{order_id}/items", response_model=schemas.OrderItemOut, status_code=201)
def add_item(order_id: int, payload: schemas.OrderItemIn, db: Session = Depends(get_db),
             user: models.User = Depends(require_roles("admin", "manager", "master"))):
    o = db.get(models.Order, order_id)
    if not o:
        raise HTTPException(404, "Не найден")
    if o.status in ("issued", "cancelled"):
        raise HTTPException(400, "Нельзя менять состав закрытого заказа")
    oi = models.OrderItem(order_id=o.id, **payload.model_dump())
    db.add(oi); db.flush()
    if payload.kind == "part" and payload.product_id:
        stock = db.get(models.Stock, payload.product_id)
        if not stock or stock.quantity < payload.quantity:
            raise HTTPException(400, "Недостаточно остатков")
        stock.quantity -= payload.quantity
        db.add(models.StockMovement(product_id=payload.product_id, user_id=user.id, order_id=o.id,
                                    type="out", quantity=payload.quantity, cost=payload.unit_cost,
                                    note=f"Заказ {o.number}"))
    db.refresh(o)
    o.total_amount = _calc_total(o.items, o.discount_amount)
    db.commit(); db.refresh(oi)
    return oi


@router.delete("/{order_id}/items/{item_id}", status_code=204)
def del_item(order_id: int, item_id: int, db: Session = Depends(get_db),
             user: models.User = Depends(require_roles("admin", "manager"))):
    o = db.get(models.Order, order_id)
    if not o:
        raise HTTPException(404, "Не найден")
    item = db.get(models.OrderItem, item_id)
    if not item or item.order_id != order_id:
        raise HTTPException(404, "Позиция не найдена")
    # вернуть на склад
    if item.kind == "part" and item.product_id:
        stock = db.get(models.Stock, item.product_id)
        if stock:
            stock.quantity += item.quantity
            db.add(models.StockMovement(product_id=item.product_id, user_id=user.id, order_id=o.id,
                                        type="in", quantity=item.quantity, cost=item.unit_cost,
                                        note=f"Возврат из заказа {o.number}"))
    db.delete(item); db.flush()
    db.refresh(o)
    o.total_amount = _calc_total(o.items, o.discount_amount)
    db.commit()
