"""Salary calculation models:
   итог = base_salary*коэф_дней + work_share_pct*стоимость_работ + parts_share_pct*наценка_на_запчасти
                                + revenue_share_pct*выручка + bonus - deduction
"""
from datetime import date, datetime
from decimal import Decimal
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, and_
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db
from ..deps import require_roles, get_current_user

router = APIRouter()


@router.get("/rules", response_model=List[schemas.SalaryRuleOut])
def list_rules(db: Session = Depends(get_db), _=Depends(get_current_user)):
    return db.scalars(select(models.SalaryRule).order_by(models.SalaryRule.id.desc())).all()


@router.post("/rules", response_model=schemas.SalaryRuleOut, status_code=201)
def create_rule(payload: schemas.SalaryRuleIn, db: Session = Depends(get_db),
                _=Depends(require_roles("admin", "accountant"))):
    if not db.get(models.User, payload.user_id):
        raise HTTPException(400, "Сотрудник не найден")
    r = models.SalaryRule(**payload.model_dump())
    db.add(r); db.commit(); db.refresh(r)
    return r


@router.put("/rules/{rule_id}", response_model=schemas.SalaryRuleOut)
def update_rule(rule_id: int, payload: schemas.SalaryRuleIn, db: Session = Depends(get_db),
                _=Depends(require_roles("admin", "accountant"))):
    r = db.get(models.SalaryRule, rule_id)
    if not r:
        raise HTTPException(404, "Правило не найдено")
    for k, v in payload.model_dump().items():
        setattr(r, k, v)
    db.commit(); db.refresh(r)
    return r


def _active_rule(db: Session, user_id: int, on_day: date) -> models.SalaryRule | None:
    rules = db.scalars(
        select(models.SalaryRule).where(models.SalaryRule.user_id == user_id)
        .order_by(models.SalaryRule.id.desc())
    ).all()
    for r in rules:
        if r.valid_from <= on_day and (r.valid_to is None or r.valid_to >= on_day):
            return r
    return rules[0] if rules else None


@router.post("/calc", response_model=schemas.SalaryRecordOut)
def calc_salary(payload: schemas.SalaryCalcIn, db: Session = Depends(get_db),
                actor: models.User = Depends(require_roles("admin", "accountant"))):
    user = db.get(models.User, payload.user_id)
    if not user:
        raise HTTPException(404, "Сотрудник не найден")
    rule = _active_rule(db, user.id, payload.period_start)
    if not rule:
        raise HTTPException(400, "Не задано правило начисления для сотрудника")

    # выручка по выданным заказам, где сотрудник — мастер или менеджер
    works_amount = Decimal('0')
    parts_amount = Decimal('0')   # наценка = (price - cost) * qty
    revenue_amount = Decimal('0')
    breakdown_orders: list[dict] = []

    orders = db.scalars(
        select(models.Order).where(
            and_(
                models.Order.issued_at.isnot(None),
                models.Order.issued_at >= payload.period_start,
                models.Order.issued_at < payload.period_end,
            )
        )
    ).all()

    for o in orders:
        is_master = (o.master_id == user.id)
        is_manager = (o.manager_id == user.id)
        if not (is_master or is_manager):
            continue
        order_works = Decimal('0')
        order_parts_margin = Decimal('0')
        for it in o.items:
            line_total = (it.unit_price or 0) * (it.quantity or 0)
            if it.kind == "service":
                # доля мастера: процент по позиции имеет приоритет
                share = it.master_share_pct or rule.work_share_pct
                if is_master:
                    order_works += line_total * share / Decimal('100')
            else:  # part
                margin = ((it.unit_price or 0) - (it.unit_cost or 0)) * (it.quantity or 0)
                if margin < 0:
                    margin = Decimal('0')
                if is_master and rule.parts_share_pct:
                    order_parts_margin += margin * rule.parts_share_pct / Decimal('100')
        # доля менеджера от общей выручки заказа
        order_rev_share = Decimal('0')
        if is_manager and rule.revenue_share_pct:
            order_rev_share = (o.total_amount or Decimal('0')) * rule.revenue_share_pct / Decimal('100')

        works_amount += order_works
        parts_amount += order_parts_margin
        revenue_amount += order_rev_share
        if order_works or order_parts_margin or order_rev_share:
            breakdown_orders.append({
                "order_id": o.id, "number": o.number,
                "works": str(order_works), "parts_margin": str(order_parts_margin),
                "revenue_share": str(order_rev_share),
            })

    # Окладная часть пропорционально длительности периода (упрощение: full base)
    base_amount = rule.base_salary or Decimal('0')

    total = base_amount + works_amount + parts_amount + revenue_amount + payload.bonus_amount - payload.deduction_amount

    rec = models.SalaryRecord(
        user_id=user.id, period_start=payload.period_start, period_end=payload.period_end,
        base_amount=base_amount, works_amount=works_amount, parts_amount=parts_amount,
        revenue_amount=revenue_amount, bonus_amount=payload.bonus_amount,
        deduction_amount=payload.deduction_amount, total_amount=total,
        breakdown={"orders": breakdown_orders, "rule_id": rule.id},
    )

    if payload.save:
        # upsert by (user_id, period_start, period_end)
        existing = db.scalar(select(models.SalaryRecord).where(
            and_(models.SalaryRecord.user_id == user.id,
                 models.SalaryRecord.period_start == payload.period_start,
                 models.SalaryRecord.period_end == payload.period_end)))
        if existing:
            for fld in ("base_amount", "works_amount", "parts_amount", "revenue_amount",
                        "bonus_amount", "deduction_amount", "total_amount", "breakdown"):
                setattr(existing, fld, getattr(rec, fld))
            db.commit(); db.refresh(existing)
            return existing
        else:
            db.add(rec); db.commit(); db.refresh(rec)
            return rec
    return rec


@router.get("/records", response_model=List[schemas.SalaryRecordOut])
def list_records(user_id: int | None = None, db: Session = Depends(get_db),
                 _=Depends(require_roles("admin", "accountant"))):
    stmt = select(models.SalaryRecord).order_by(models.SalaryRecord.id.desc())
    if user_id:
        stmt = stmt.where(models.SalaryRecord.user_id == user_id)
    return db.scalars(stmt).all()


@router.post("/records/{rec_id}/pay", response_model=schemas.SalaryRecordOut)
def pay_record(rec_id: int, db: Session = Depends(get_db),
               actor: models.User = Depends(require_roles("admin", "accountant"))):
    rec = db.get(models.SalaryRecord, rec_id)
    if not rec:
        raise HTTPException(404, "Запись не найдена")
    if rec.paid:
        raise HTTPException(400, "Уже выплачена")
    rec.paid = True
    rec.paid_at = datetime.utcnow()
    # фиксируем как расход
    db.add(models.Transaction(
        user_id=actor.id, type="expense", method="cash",
        amount=rec.total_amount, category="salary",
        description=f"Зарплата за {rec.period_start} — {rec.period_end} (user_id={rec.user_id})",
    ))
    db.commit(); db.refresh(rec)
    return rec
