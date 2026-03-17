from app.services.phone_service import normalize_phone


def test_normalize_standard_plus7():
    assert normalize_phone("+79161234567") == "+79161234567"


def test_normalize_eight_prefix():
    assert normalize_phone("89161234567") == "+79161234567"


def test_normalize_without_country():
    assert normalize_phone("9161234567") == "+79161234567"


def test_normalize_with_formatting():
    assert normalize_phone("+7 (916) 123-45-67") == "+79161234567"


def test_normalize_with_dashes():
    assert normalize_phone("8-916-123-45-67") == "+79161234567"


def test_normalize_invalid():
    assert normalize_phone("invalid") is None


def test_normalize_empty():
    assert normalize_phone("") is None


def test_normalize_too_short():
    assert normalize_phone("123") is None
