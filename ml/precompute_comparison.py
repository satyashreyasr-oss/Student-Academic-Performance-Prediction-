"""
Run once locally to generate DATA/comparison.csv.
Streamlit reads this file instead of running predictions at startup.

Usage:  python ml/precompute_comparison.py
"""

import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

ARTIFACT_DIR = Path("ml/artifacts")
DATA_PATH    = Path("DATA/students.csv")
OUT_PATH     = Path("DATA/comparison.csv")

FEATURES = [
    "Age", "Gender", "Study_Hours_per_Day", "Sleep_Hours",
    "Attendance_%", "Assignments_Completed_%", "Avg_Internal_Score",
    "Stress_Level_(1-10)", "Social_Media_Hours",
]

def grade_band(sgpa):
    if sgpa >= 8.5: return "A"
    if sgpa >= 7.0: return "B"
    if sgpa >= 5.5: return "C"
    if sgpa >= 4.0: return "D"
    return "F"

def main():
    model    = joblib.load(ARTIFACT_DIR / "model.pkl")
    pipeline = joblib.load(ARTIFACT_DIR / "pipeline.pkl")

    df = pd.read_csv(DATA_PATH)
    df.set_index("student_id", inplace=True)

    transformed = pipeline.transform(df[FEATURES])
    preds       = np.clip(model.predict(transformed), 0.0, 10.0).round(2)

    cdf = pd.DataFrame({
        "student_id":       df.index,
        "actual":           df["SGPA"].values,
        "predicted":        preds,
    })
    cdf["error"]           = (cdf["actual"] - cdf["predicted"]).round(2)
    cdf["abs_error"]       = cdf["error"].abs().round(2)
    cdf["actual_grade"]    = cdf["actual"].apply(grade_band)
    cdf["predicted_grade"] = cdf["predicted"].apply(grade_band)
    cdf["grade_match"]     = cdf["actual_grade"] == cdf["predicted_grade"]

    cdf.to_csv(OUT_PATH, index=False)
    print(f"Saved {len(cdf)} rows to {OUT_PATH}")

if __name__ == "__main__":
    main()
