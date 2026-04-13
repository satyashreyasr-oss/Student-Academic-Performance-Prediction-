"""
main.py  –  FastAPI backend for Student Performance Predictor

Start:  uvicorn main:app --reload --port 8000
Docs:   http://localhost:8000/docs
"""

import math
import os
import pandas as pd
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

import models, schemas, ml_service
from database import engine, get_db

# ── Load CSV dataset once at module level ─────────────────────────────────────
CSV_PATH = os.path.join(os.path.dirname(__file__), "..", "DATA", "students.csv")
_csv_df = pd.read_csv(CSV_PATH)
_csv_df.set_index("student_id", inplace=True)

# ── Startup ───────────────────────────────────────────────────────────────────
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Student Performance Predictor API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],          # tighten in production
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup():
    ml_service.load_artifacts()


# ── Students ──────────────────────────────────────────────────────────────────

@app.post("/students", response_model=schemas.StudentOut, tags=["Students"])
def create_student(student: schemas.StudentCreate, db: Session = Depends(get_db)):
    existing = db.query(models.Student).filter_by(student_id=student.student_id).first()
    if existing:
        raise HTTPException(400, "student_id already exists")
    obj = models.Student(**student.model_dump())
    db.add(obj); db.commit(); db.refresh(obj)
    return obj


@app.get("/students", response_model=list[schemas.StudentOut], tags=["Students"])
def list_students(db: Session = Depends(get_db)):
    return db.query(models.Student).all()


@app.get("/students/{student_id}", response_model=schemas.StudentOut, tags=["Students"])
def get_student(student_id: str, db: Session = Depends(get_db)):
    obj = db.query(models.Student).filter_by(student_id=student_id).first()
    if not obj:
        raise HTTPException(404, "Student not found")
    return obj


# ── Records ───────────────────────────────────────────────────────────────────

@app.post("/records", response_model=schemas.RecordOut, tags=["Records"])
def save_record(rec: schemas.RecordIn, db: Session = Depends(get_db)):
    obj = models.StudentRecord(**rec.model_dump())
    db.add(obj); db.commit(); db.refresh(obj)
    return obj


@app.get("/records/{student_id}", response_model=list[schemas.RecordOut], tags=["Records"])
def get_records(student_id: str, db: Session = Depends(get_db)):
    return db.query(models.StudentRecord).filter_by(student_id=student_id).all()


# ── Predict ───────────────────────────────────────────────────────────────────

FEATURE_KEYS = [
    "Age", "Gender", "Study_Hours_per_Day", "Sleep_Hours",
    "Attendance_%", "Assignments_Completed_%", "Avg_Internal_Score",
    "Stress_Level_(1-10)", "Social_Media_Hours",
]

# Maps API field names (snake_case) to model feature names (from CSV)
API_TO_MODEL = {
    "age":                   "Age",
    "gender":                "Gender",
    "study_hours_per_day":   "Study_Hours_per_Day",
    "sleep_hours":           "Sleep_Hours",
    "attendance":            "Attendance_%",
    "assignments_completed": "Assignments_Completed_%",
    "internal_score":        "Avg_Internal_Score",
    "stress_level":          "Stress_Level_(1-10)",
    "social_media_hours":    "Social_Media_Hours",
}

# Reverse mapping: CSV column names → API field names
CSV_TO_API = {v: k for k, v in API_TO_MODEL.items()}


# ── CSV Dataset Lookup ────────────────────────────────────────────────────────

@app.get("/csv-students", tags=["CSV Data"])
def list_csv_students():
    """Return all student IDs from the training CSV."""
    return list(_csv_df.index)


@app.get("/csv-students/{student_id}", tags=["CSV Data"])
def get_csv_student(student_id: str):
    """Lookup a student's features + actual SGPA from the training CSV."""
    if student_id not in _csv_df.index:
        raise HTTPException(404, f"Student {student_id} not found in dataset")
    row = _csv_df.loc[student_id]
    result = {"student_id": student_id}
    for csv_col, api_key in CSV_TO_API.items():
        val = row[csv_col]
        result[api_key] = val if isinstance(val, str) else float(val)
    sgpa_val = row.get("SGPA", "")
    result["actual_sgpa"] = float(sgpa_val) if str(sgpa_val).strip() not in ("", "nan") else None
    return result


@app.post("/predict", response_model=schemas.PredictResponse, tags=["ML"])
def predict(req: schemas.PredictRequest, db: Session = Depends(get_db)):
    features = {model_key: getattr(req, api_key) for api_key, model_key in API_TO_MODEL.items()}
    result   = ml_service.predict(features)

    # Persist prediction if student_id given
    if req.student_id:
        # Auto-create student if not already in DB
        existing_student = db.query(models.Student).filter_by(student_id=req.student_id).first()
        if not existing_student:
            db.add(models.Student(student_id=req.student_id, name=req.student_id))

        pred_obj = models.Prediction(
            student_id     = req.student_id,
            predicted_sgpa = result["predicted_sgpa"],
            model_version  = result["model_version"],
        )
        db.add(pred_obj); db.commit()

    return schemas.PredictResponse(
        student_id     = req.student_id,
        predicted_sgpa = result["predicted_sgpa"],
        grade_band     = result["grade_band"],
        model_version  = result["model_version"],
    )


