from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


# ── Student ───────────────────────────────────────────────────────────────────

class StudentCreate(BaseModel):
    student_id: str
    name: str
    section: Optional[str] = None


class StudentOut(StudentCreate):
    id: int
    class Config:
        from_attributes = True


# ── Record (features) ─────────────────────────────────────────────────────────

class RecordIn(BaseModel):
    student_id: str
    age:                    float = Field(..., ge=15, le=60)
    gender:                 str
    study_hours_per_day:    float = Field(..., ge=0, le=24)
    sleep_hours:            float = Field(..., ge=0, le=24)
    attendance:             float = Field(..., ge=0, le=100)
    assignments_completed:  float = Field(..., ge=0, le=100)
    internal_score:         float = Field(..., ge=0, le=50)
    stress_level:           float = Field(..., ge=1, le=10)
    social_media_hours:     float = Field(..., ge=0, le=24)


class RecordOut(RecordIn):
    id: int
    created_at: datetime
    class Config:
        from_attributes = True


# ── Prediction ────────────────────────────────────────────────────────────────

class PredictRequest(BaseModel):
    student_id: Optional[str] = None      # optional; if given, saves to DB
    age:                    float = Field(..., ge=15, le=60)
    gender:                 str
    study_hours_per_day:    float = Field(..., ge=0, le=24)
    sleep_hours:            float = Field(..., ge=0, le=24)
    attendance:             float = Field(..., ge=0, le=100)
    assignments_completed:  float = Field(..., ge=0, le=100)
    internal_score:         float = Field(..., ge=0, le=50)
    stress_level:           float = Field(..., ge=1, le=10)
    social_media_hours:     float = Field(..., ge=0, le=24)


class PredictResponse(BaseModel):
    student_id:     Optional[str]
    predicted_sgpa:  float
    grade_band:      str
    model_version:   str


# ── Actual result ─────────────────────────────────────────────────────────────

class ActualIn(BaseModel):
    student_id:  str
    actual_sgpa: float = Field(..., ge=0, le=10)


class ActualOut(ActualIn):
    id: int
    result_date: datetime
    class Config:
        from_attributes = True


# ── Metrics ───────────────────────────────────────────────────────────────────

class MetricsOut(BaseModel):
    n_compared:    int
    mae:           float
    rmse:          float
    r2:            float
    within_0_5:    float       # % within ±0.5 SGPA
    model_mae:     float       # from training metrics.json
    model_rmse:    float
    model_r2:      float
