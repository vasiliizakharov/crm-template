from typing import Iterable
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from .auth import decode_token
from .database import get_db
from . import models

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> models.User:
    creds_err = HTTPException(status_code=401, detail="Не авторизован",
                              headers={"WWW-Authenticate": "Bearer"})
    payload = decode_token(token)
    if not payload:
        raise creds_err
    user_id = int(payload.get("sub", 0))
    user = db.get(models.User, user_id)
    if not user or not user.is_active:
        raise creds_err
    return user


def require_roles(*roles: str):
    allowed = set(roles)

    def dep(user: models.User = Depends(get_current_user)) -> models.User:
        if user.role not in allowed:
            raise HTTPException(status_code=403, detail=f"Доступ запрещён. Требуется роль: {', '.join(allowed)}")
        return user

    return dep
