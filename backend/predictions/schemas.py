"""
Pydantic request-payload validation. DRF ModelSerializers handle the output
side (serializing StudentPrediction rows to JSON); these schemas handle the
input side for POST endpoints, independent of the Django model layer.
"""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field, field_validator

FEATURE_BOUNDS = {
    "attendance_rate": (0, 100),
    "midterm_1": (0, 100),
    "midterm_2": (0, 100),
    "assignments_avg": (0, 100),
    "study_hours_weekly": (0, 30),
}


class PredictRequestSchema(BaseModel):
    student_id: Optional[str] = Field(default=None, max_length=32)
    attendance_rate: float = Field(ge=0, le=100)
    midterm_1: float = Field(ge=0, le=100)
    midterm_2: float = Field(ge=0, le=100)
    assignments_avg: float = Field(ge=0, le=100)
    study_hours_weekly: float = Field(ge=0, le=30)

    @field_validator("student_id")
    @classmethod
    def strip_student_id(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        v = v.strip()
        return v or None


class RetrainRequestSchema(BaseModel):
    """Optional body for POST /api/retrain. An empty/absent body just
    retrains on the existing dataset.csv (the common case)."""

    force_regenerate: bool = False
    rows: Optional[int] = Field(default=None, ge=100, le=50000)
