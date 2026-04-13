"""
compare_all.py
Automatically predicts SGPA for ALL students and saves their actual SGPA,
so the dashboard shows full comparison for every student.

Usage: Make sure backend is running (uvicorn main:app --port 8000), then:
    python compare_all.py
"""

import requests
import pandas as pd
import os
import time

API = "http://localhost:8000"
CSV_PATH = os.path.join(os.path.dirname(__file__), "DATA", "students.csv")

df = pd.read_csv(CSV_PATH)
print(f"Total students in CSV: {len(df)}")

# Only process students that have a valid SGPA
df = df[df["SGPA"].notna() & (df["SGPA"].astype(str).str.strip() != "")]
print(f"Students with SGPA: {len(df)}")

success = 0
errors = 0

for i, row in df.iterrows():
    sid = row["Student_ID"]

    # Step 1: Predict
    payload = {
        "student_id": sid,
        "age": float(row["Age"]),
        "gender": row["Gender"],
        "study_hours_per_day": float(row["Study_Hours_per_Day"]),
        "sleep_hours": float(row["Sleep_Hours"]),
        "attendance": float(row["Attendance_%"]),
        "assignments_completed": float(row["Assignments_Completed_%"]),
        "midterm_score": float(row["Midterm_Score"]),
        "stress_level": float(row["Stress_Level_(1-10)"]),
        "social_media_hours": float(row["Social_Media_Hours"]),
    }

    try:
        r1 = requests.post(f"{API}/predict", json=payload)
        r1.raise_for_status()
        predicted = r1.json()["predicted_sgpa"]

        # Step 2: Save actual SGPA
        r2 = requests.post(f"{API}/actuals", json={
            "student_id": sid,
            "actual_sgpa": float(row["SGPA"]),
        })
        r2.raise_for_status()

        success += 1
        if success % 25 == 0:
            print(f"  Processed {success} students...")

    except Exception as e:
        errors += 1
        if errors <= 5:
            print(f"  Error for {sid}: {e}")

print(f"\nDone! {success} students compared, {errors} errors.")
print("Refresh the Dashboard in your browser to see all comparisons.")
