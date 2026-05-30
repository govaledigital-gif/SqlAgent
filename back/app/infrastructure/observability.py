import time

from fastapi import APIRouter, Request
from fastapi.responses import Response
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest
from starlette.middleware.base import BaseHTTPMiddleware

try:
    import sentry_sdk
    from sentry_sdk.integrations.fastapi import FastApiIntegration
except Exception:  # pragma: no cover - optional dependency
    sentry_sdk = None
    FastApiIntegration = None

from app.config.settings import settings


REQUEST_COUNT = Counter(
    "sqlagent_http_requests_total",
    "Total HTTP requests processed by the API",
    ["method", "path", "status"],
)

REQUEST_DURATION = Histogram(
    "sqlagent_http_request_duration_seconds",
    "HTTP request duration in seconds",
    ["method", "path"],
)

router = APIRouter(tags=["Observability"])


class MetricsMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start_time = time.perf_counter()
        response = await call_next(request)

        path = request.url.path
        method = request.method
        status_code = str(response.status_code)

        REQUEST_COUNT.labels(method=method, path=path, status=status_code).inc()
        REQUEST_DURATION.labels(method=method, path=path).observe(time.perf_counter() - start_time)

        return response


@router.get("/metrics")
def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


def init_sentry() -> None:
    if not settings.SENTRY_DSN or sentry_sdk is None:
        return

    sentry_sdk.init(
        dsn=settings.SENTRY_DSN,
        integrations=[FastApiIntegration(transaction_style="endpoint")],
        traces_sample_rate=0.0,
        send_default_pii=False,
    )