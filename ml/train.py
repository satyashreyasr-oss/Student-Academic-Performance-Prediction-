"""
train.py
Trains, evaluates, and saves the best regression model + preprocessing pipeline.

Usage:
    python train.py

Outputs (saved to ml/artifacts/):
    model.pkl       – best trained model
    pipeline.pkl    – fitted sklearn preprocessing pipeline
    metrics.json    – evaluation metrics on held-out test set
    feature_importance.json
"""

import json
import os
import joblib
import numpy as np
import pandas as pd

from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import StandardScaler, OrdinalEncoder
from sklearn.impute import SimpleImputer
from sklearn.linear_model import Ridge
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

# ── Config ────────────────────────────────────────────────────────────────────
DATA_PATH      = os.path.join(os.path.dirname(__file__), "..", "DATA", "students.csv")
ARTIFACTS_DIR  = "artifacts"
TARGET         = "SGPA"

FEATURES = [
    "Age",
    "Gender",
    "Study_Hours_per_Day",
    "Sleep_Hours",
    "Attendance_%",
    "Assignments_Completed_%",
    "Avg_Internal_Score",
    "Stress_Level_(1-10)",
    "Social_Media_Hours",
]

os.makedirs(ARTIFACTS_DIR, exist_ok=True)

# ── Load data ─────────────────────────────────────────────────────────────────
df = pd.read_csv(DATA_PATH)
# Only use rows that have a valid SGPA for training
df = df[df[TARGET].notna() & (df[TARGET].astype(str).str.strip() != "")]
df[TARGET] = df[TARGET].astype(float)
print(f"Rows with SGPA (usable for training): {len(df)}")
X = df[FEATURES]
y = df[TARGET]

X_train, X_temp, y_train, y_temp = train_test_split(X, y, test_size=0.30, random_state=42)
X_val,   X_test, y_val,   y_test = train_test_split(X_temp, y_temp, test_size=0.50, random_state=42)

print(f"Train: {len(X_train)}  Val: {len(X_val)}  Test: {len(X_test)}")

# ── Preprocessing pipeline ────────────────────────────────────────────────────
# Gender is categorical; all others are numeric
cat_features = ["Gender"]
num_features = [f for f in FEATURES if f not in cat_features]

preprocess = ColumnTransformer([
    ("num", Pipeline([
        ("imputer", SimpleImputer(strategy="median")),
        ("scaler",  StandardScaler()),
    ]), num_features),
    ("cat", Pipeline([
        ("imputer", SimpleImputer(strategy="most_frequent")),
        ("encoder", OrdinalEncoder(handle_unknown="use_encoded_value", unknown_value=-1)),
    ]), cat_features),
])

X_train_t = preprocess.fit_transform(X_train)
X_val_t   = preprocess.transform(X_val)
X_test_t  = preprocess.transform(X_test)

# ── Candidate models ──────────────────────────────────────────────────────────
candidates = {
    "Ridge":            Ridge(alpha=10),
    "RandomForest":     RandomForestRegressor(n_estimators=200, random_state=42, n_jobs=-1),
    "GradientBoosting": GradientBoostingRegressor(n_estimators=200, learning_rate=0.05, random_state=42),
}

best_name, best_model, best_val_mae = None, None, float("inf")

for name, model in candidates.items():
    model.fit(X_train_t, y_train)
    preds = model.predict(X_val_t)
    mae   = mean_absolute_error(y_val, preds)
    rmse  = mean_squared_error(y_val, preds) ** 0.5
    r2    = r2_score(y_val, preds)
    print(f"  {name:25s}  MAE={mae:.3f}  RMSE={rmse:.3f}  R²={r2:.4f}")
    if mae < best_val_mae:
        best_val_mae = mae
        best_name    = name
        best_model   = model

print(f"\nBest model: {best_name}  (val MAE={best_val_mae:.3f})")

# ── Final evaluation on held-out test set ─────────────────────────────────────
test_preds = best_model.predict(X_test_t)
mae  = mean_absolute_error(y_test, test_preds)
rmse = mean_squared_error(y_test, test_preds) ** 0.5
r2   = r2_score(y_test, test_preds)

# % predictions within ±0.5 SGPA
within_5 = float(np.mean(np.abs(test_preds - y_test) <= 0.5) * 100)

metrics = {
    "model":       best_name,
    "test_mae":    round(mae, 4),
    "test_rmse":   round(rmse, 4),
    "test_r2":     round(r2, 4),
    "within_5pct": round(within_5, 2),
    "n_test":      len(y_test),
}
print("\nTest metrics:", json.dumps(metrics, indent=2))

# ── Feature importance ────────────────────────────────────────────────────────
fi = {}
if hasattr(best_model, "feature_importances_"):
    importances = best_model.feature_importances_
    fi = dict(zip(FEATURES, [round(float(v), 6) for v in importances]))
    fi = dict(sorted(fi.items(), key=lambda x: x[1], reverse=True))

# ── Save artifacts ────────────────────────────────────────────────────────────
joblib.dump(best_model,  f"{ARTIFACTS_DIR}/model.pkl")
joblib.dump(preprocess,  f"{ARTIFACTS_DIR}/pipeline.pkl")

with open(f"{ARTIFACTS_DIR}/metrics.json", "w") as f:
    json.dump(metrics, f, indent=2)

with open(f"{ARTIFACTS_DIR}/feature_importance.json", "w") as f:
    json.dump(fi, f, indent=2)

with open(f"{ARTIFACTS_DIR}/features.json", "w") as f:
    json.dump(FEATURES, f)

print(f"\nArtifacts saved to ./{ARTIFACTS_DIR}/")
