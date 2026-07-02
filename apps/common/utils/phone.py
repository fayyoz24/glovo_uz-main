import re


def normalize_phone(phone: str) -> str:
    """
    Normalize Uzbekistan phone numbers to +998XXXXXXXXX format.
    Accepts: 998901234567, 0901234567, +998901234567
    """
    digits = re.sub(r"\D", "", phone)
    if digits.startswith("998") and len(digits) == 12:
        return f"+{digits}"
    if digits.startswith("0") and len(digits) == 10:
        return f"+998{digits[1:]}"
    if len(digits) == 9:
        return f"+998{digits}"
    return phone  # return as-is if unrecognized
