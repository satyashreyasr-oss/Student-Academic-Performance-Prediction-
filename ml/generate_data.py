"""
generate_data.py
Generates a realistic synthetic dataset of 1000 student records.
Target: SGPA (0–10 scale)
Run once: python generate_data.py
"""

import numpy as np
import pandas as pd

np.random.seed(42)
N = 1000

# ── Features (match train.py expected columns) ──────────────────────────────
age                   = np.clip(np.random.normal(21, 3, N), 17, 35).astype(int).astype(float)
gender                = np.random.choice(["Male", "Female"], N)
study_hours_per_day   = np.clip(np.random.normal(4.5, 1.8, N), 0.5, 12.0)
sleep_hours           = np.clip(np.random.normal(6.8, 1.2, N), 3.0, 10.0)
attendance            = np.clip(np.random.normal(78, 12, N), 30, 100)
assignments_completed = np.clip(np.random.normal(75, 15, N), 20, 100)
internal_score        = np.clip(np.random.normal(32, 8, N), 5, 50)
stress_level          = np.clip(np.random.normal(5.5, 2, N), 1, 10)
social_media_hours    = np.clip(np.random.normal(3, 1.5, N), 0, 8)

# ── Target: SGPA on 0–10 scale ──────────────────────────────────────────────
sgpa = (
    1.5                                     # base offset
    + 0.30 * (internal_score / 5)            # max ~3.0
    + 0.20 * (attendance / 10)              # max ~2.0
    + 0.15 * (assignments_completed / 10)   # max ~1.5
    + 0.10 * study_hours_per_day            # max ~1.2
    + 0.05 * sleep_hours                    # max ~0.5
    - 0.03 * stress_level                   # penalty
    - 0.05 * social_media_hours             # penalty
    + np.random.normal(0, 0.4, N)           # noise
)
sgpa = np.clip(sgpa, 0, 10).round(2)

df = pd.DataFrame({
    "student_id":             [f"S{str(i+1).zfill(4)}" for i in range(N)],
    "Age":                    age,
    "Gender":                 gender,
    "Study_Hours_per_Day":    study_hours_per_day.round(2),
    "Sleep_Hours":            sleep_hours.round(2),
    "Attendance_%":           attendance.round(2),
    "Assignments_Completed_%": assignments_completed.round(2),
    "Avg_Internal_Score":     internal_score.round(2),
    "Stress_Level_(1-10)":    stress_level.round(2),
    "Social_Media_Hours":     social_media_hours.round(2),
    "SGPA":                   sgpa,
})

df.to_csv("data/students.csv", index=False)
print(f"Dataset saved: data/students.csv  ({N} rows)")
print(df.describe().round(2))
