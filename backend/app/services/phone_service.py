import phonenumbers
from phonenumbers import NumberParseException


def normalize_phone(raw_phone: str, default_region: str = "RU") -> str | None:
    """
    Normalize a phone number to E.164 format.
    Returns None if the number is invalid.

    Examples:
        "89161234567"        -> "+79161234567"
        "+7 (916) 123-45-67" -> "+79161234567"
        "9161234567"         -> "+79161234567"
        "+79161234567"       -> "+79161234567"
    """
    if not raw_phone or not raw_phone.strip():
        return None
    try:
        parsed = phonenumbers.parse(raw_phone.strip(), default_region)
        if not phonenumbers.is_valid_number(parsed):
            return None
        return phonenumbers.format_number(
            parsed, phonenumbers.PhoneNumberFormat.E164
        )
    except NumberParseException:
        return None
