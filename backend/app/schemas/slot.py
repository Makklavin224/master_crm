from datetime import date, time

from pydantic import BaseModel


class AvailableSlot(BaseModel):
    time: time


class AvailableSlotsResponse(BaseModel):
    date: date
    slots: list[AvailableSlot]
