from typing import Literal

from pydantic import BaseModel, Field, field_validator


class MasterSettings(BaseModel):
    buffer_minutes: int
    cancellation_deadline_hours: int
    slot_interval_minutes: int

    model_config = {"from_attributes": True}


class MasterSettingsUpdate(BaseModel):
    buffer_minutes: int | None = Field(default=None, ge=0, le=60)
    cancellation_deadline_hours: int | None = Field(default=None, ge=0, le=72)
    slot_interval_minutes: int | None = None

    @field_validator("slot_interval_minutes")
    @classmethod
    def validate_slot_interval(cls, v: int | None) -> int | None:
        if v is not None and v not in (15, 30):
            raise ValueError("slot_interval_minutes must be 15 or 30")
        return v


# --- Payment settings ---


class PaymentSettings(BaseModel):
    """Read-only view of master's payment configuration."""

    card_number: str | None = None
    sbp_phone: str | None = None
    bank_name: str | None = None
    has_robokassa: bool = False  # computed: True if merchant_login is set
    robokassa_is_test: bool = False
    robokassa_hash_algorithm: str = "sha256"
    fiscalization_level: str = "none"  # none, manual, auto
    has_seen_grey_warning: bool = False
    receipt_sno: str = "patent"

    model_config = {"from_attributes": True}


class PaymentSettingsUpdate(BaseModel):
    """Update master's payment requisites and fiscalization settings."""

    card_number: str | None = None
    sbp_phone: str | None = None
    bank_name: str | None = None
    fiscalization_level: Literal["none", "manual", "auto"] | None = None
    receipt_sno: str | None = None
    has_seen_grey_warning: bool | None = None


# --- Notification settings ---


class NotificationSettings(BaseModel):
    """Read-only view of master's notification configuration."""

    reminders_enabled: bool
    reminder_1_hours: int
    reminder_2_hours: int | None
    address_note: str | None

    model_config = {"from_attributes": True}


class NotificationSettingsUpdate(BaseModel):
    """Update master's notification preferences."""

    reminders_enabled: bool | None = None
    reminder_1_hours: int | None = None
    reminder_2_hours: int | None = Field(default=None)
    address_note: str | None = None

    @field_validator("reminder_1_hours")
    @classmethod
    def validate_reminder_1(cls, v: int | None) -> int | None:
        if v is not None and v not in (1, 2, 6, 12, 24):
            raise ValueError("Interval must be 1, 2, 6, 12, or 24 hours")
        return v

    @field_validator("reminder_2_hours")
    @classmethod
    def validate_reminder_2(cls, v: int | None) -> int | None:
        if v is not None and v not in (1, 2, 6, 12, 24):
            raise ValueError("Interval must be 1, 2, 6, 12, or 24 hours")
        return v


# --- Robokassa ---


class RobokassaSetup(BaseModel):
    """Connect Robokassa credentials."""

    merchant_login: str = Field(min_length=1)
    password1: str = Field(min_length=1)
    password2: str = Field(min_length=1)
    is_test: bool = False
    hash_algorithm: str = Field(
        default="sha256", pattern=r"^(md5|sha256|sha512)$"
    )


class RobokassaDisconnect(BaseModel):
    """Confirmation model for disconnecting Robokassa (empty body)."""

    pass
