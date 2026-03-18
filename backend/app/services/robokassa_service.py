"""Robokassa payment integration service.

Handles payment URL generation with HMAC signatures, ResultURL callback
verification, and Receipt JSON construction for 54-FZ fiscalization.

Signature formulas (from official docs):
- Initiation: hash(MerchantLogin:OutSum:InvId[:Receipt]:Password#1[:Shp_*])
- Callback:   hash(OutSum:InvId:Password#2[:Shp_*])
- Shp_ params sorted alphabetically by key name.
"""

import hashlib
import json
import urllib.parse
from dataclasses import dataclass


@dataclass
class RobokassaCredentials:
    """Decrypted Robokassa credentials for a specific master."""

    merchant_login: str
    password1: str  # decrypted Password#1 (for payment initiation)
    password2: str  # decrypted Password#2 (for callback verification)
    is_test: bool = False
    hash_algorithm: str = "sha256"  # md5, sha256, sha512


class RobokassaService:
    """Stateless service for Robokassa payment integration."""

    PAYMENT_URL = "https://auth.robokassa.ru/Merchant/Index.aspx"

    @staticmethod
    def _compute_hash(data: str, algorithm: str) -> str:
        """Compute hash using the configured algorithm.

        Args:
            data: The string to hash (colon-separated signature parts).
            algorithm: One of "md5", "sha256", "sha512".

        Returns:
            Hex-encoded hash string.
        """
        if algorithm == "md5":
            return hashlib.md5(data.encode("utf-8")).hexdigest()
        elif algorithm == "sha256":
            return hashlib.sha256(data.encode("utf-8")).hexdigest()
        elif algorithm == "sha512":
            return hashlib.sha512(data.encode("utf-8")).hexdigest()
        raise ValueError(f"Unsupported hash algorithm: {algorithm}")

    @staticmethod
    def generate_payment_url(
        creds: RobokassaCredentials,
        inv_id: int,
        out_sum: str,  # "100.00" format
        description: str,
        receipt_json: dict | None = None,
        shp_params: dict[str, str] | None = None,
        email: str | None = None,
    ) -> str:
        """Generate a signed Robokassa payment URL.

        Args:
            creds: Decrypted Robokassa credentials.
            inv_id: Unique integer invoice ID from robokassa_inv_id_seq.
            out_sum: Payment amount as string with 2 decimal places ("1500.00").
            description: Payment description shown to client.
            receipt_json: Optional Receipt JSON for fiscalization (54-FZ).
            shp_params: Optional custom Shp_ parameters (e.g. Shp_master_id).
            email: Optional client email for receipt delivery.

        Returns:
            Full payment URL with all parameters and signature.
        """
        # Build signature string
        sig_parts = [creds.merchant_login, out_sum, str(inv_id)]

        # Include Receipt in signature if present
        receipt_encoded = None
        if receipt_json:
            receipt_str = json.dumps(receipt_json, ensure_ascii=False)
            receipt_encoded = urllib.parse.quote(receipt_str)
            sig_parts.append(receipt_encoded)

        sig_parts.append(creds.password1)

        # Append Shp_ params sorted alphabetically
        if shp_params:
            for key in sorted(shp_params.keys()):
                sig_parts.append(f"{key}={shp_params[key]}")

        signature = RobokassaService._compute_hash(
            ":".join(sig_parts), creds.hash_algorithm
        )

        # Build URL params
        params = {
            "MerchantLogin": creds.merchant_login,
            "OutSum": out_sum,
            "InvId": str(inv_id),
            "SignatureValue": signature,
            "Description": description,
        }
        if receipt_encoded:
            params["Receipt"] = receipt_encoded
        if email:
            params["Email"] = email
        if creds.is_test:
            params["IsTest"] = "1"
        if shp_params:
            params.update(shp_params)

        return f"{RobokassaService.PAYMENT_URL}?{urllib.parse.urlencode(params)}"

    @staticmethod
    def verify_result_signature(
        creds: RobokassaCredentials,
        out_sum: str,
        inv_id: str,
        received_signature: str,
        shp_params: dict[str, str] | None = None,
    ) -> bool:
        """Verify ResultURL callback signature using Password#2.

        Args:
            creds: Decrypted Robokassa credentials.
            out_sum: Payment amount from callback.
            inv_id: Invoice ID from callback.
            received_signature: SignatureValue from callback.
            shp_params: Shp_ parameters from callback.

        Returns:
            True if signature is valid, False otherwise.
        """
        sig_parts = [out_sum, str(inv_id), creds.password2]

        if shp_params:
            for key in sorted(shp_params.keys()):
                sig_parts.append(f"{key}={shp_params[key]}")

        expected = RobokassaService._compute_hash(
            ":".join(sig_parts), creds.hash_algorithm
        )
        # Case-insensitive comparison (Robokassa may send uppercase)
        return expected.upper() == received_signature.upper()

    @staticmethod
    def build_receipt_json(
        service_name: str,
        amount_rub: str,  # "1500.00"
        sno: str = "patent",
    ) -> dict:
        """Build Receipt JSON for 54-FZ fiscalization via Robochecks.

        Args:
            service_name: Name of the service (truncated to 128 chars).
            amount_rub: Amount in rubles as string ("1500.00").
            sno: Tax system. "patent" for self-employed on patent,
                 other options: "osn", "usn_income", "usn_income_outcome",
                 "envd", "esn".

        Returns:
            Receipt dict ready for JSON serialization in payment URL.
        """
        return {
            "sno": sno,
            "items": [
                {
                    "name": service_name[:128],  # max 128 chars per Robokassa spec
                    "quantity": 1,
                    "sum": float(amount_rub),
                    "payment_method": "full_payment",
                    "payment_object": "service",
                    "tax": "none",  # self-employed on NPD/patent = no VAT
                }
            ],
        }
