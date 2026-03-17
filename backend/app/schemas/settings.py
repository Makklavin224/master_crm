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
