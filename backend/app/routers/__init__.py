from .auth import router as auth_router
from .users import router as users_router
from .branches import router as branches_router
from .customers import router as customers_router
from .devices import router as devices_router
from .products import router as products_router
from .stock import router as stock_router
from .orders import router as orders_router
from .finance import router as finance_router
from .salaries import router as salaries_router
from .reports import router as reports_router

__all__ = [
    "auth_router", "users_router", "branches_router", "customers_router", "devices_router",
    "products_router", "stock_router", "orders_router", "finance_router", "salaries_router",
    "reports_router",
]