@app.get("/predictions", tags=["ML"])
def list_predictions(db: Session = Depends(get_db)):
    rows = db.query(models.Prediction).all()
    return [
        {
            "id":             r.id,
            "student_id":     r.student_id,
            "predicted_sgpa": r.predicted_sgpa,
            "model_version":  r.model_version,
            "created_at":     r.created_at,
        }
        for r in rows
    ]


@app.get("/predictions/{student_id}", tags=["ML"])
def get_prediction(student_id: str, db: Session = Depends(get_db)):
    row = (
        db.query(models.Prediction)
        .filter_by(student_id=student_id)
        .order_by(models.Prediction.created_at.desc())
        .first()
    )
    if not row:
        raise HTTPException(404, "No prediction found for this student")
    return row


# ── Actual results ────────────────────────────────────────────────────────────

@app.post("/actuals", response_model=schemas.ActualOut, tags=["Results"])
def save_actual(data: schemas.ActualIn, db: Session = Depends(get_db)):
    existing = db.query(models.ActualResult).filter_by(student_id=data.student_id).first()
    if existing:
        existing.actual_sgpa = data.actual_sgpa
        db.commit(); db.refresh(existing)
        return existing
    obj = models.ActualResult(**data.model_dump())
    db.add(obj); db.commit(); db.refresh(obj)
    return obj


@app.get("/actuals", response_model=list[schemas.ActualOut], tags=["Results"])
def list_actuals(db: Session = Depends(get_db)):
    return db.query(models.ActualResult).all()


# ── Metrics ───────────────────────────────────────────────────────────────────

@app.get("/metrics", response_model=schemas.MetricsOut, tags=["Metrics"])
def get_metrics(db: Session = Depends(get_db)):
    """Compare predictions vs actual results for students that have both."""
    preds   = {p.student_id: p.predicted_sgpa for p in db.query(models.Prediction).all()}
    actuals = {a.student_id: a.actual_sgpa    for a in db.query(models.ActualResult).all()}

    common = [sid for sid in preds if sid in actuals]
    n = len(common)

    if n == 0:
        model_m = ml_service.get_metrics()
        return schemas.MetricsOut(
            n_compared=0, mae=0, rmse=0, r2=0, within_0_5=0,
            model_mae=model_m["test_mae"], model_rmse=model_m["test_rmse"],
            model_r2=model_m["test_r2"],
        )

    errors = [actuals[s] - preds[s] for s in common]
    abs_e  = [abs(e) for e in errors]
    mae    = sum(abs_e) / n
    rmse   = math.sqrt(sum(e**2 for e in errors) / n)

    mean_actual = sum(actuals[s] for s in common) / n
    ss_res = sum((actuals[s] - preds[s])**2 for s in common)
    ss_tot = sum((actuals[s] - mean_actual)**2 for s in common)
    r2     = 1 - ss_res / ss_tot if ss_tot > 0 else 0.0

    within_0_5 = sum(1 for e in abs_e if e <= 0.5) / n * 100

    model_m = ml_service.get_metrics()
    return schemas.MetricsOut(
        n_compared = n,
        mae        = round(mae, 4),
        rmse       = round(rmse, 4),
        r2         = round(r2, 4),
        within_0_5 = round(within_0_5, 2),
        model_mae  = model_m["test_mae"],
        model_rmse = model_m["test_rmse"],
        model_r2   = model_m["test_r2"],
    )


@app.get("/feature-importance", tags=["Metrics"])
def feature_importance():
    return ml_service.get_feature_importance()


@app.get("/comparison", tags=["Metrics"])
def comparison(db: Session = Depends(get_db)):
    """Returns per-student predicted vs actual for scatter plot."""
    preds   = {p.student_id: p.predicted_sgpa for p in db.query(models.Prediction).all()}
    actuals = {a.student_id: a.actual_sgpa    for a in db.query(models.ActualResult).all()}
    students = {s.student_id: s.name for s in db.query(models.Student).all()}

    return [
        {
            "student_id":     sid,
            "name":           students.get(sid, sid),
            "predicted":      preds[sid],
            "actual":         actuals[sid],
            "error":          round(actuals[sid] - preds[sid], 2),
            "abs_error":      round(abs(actuals[sid] - preds[sid]), 2),
        }
        for sid in preds if sid in actuals
    ]
