from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from .. import models, schemas, auth as auth_lib
from ..database import get_db
from ..deps import require_roles, get_current_user

router = APIRouter()


@router.get("/", response_model=List[schemas.UserOut])
def list_users(db: Session = Depends(get_db), _=Depends(get_current_user)):
    return db.scalars(select(models.User).order_by(models.User.id)).all()


@router.post("/", response_model=schemas.UserOut, status_code=201)
def create_user(payload: schemas.UserCreate, db: Session = Depends(get_db),
                _=Depends(require_roles("admin"))):
    if db.scalar(select(models.User).where(models.User.email == payload.email.lower())):
        raise HTTPException(409, "Пользователь с таким email уже существует")
    u = models.User(
        email=payload.email.lower(),
        full_name=payload.full_name,
        phone=payload.phone,
        role=payload.role,
        branch_id=payload.branch_id,
        is_active=payload.is_active,
        password_hash=auth_lib.hash_password(payload.password),
    )
    db.add(u); db.commit(); db.refresh(u)
    return u


@router.put("/{user_id}", response_model=schemas.UserOut)
def update_user(user_id: int, payload: schemas.UserUpdate, db: Session = Depends(get_db),
                actor: models.User = Depends(require_roles("admin"))):
    u = db.get(models.User, user_id)
    if not u:
        raise HTTPException(404, "Не найден")
    for fld in ("full_name", "phone", "role", "branch_id", "is_active"):
        v = getattr(payload, fld)
        if v is not None:
            setattr(u, fld, v)
    if payload.password:
        u.password_hash = auth_lib.hash_password(payload.password)
    db.commit(); db.refresh(u)
    return u


@router.delete("/{user_id}", status_code=204)
def delete_user(user_id: int, db: Session = Depends(get_db),
                actor: models.User = Depends(require_roles("admin"))):
    u = db.get(models.User, user_id)
    if not u:
        return
    if u.id == actor.id:
        raise HTTPException(400, "Нельзя удалить самого себя")
    u.is_active = False  # soft delete
    db.commit()
