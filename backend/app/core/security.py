import hashlib
import hmac
import json
import urllib.parse
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
