from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
import time

REQUEST_COUNT = Counter(
    "service_crm_requests_total",
    "Total HTTP requests",
    ["method", "path", "status"],
)
REQUEST_LATENCY = Histogram(
    "service_crm_request_latency_seconds",
    "HTTP request latency",
    ["method", "path"],
    buckets=(0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2.5, 5, 10),
)
ORDERS_GAUGE = Gauge("service_crm_orders_total", "Total orders by status", ["status"])


class PrometheusMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        path = request.url.path
        if path == "/metrics":
            return await call_next(request)
        start = time.perf_counter()
        response = await call_next(request)
        elapsed = time.perf_counter() - start
        # collapse path params to route template if possible
        route = getattr(request.scope.get("route"), "path", path)
        REQUEST_COUNT.labels(request.method, route, response.status_code).inc()
        REQUEST_LATENCY.labels(request.method, route).observe(elapsed)
        return response


def metrics_endpoint() -> Response:
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)
