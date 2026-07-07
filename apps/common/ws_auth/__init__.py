"""
Channels (WebSocket) uchun JWT autentifikatsiya middleware.

Frontend SPA cookie/sessiyadan emas, localStorage'dagi JWT access tokendan
foydalanadi (bearer token), shuning uchun standart Channels
``AuthMiddlewareStack`` (faqat Django sessiyasini biladi) kuryer/mijoz
socket ulanishlarida ishlamaydi.

Bu middleware WebSocket so'rovining query-string'idan ``?token=<access>``
ni o'qiydi, uni SimpleJWT orqali tekshiradi va tegishli foydalanuvchini
``scope["user"]`` ga qo'yadi. Token yo'q yoki yaroqsiz bo'lsa
foydalanuvchi ``AnonymousUser`` bo'lib qoladi (consumer o'zi 4001 bilan
yopadi).

Frontend tomonda ulanish shunday quriladi:
    wss://.../ws/courier/?token=<access_token>
"""
from urllib.parse import parse_qs

from channels.db import database_sync_to_async
from channels.middleware import BaseMiddleware
from django.contrib.auth.models import AnonymousUser


@database_sync_to_async
def get_user_from_token(raw_token):
    from rest_framework_simplejwt.exceptions import TokenError
    from rest_framework_simplejwt.tokens import AccessToken
    from apps.accounts.models import User

    if not raw_token:
        return AnonymousUser()
    try:
        validated = AccessToken(raw_token)
        user_id = validated["user_id"]
        return User.objects.get(id=user_id)
    except (TokenError, User.DoesNotExist, KeyError):
        return AnonymousUser()


class JWTAuthMiddleware(BaseMiddleware):
    """WebSocket scope'ga ``?token=`` query-parametr orqali JWT auth qo'shadi."""

    async def __call__(self, scope, receive, send):
        query_string = scope.get("query_string", b"").decode()
        query_params = parse_qs(query_string)
        raw_token = (query_params.get("token") or [None])[0]
        scope["user"] = await get_user_from_token(raw_token)
        return await super().__call__(scope, receive, send)


def JWTAuthMiddlewareStack(inner):
    return JWTAuthMiddleware(inner)
