import base64
import hashlib
import hmac
import json
import urllib.parse
from collections import OrderedDict
from datetime import datetime, timedelta, timezone

import jwt
from jwt.exceptions import InvalidTokenError
from pwdlib import PasswordHash

from app.core.config import settings

password_hash = PasswordHash.recommended()  # Argon2
DUMMY_HASH = password_hash.hash("dummy")  # Timing attack prevention


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return password_hash.verify(plain_password, hashed_password)


def hash_password(password: str) -> str:
    return password_hash.hash(password)


def create_access_token(
    data: dict, expires_delta: timedelta | None = None
) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta
        or timedelta(minutes=settings.access_token_expire_minutes)
    )
    to_encode.update({"exp": expire})
    return jwt.encode(
        to_encode, settings.jwt_secret_key, algorithm=settings.jwt_algorithm
    )


def decode_access_token(token: str) -> dict:
    return jwt.decode(
        token,
        settings.jwt_secret_key,
        algorithms=[settings.jwt_algorithm],
    )


def validate_tg_init_data(
    init_data_raw: str,
    bot_token: str,
    max_age_seconds: int = 86400,
) -> dict | None:
    """
    Validate Telegram Mini App initData per Telegram documentation.

    Returns parsed user dict on success, None on failure.
    Uses HMAC-SHA256 with timing-safe comparison.
    """
    if not init_data_raw or not bot_token:
        return None

    try:
        # Parse as URL-encoded query params
        parsed = urllib.parse.parse_qs(init_data_raw, keep_blank_values=True)

        # Extract hash
        hash_values = parsed.pop("hash", None)
        if not hash_values:
            return None
        received_hash = hash_values[0]

        # Build data-check-string: sort remaining params alphabetically,
        # join as "key=value\n"
        # parse_qs returns lists, so flatten to first value
        data_pairs = []
        for key in sorted(parsed.keys()):
            value = parsed[key][0]
            data_pairs.append(f"{key}={value}")
        data_check_string = "\n".join(data_pairs)

        # Create secret key: HMAC-SHA256 of bot_token with "WebAppData" as key
        secret_key = hmac.new(
            b"WebAppData", bot_token.encode("utf-8"), hashlib.sha256
        ).digest()

        # Compute expected hash
        computed_hash = hmac.new(
            secret_key, data_check_string.encode("utf-8"), hashlib.sha256
        ).hexdigest()

        # Timing-safe comparison (NOT == to prevent timing attacks)
        if not hmac.compare_digest(computed_hash, received_hash):
            return None

        # Check auth_date freshness
        auth_date_values = parsed.get("auth_date")
        if auth_date_values:
            auth_date = int(auth_date_values[0])
            now = int(datetime.now(timezone.utc).timestamp())
            if now - auth_date > max_age_seconds:
                return None

        # Parse user JSON
        user_values = parsed.get("user")
        if user_values:
            return json.loads(user_values[0])

        return None
    except (ValueError, KeyError, json.JSONDecodeError):
        return None


def validate_max_init_data(
    init_data_raw: str, bot_token: str, max_age_seconds: int = 86400
) -> dict | None:
    """Validate MAX Mini App initData. Algorithm identical to Telegram."""
    return validate_tg_init_data(init_data_raw, bot_token, max_age_seconds)


def validate_vk_launch_params(
    query_string: str, app_secret: str
) -> dict | None:
    """
    Validate VK Mini App launch parameters.

    Verifies HMAC-SHA256 signature on vk_* params using the app secret.
    Returns flattened dict of all params on success, None on failure.
    """
    if not query_string or not app_secret:
        return None

    try:
        parsed = urllib.parse.parse_qs(query_string, keep_blank_values=True)

        # Extract sign
        sign_values = parsed.get("sign")
        if not sign_values:
            return None
        received_sign = sign_values[0]

        # Filter params starting with "vk_", sort alphabetically
        vk_params = OrderedDict(
            sorted(
                (k, v[0])
                for k, v in parsed.items()
                if k.startswith("vk_")
            )
        )

        # URL-encode sorted vk_* params
        encoded_string = urllib.parse.urlencode(vk_params)

        # HMAC-SHA256 with app_secret
        hash_bytes = hmac.new(
            app_secret.encode("utf-8"),
            encoded_string.encode("utf-8"),
            hashlib.sha256,
        ).digest()

        # base64-encode, strip trailing "=", URL-safe replacements
        computed_sign = (
            base64.b64encode(hash_bytes)
            .decode("utf-8")
            .rstrip("=")
            .replace("+", "-")
            .replace("/", "_")
        )

        # Timing-safe comparison
        if not hmac.compare_digest(computed_sign, received_sign):
            return None

        # Return all params as flat dict
        return {k: v[0] for k, v in parsed.items()}

    except (ValueError, KeyError):
        return None
