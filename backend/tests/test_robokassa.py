"""Unit tests for RobokassaService: signature generation/verification, receipt JSON.

No database required -- pure unit tests.
"""

import hashlib
import os

import pytest

from app.services.robokassa_service import RobokassaCredentials, RobokassaService


@pytest.fixture(autouse=True)
def set_encryption_key():
    """Ensure ENCRYPTION_KEY is set for encryption tests."""
    from cryptography.fernet import Fernet

    key = Fernet.generate_key().decode()
    os.environ.setdefault("ENCRYPTION_KEY", key)


def _make_creds(
    algorithm: str = "sha256",
    is_test: bool = False,
) -> RobokassaCredentials:
    return RobokassaCredentials(
        merchant_login="test_merchant",
        password1="password1_secret",
        password2="password2_secret",
        is_test=is_test,
        hash_algorithm=algorithm,
    )


# --- Compute hash ---


def test_compute_hash_md5():
    data = "test:data:string"
    expected = hashlib.md5(data.encode("utf-8")).hexdigest()
    result = RobokassaService._compute_hash(data, "md5")
    assert result == expected


def test_compute_hash_sha256():
    data = "test:data:string"
    expected = hashlib.sha256(data.encode("utf-8")).hexdigest()
    result = RobokassaService._compute_hash(data, "sha256")
    assert result == expected


# --- Generate payment URL ---


def test_generate_payment_url():
    creds = _make_creds()
    url = RobokassaService.generate_payment_url(
        creds=creds,
        inv_id=42,
        out_sum="1500.00",
        description="Test payment",
    )
    assert "MerchantLogin=test_merchant" in url
    assert "OutSum=1500.00" in url
    assert "InvId=42" in url
    assert "SignatureValue=" in url
    assert "Description=" in url


def test_generate_payment_url_with_receipt():
    creds = _make_creds()
    receipt = RobokassaService.build_receipt_json(
        service_name="Haircut",
        amount_rub="1500.00",
        sno="patent",
    )
    url = RobokassaService.generate_payment_url(
        creds=creds,
        inv_id=43,
        out_sum="1500.00",
        description="Payment with receipt",
        receipt_json=receipt,
    )
    assert "Receipt=" in url


def test_generate_payment_url_test_mode():
    creds = _make_creds(is_test=True)
    url = RobokassaService.generate_payment_url(
        creds=creds,
        inv_id=44,
        out_sum="500.00",
        description="Test mode payment",
    )
    assert "IsTest=1" in url


def test_generate_payment_url_with_shp_params():
    creds = _make_creds()
    shp_params = {
        "Shp_master_id": "abc-123",
        "Shp_booking_id": "def-456",
    }
    url = RobokassaService.generate_payment_url(
        creds=creds,
        inv_id=45,
        out_sum="1000.00",
        description="With Shp params",
        shp_params=shp_params,
    )
    assert "Shp_master_id=abc-123" in url
    assert "Shp_booking_id=def-456" in url


# --- Verify result signature ---


def test_verify_result_signature_valid():
    creds = _make_creds()
    out_sum = "1500.00"
    inv_id = "42"
    # Compute expected signature using Password#2
    sig_data = f"{out_sum}:{inv_id}:{creds.password2}"
    expected_sig = hashlib.sha256(sig_data.encode("utf-8")).hexdigest()

    result = RobokassaService.verify_result_signature(
        creds=creds,
        out_sum=out_sum,
        inv_id=inv_id,
        received_signature=expected_sig,
    )
    assert result is True


def test_verify_result_signature_invalid():
    creds = _make_creds()
    result = RobokassaService.verify_result_signature(
        creds=creds,
        out_sum="1500.00",
        inv_id="42",
        received_signature="definitely_wrong_signature",
    )
    assert result is False


def test_verify_result_signature_case_insensitive():
    creds = _make_creds()
    out_sum = "1500.00"
    inv_id = "42"
    sig_data = f"{out_sum}:{inv_id}:{creds.password2}"
    expected_sig = hashlib.sha256(sig_data.encode("utf-8")).hexdigest()

    # Send uppercase signature
    result = RobokassaService.verify_result_signature(
        creds=creds,
        out_sum=out_sum,
        inv_id=inv_id,
        received_signature=expected_sig.upper(),
    )
    assert result is True


# --- Build receipt JSON ---


def test_build_receipt_json():
    receipt = RobokassaService.build_receipt_json(
        service_name="Haircut",
        amount_rub="1500.00",
        sno="patent",
    )
    assert receipt["sno"] == "patent"
    assert len(receipt["items"]) == 1
    item = receipt["items"][0]
    assert item["name"] == "Haircut"
    assert item["quantity"] == 1
    assert item["sum"] == 1500.00
    assert item["tax"] == "none"
    assert item["payment_method"] == "full_payment"
    assert item["payment_object"] == "service"


def test_build_receipt_json_long_name():
    long_name = "A" * 200
    receipt = RobokassaService.build_receipt_json(
        service_name=long_name,
        amount_rub="100.00",
    )
    assert len(receipt["items"][0]["name"]) == 128


# --- Encryption roundtrip ---


def test_encrypt_decrypt_roundtrip():
    from app.services.encryption_service import decrypt_value, encrypt_value

    original = "my_secret_password"
    encrypted = encrypt_value(original)
    decrypted = decrypt_value(encrypted)
    assert decrypted == original
    assert encrypted != original


def test_decrypt_invalid_token():
    from app.services.encryption_service import decrypt_value

    result = decrypt_value("not-a-valid-fernet-token")
    assert result is None


# --- PaymentService.format_receipt_data ---


def test_format_receipt_data():
    from app.services.payment_service import PaymentService

    result = PaymentService.format_receipt_data(
        amount_kopecks=150000,
        service_name="Manicure",
        client_name="Anna Ivanova",
    )
    assert "1" in result["amount_display"]  # 1500.00
    assert "500" in result["amount_display"]
    assert result["service_name"] == "Manicure"
    assert result["client_name"] == "Anna Ivanova"
    assert "." in result["date"]  # dd.mm.yyyy format
