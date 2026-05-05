from datetime import date, datetime, timezone, timedelta
from decimal import Decimal
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db
from ..deps import get_current_user

router = APIRouter()


def _parse_period(period_start: Optional[date], period_end: Optional[date]):
    if not period_end:
        period_end = date.today() + timedelta(days=1)
    if not period_start:
        period_start = period_end - timedelta(days=30)
    return period_start, period_end


@router.get("/summary", response_model=schemas.ReportSummary)
def summary(period_start: Optional[date] = Query(None),
            period_end: Optional[date] = Query(None),
            db: Session = Depends(get_db), _=Depends(get_current_user)):
    period_start, period_end = _parse_period(period_start, period_end)

    orders_total = db.scalar(
        select(func.count(models.Order.id))
        .where(models.Order.created_at >= period_start, models.Order.created_at < period_end)
    ) or 0
    by_status_rows = db.execute(
        select(models.Order.status, func.count())
        .where(models.Order.created_at >= period_start, models.Order.created_at < period_end)
        .group_by(models.Order.status)
    ).all()
    by_status = {s: int(n) for s, n in by_status_rows}

    income = db.scalar(
        select(func.coalesce(func.sum(models.Transaction.amount), 0))
        .where(models.Transaction.type == "income",
               models.Transaction.created_at >= period_start,
               models.Transaction.created_at < period_end)
    ) or Decimal('0')
    expense = db.scalar(
        select(func.coalesce(func.sum(models.Transaction.amount), 0))
        .where(models.Transaction.type == "expense",
               models.Transaction.created_at >= period_start,
               models.Transaction.created_at < period_end)
    ) or Decimal('0')

    avg_check = Decimal('0')
    closed_orders_total = db.scalar(
        select(func.coalesce(func.sum(models.Order.total_amount), 0))
        .where(models.Order.issued_at.isnot(None),
               models.Order.issued_at >= period_start,
               models.Order.issued_at < period_end)
    ) or Decimal('0')
    closed_count = db.scalar(
        select(func.count(models.Order.id))
        .where(models.Order.issued_at.isnot(None),
               models.Order.issued_at >= period_start,
               models.Order.issued_at < period_end)
    ) or 0
    if closed_count:
        avg_check = closed_orders_total / closed_count

    return schemas.ReportSummary(
        period_start=period_start, period_end=period_end,
        orders_total=orders_total, orders_by_status=by_status,
        revenue=income, expense=expense, profit=income - expense,
        avg_check=avg_check,
    )


@router.get("/stock-value")
def stock_value(db: Session = Depends(get_db), _=Depends(get_current_user)):
    row = db.execute(
        select(
            func.coalesce(func.sum(models.Stock.quantity * models.Product.cost), 0).label("by_cost"),
            func.coalesce(func.sum(models.Stock.quantity * models.Product.price), 0).label("by_price"),
            func.count(models.Stock.product_id).label("positions"),
        ).join(models.Product, models.Product.id == models.Stock.product_id)
    ).one()
    return {"by_cost": row.by_cost, "by_price": row.by_price, "positions": row.positions}


@router.get("/top-customers")
def top_customers(limit: int = 10, db: Session = Depends(get_db), _=Depends(get_current_user)):
    rows = db.execute(
        select(
            models.Customer.id, models.Customer.full_name, models.Customer.phone,
            func.count(models.Order.id).label("orders"),
            func.coalesce(func.sum(models.Order.total_amount), 0).label("amount"),
        ).join(models.Order, models.Order.customer_id == models.Customer.id)
        .group_by(models.Customer.id)
        .order_by(func.coalesce(func.sum(models.Order.total_amount), 0).desc())
        .limit(limit)
    ).all()
    return [{"id": r.id, "name": r.full_name, "phone": r.phone,
             "orders": int(r.orders), "amount": r.amount} for r in rows]
