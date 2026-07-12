"""
apps/common/api/health.py

Konteynerlar (docker-compose healthcheck) va nginx uchun yengil health-check
endpointi. Autentifikatsiya talab qilmaydi, DB va Redis ulanishini tekshiradi.

GET /api/v1/health/  -> 200 {"status": "ok"}  yoki 503 {"status": "error", ...}
"""
from django.db import connections
from django.db.utils import OperationalError
from django.http import JsonResponse
from django.views.decorators.http import require_GET
from django.views.decorators.csrf import csrf_exempt


@csrf_exempt
@require_GET
def health_check(request):
    checks = {}

    # --- Database ---
    try:
        connections["default"].cursor()
        checks["database"] = "ok"
    except OperationalError:
        checks["database"] = "error"

    # --- Redis (cache/broker) ---
    try:
        import redis
        from decouple import config as env_config

        redis_host = env_config("REDIS_HOST", default="127.0.0.1")
        redis_port = env_config("REDIS_PORT", default=6379, cast=int)
        redis_password = env_config("REDIS_PASSWORD", default="")
        redis_url = (
            f"redis://:{redis_password}@{redis_host}:{redis_port}/0"
            if redis_password
            else f"redis://{redis_host}:{redis_port}/0"
        )
        client = redis.from_url(redis_url, socket_connect_timeout=2)
        client.ping()
        checks["redis"] = "ok"
    except Exception:
        checks["redis"] = "error"

    healthy = all(v == "ok" for v in checks.values())
    return JsonResponse(
        {"status": "ok" if healthy else "error", "checks": checks},
        status=200 if healthy else 503,
    )
