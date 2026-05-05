from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db
from ..deps import require_roles, get_current_user

router = APIRouter()


@router.get("/", response_model=List[schemas.DeviceOut])
def list_devices(customer_id: Optional[int] = Query(None),
                 db: Session = Depends(get_db), _=Depends(get_current_user)):
    stmt = select(models.Device).order_by(models.Device.id.desc())
    if customer_id:
        stmt = stmt.where(models.Device.customer_id == customer_id)
    return db.scalars(stmt).all()


@router.post("/", response_model=schemas.DeviceOut, status_code=201)
def create_device(payload: schemas.DeviceCreate, db: Session = Depends(get_db),
                  _=Depends(require_roles("admin", "manager"))):
    if not db.get(models.Customer, payload.customer_id):
        raise HTTPException(400, "Клиент не найден")
    d = models.Device(**payload.model_dump())
    db.add(d); db.commit(); db.refresh(d)
    return d


@router.delete("/{device_id}", status_code=204)
def delete_device(device_id: int, db: Session = Depends(get_db),
                  _=Depends(require_roles("admin", "manager"))):
    d = db.get(models.Device, device_id)
    if d:
        db.delete(d); db.commit()
