from phonenumbers import parse, format_number, PhoneNumberFormat

from apps.accounts.models import User



def update_user_profile(user: User, validated_data: dict) -> User:
    allowed_fields = {"full_name", "email", "phone", "language"}
    for field in allowed_fields:
        if field in validated_data:
            setattr(user, field, validated_data[field])
    user.save(update_fields=list(allowed_fields & validated_data.keys()))
    return user