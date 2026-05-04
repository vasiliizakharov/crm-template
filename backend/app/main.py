"""CRM Template — FastAPI entry point."""
from fastapi import FastAPI
from fastapi.responses import PlainTextResponse
from prometheus_client import Counter, generate_latest, CONTENT_TYPE_LATEST

app = FastAPI(title="CRM Template", version="0.1.0",
              description="Generic CRM template for small businesses")

requests_total = Counter("crm_requests_total", "Total HTTP requests",
                         ["method", "endpoint"])

@app.get("/")
def root():
    return {"app": "crm-template", "status": "running",
            "docs": "/docs", "metrics": "/metrics"}

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/metrics")
def metrics():
    return PlainTextResponse(generate_latest(), media_type=CONTENT_TYPE_LATEST)

# TODO: include routers
# from .routers import customers, orders, inventory, finance, auth
# app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])
# app.include_router(customers.router, prefix="/api/v1/customers", tags=["customers"])
# app.include_router(orders.router, prefix="/api/v1/orders", tags=["orders"])
# app.include_router(inventory.router, prefix="/api/v1/inventory", tags=["inventory"])
# app.include_router(finance.router, prefix="/api/v1/finance", tags=["finance"])
