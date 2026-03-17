import uuid
from datetime import date, datetime, time

from pydantic import BaseModel, Field, model_validator


class ScheduleDayEntry(BaseModel):
    day_of_week: int = Field(ge=0, le=6)
    start_time: time
    end_time: time
    break_start: time | None = None
    break_end: time | None = None
    is_working: bool = True


class ScheduleTemplate(BaseModel):
    days: list[ScheduleDayEntry]

    @model_validator(mode="after")
    def validate_seven_unique_days(self) -> "ScheduleTemplate":
        if len(self.days) != 7:
            raise ValueError("Schedule must contain exactly 7 day entries")
        day_values = [d.day_of_week for d in self.days]
        if len(set(day_values)) != 7:
            raise ValueError("Each day_of_week must be unique (0-6)")
        return self


class ScheduleExceptionCreate(BaseModel):
    exception_date: date
    is_day_off: bool = True
    start_time: time | None = None
    end_time: time | None = None
    reason: str | None = None


class ScheduleExceptionRead(BaseModel):
    id: uuid.UUID
    exception_date: date
    is_day_off: bool
    start_time: time | None
    end_time: time | None
    reason: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class ScheduleDayRead(BaseModel):
    day_of_week: int
    start_time: time
    end_time: time
    break_start: time | None
    break_end: time | None
    is_working: bool

    model_config = {"from_attributes": True}
