from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.orm import Session

from .. import models, schemas, auth as auth_lib
from ..database import get_db
from ..deps import get_current_user

router = APIRouter()


@router.post("/login", response_model=schemas.Token)
def login(form: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.scalar(select(models.User).where(models.User.email == form.username.lower()))
    if not user or not auth_lib.verify_password(form.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Неверный email или пароль")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Учётная запись отключена")
    user.last_login_at = datetime.now(timezone.utc)
    db.commit()
    token = auth_lib.create_access_token(user.id, user.role, user.email, user.full_name)
    return schemas.Token(access_token=token, user=schemas.UserOut.model_validate(user))


@router.post("/login-json", response_model=schemas.Token)
def login_json(payload: schemas.LoginIn, db: Session = Depends(get_db)):
    """Альтернативный JSON-логин (fetch-friendly)."""
    user = db.scalar(select(models.User).where(models.User.email == payload.email.lower()))
    if not user or not auth_lib.verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Неверный email или пароль")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Учётная запись отключена")
    user.last_login_at = datetime.now(timezone.utc)
    db.commit()
    token = auth_lib.create_access_token(user.id, user.role, user.email, user.full_name)
    return schemas.Token(access_token=token, user=schemas.UserOut.model_validate(user))


@router.get("/me", response_model=schemas.UserOut)
def me(user: models.User = Depends(get_current_user)):
    return user
