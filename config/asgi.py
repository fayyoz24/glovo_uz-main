"""
ASGI config for config project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/6.0/howto/deployment/asgi/
"""

# import os

# from django.core.asgi import get_asgi_application

# os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

# application = get_asgi_application()

import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from config.routing import websocket_urlpatterns

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

# Frontend (React SPA) foydalanuvchini Django sessiyasi bilan emas, JWT bilan
# tanitadi, shuning uchun standart AuthMiddlewareStack o'rniga localStorage'dagi
# access tokenni ?token= query-parametridan o'qiydigan JWTAuthMiddlewareStack
# ishlatiladi (qarang: apps/common/ws_auth).
from apps.common.ws_auth import JWTAuthMiddlewareStack

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": JWTAuthMiddlewareStack(
        URLRouter(websocket_urlpatterns)
    ),
})

