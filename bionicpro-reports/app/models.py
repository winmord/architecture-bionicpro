from pydantic import BaseModel
from typing import Optional
from datetime import date


class ReportResponse(BaseModel):
    user_email: str
    user_name: str
    total_sessions: int
    total_gestures: int
    avg_confidence: float
    avg_battery: float
    first_activity: Optional[date]
    last_activity: Optional[date]
    updated_at: date


class ErrorResponse(BaseModel):
    error: str
    detail: Optional[str] = None