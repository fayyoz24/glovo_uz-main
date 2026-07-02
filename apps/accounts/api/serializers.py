from rest_framework import serializers
from apps.accounts.models import User
from apps.accounts.constants import Language, LOGIN_CODE_LENGTH


class GenerateLoginCodeSerializer(serializers.Serializer):
    """Bot -> Backend: yangi login kodi so'raladi."""
    telegram_user_id = serializers.IntegerField()
    telegram_username = serializers.CharField(required=False, allow_blank=True, default="")
    telegram_first_name = serializers.CharField(required=False, allow_blank=True, default="")


class LoginCodeResponseSerializer(serializers.Serializer):
    """Backend -> Bot: yaratilgan kod va uning amal qilish muddati."""
    code = serializers.CharField()
    expires_in = serializers.IntegerField()


class VerifyLoginCodeSerializer(serializers.Serializer):
    """Frontend -> Backend: foydalanuvchi saytga kiritgan kod."""
    code = serializers.CharField(min_length=LOGIN_CODE_LENGTH, max_length=LOGIN_CODE_LENGTH)


class UserMeSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            "id", "telegram_user_id", "telegram_username",
            "phone", "email", "full_name",
            "role", "language", "is_verified",
        ]
        read_only_fields = ["id", "telegram_user_id", "telegram_username", "role", "is_verified"]

    def validate_language(self, value):
        valid_langs = [lang[0] for lang in Language.CHOICES]
        if value not in valid_langs:
            raise serializers.ValidationError("Qo'llab-quvvatlanmaydigan til.")
        return value


class UpdateProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["full_name", "email", "phone", "language"]
