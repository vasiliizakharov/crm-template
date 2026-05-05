from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select, func

from .config import settings
from .database import SessionLocal
from .metrics import PrometheusMiddleware, metrics_endpoint, ORDERS_GAUGE
from .routers import (
    auth_router, users_router, branches_router, customers_router, devices_router,
    products_router, stock_router, orders_router, finance_router, salaries_router,
    reports_router,
)
from . import models


def update_orders_gauge():
    with SessionLocal() as db:
        rows = db.execute(
            select(models.Order.status, func.count()).group_by(models.Order.status)
        ).all()
        # reset
        for s in ('new', 'diagnosing', 'awaiting', 'in_repair', 'ready', 'issued', 'cancelled', 'warranty'):
            ORDERS_GAUGE.labels(s).set(0)
        for status, n in rows:
            ORDERS_GAUGE.labels(status).set(n)


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        update_orders_gauge()
    except Exception:
        pass
    yield


app = FastAPI(title=settings.app_name, version="1.0.0", lifespan=lifespan)

origins = [o.strip() for o in settings.cors_origins.split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins or ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(PrometheusMiddleware)


@app.get("/health")
def health():
    return {"status": "ok", "app": settings.app_name, "env": settings.app_env}


@app.get("/metrics")
def metrics():
    try:
        update_orders_gauge()
    except Exception:
        pass
    return metrics_endpoint()


# Routers
app.include_router(auth_router,     prefix="/api/auth",     tags=["auth"])
app.include_router(users_router,    prefix="/api/users",    tags=["users"])
app.include_router(branches_router, prefix="/api/branches", tags=["branches"])
app.include_router(customers_router,prefix="/api/customers",tags=["customers"])
app.include_router(devices_router,  prefix="/api/devices",  tags=["devices"])
app.include_router(products_router, prefix="/api/products", tags=["products"])
app.include_router(stock_router,    prefix="/api/stock",    tags=["stock"])
app.include_router(orders_router,   prefix="/api/orders",   tags=["orders"])
app.include_router(finance_router,  prefix="/api/finance",  tags=["finance"])
app.include_router(salaries_router, prefix="/api/salaries", tags=["salaries"])
app.include_router(reports_router,  prefix="/api/reports",  tags=["reports"])
