from phonenumbers import parse, format_number, PhoneNumberFormat


def normalize_phone(phone: str) -> str:
    """Telefon raqami berilgan bo'lsa E164 formatga o'giradi. Endi auth uchun ishlatilmaydi,
    lekin foydalanuvchi profilida ixtiyoriy maydon sifatida qolishi mumkin."""
    parsed = parse(phone, "UZ")
    return format_number(parsed, PhoneNumberFormat.E164)