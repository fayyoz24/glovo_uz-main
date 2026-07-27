"""
ASGI config for config project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/6.0/howto/deployment/asgi/
"""

import os

from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

# django.setup() ni chaqirish uchun avval HTTP ASGI app yaratamiz — shu orqali
# Django ilovalar registri to'liq yuklanadi. Shundan keyingina Django
# modellariga bog'liq boshqa modullarni (routing, ws_auth) import qilish
# mumkin, aks holda "AppRegistryNotReady" xatosi chiqadi.
django_asgi_app = get_asgi_application()

from channels.routing import ProtocolTypeRouter, URLRouter  # noqa: E402
from config.routing import websocket_urlpatterns  # noqa: E402

# Frontend (React SPA) foydalanuvchini Django sessiyasi bilan emas, JWT bilan
# tanitadi, shuning uchun standart AuthMiddlewareStack o'rniga localStorage'dagi
# access tokenni ?token= query-parametridan o'qiydigan JWTAuthMiddlewareStack
# ishlatiladi (qarang: apps/common/ws_auth).
from apps.common.ws_auth import JWTAuthMiddlewareStack  # noqa: E402

application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": JWTAuthMiddlewareStack(
        URLRouter(websocket_urlpatterns)
    ),
})