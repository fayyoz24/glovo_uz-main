from django.conf import settings
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, AllowAny

from apps.accounts.constants import LOGIN_CODE_EXPIRY_SECONDS
from apps.accounts.api.serializers import (
    GenerateLoginCodeSerializer,
    LoginCodeResponseSerializer,
    VerifyLoginCodeSerializer,
    UserMeSerializer,
    UpdateProfileSerializer,
)
from apps.accounts.services.auth import generate_login_code, verify_login_code
from apps.accounts.services.profile import update_user_profile


class TelegramGenerateCodeView(APIView):
    """
    POST /api/v1/auth/telegram/generate-code/

    FAQAT bot chaqiradi (X-Telegram-Bot-Api-Secret-Token bilan himoyalangan).
    Foydalanuvchi botga /start yuborganda — bot shu endpointdan yangi bir martalik
    kod so'raydi va uni foydalanuvchiga Telegram xabari sifatida yuboradi.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        secret = request.headers.get("X-Telegram-Bot-Api-Secret-Token", "")
        if not settings.TELEGRAM_BOT_SHARED_SECRET or secret != settings.TELEGRAM_BOT_SHARED_SECRET:
            return Response(status=status.HTTP_403_FORBIDDEN)

        serializer = GenerateLoginCodeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        login_code = generate_login_code(
            telegram_user_id=serializer.validated_data["telegram_user_id"],
            telegram_username=serializer.validated_data.get("telegram_username", ""),
            telegram_first_name=serializer.validated_data.get("telegram_first_name", ""),
        )
        response = LoginCodeResponseSerializer({
            "code": login_code.code,
            "expires_in": LOGIN_CODE_EXPIRY_SECONDS,
        })
        return Response(response.data, status=status.HTTP_200_OK)


class TelegramVerifyCodeView(APIView):
    """
    POST /api/v1/auth/telegram/verify-code/
    { "code": "123456" }

    Sayt (frontend) foydalanuvchi botdan olgan kodni shu yerga yuboradi.
    Muvaffaqiyatli bo'lsa — JWT tokenlar qaytadi (kerak bo'lsa User avtomatik yaratiladi).
    """
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = VerifyLoginCodeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        tokens = verify_login_code(code=serializer.validated_data["code"])
        return Response(tokens, status=status.HTTP_200_OK)


class MeView(APIView):
    """
    GET  /api/v1/auth/me/   — profil ma'lumotlari
    PATCH /api/v1/auth/me/  — profil yangilash
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = UserMeSerializer(request.user)
        return Response(serializer.data)

    def patch(self, request):
        serializer = UpdateProfileSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        user = update_user_profile(request.user, serializer.validated_data)
        return Response(UserMeSerializer(user).data)
