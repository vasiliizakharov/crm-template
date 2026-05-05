from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db
from ..deps import require_roles, get_current_user

router = APIRouter()


@router.get("/", response_model=List[schemas.BranchOut])
def list_branches(db: Session = Depends(get_db), _=Depends(get_current_user)):
    return db.scalars(select(models.Branch).order_by(models.Branch.id)).all()


@router.post("/", response_model=schemas.BranchOut, status_code=201)
def create_branch(payload: schemas.BranchCreate, db: Session = Depends(get_db),
                  _=Depends(require_roles("admin"))):
    if db.scalar(select(models.Branch).where(models.Branch.code == payload.code)):
        raise HTTPException(409, "Филиал с таким кодом уже существует")
    b = models.Branch(**payload.model_dump())
    db.add(b); db.commit(); db.refresh(b)
    return b


@router.put("/{branch_id}", response_model=schemas.BranchOut)
def update_branch(branch_id: int, payload: schemas.BranchCreate, db: Session = Depends(get_db),
                  _=Depends(require_roles("admin"))):
    b = db.get(models.Branch, branch_id)
    if not b:
        raise HTTPException(404, "Не найден")
    for k, v in payload.model_dump().items():
        setattr(b, k, v)
    db.commit(); db.refresh(b)
    return b
