"""
ml_service.py
Loads trained model + pipeline at startup; exposes predict().
"""

import json
import os
import joblib
import numpy as np
import pandas as pd

# Path to ML artifacts (relative to where uvicorn is launched, i.e. backend/)
ARTIFACT_DIR = os.path.join(os.path.dirname(__file__), "..", "ml", "artifacts")

_model    = None
_pipeline = None
_features = None
_metrics  = None
_fi       = None
MODEL_VERSION = "v1"


def load_artifacts():
    global _model, _pipeline, _features, _metrics, _fi
    _model    = joblib.load(f"{ARTIFACT_DIR}/model.pkl")
    _pipeline = joblib.load(f"{ARTIFACT_DIR}/pipeline.pkl")
    with open(f"{ARTIFACT_DIR}/features.json") as f:
        _features = json.load(f)
    with open(f"{ARTIFACT_DIR}/metrics.json") as f:
        _metrics = json.load(f)
    with open(f"{ARTIFACT_DIR}/feature_importance.json") as f:
        _fi = json.load(f)
    print(f"[ML] Loaded model: {_metrics['model']}  test_MAE={_metrics['test_mae']}")


def _grade_band(sgpa: float) -> str:
    if sgpa >= 8.5:
        return "A"
    if sgpa >= 7.0:
        return "B"
    if sgpa >= 5.5:
        return "C"
    if sgpa >= 4.0:
        return "D"
    return "F"


def predict(features: dict) -> dict:
    """
    features: dict with keys matching FEATURES list.
    Returns: { predicted_sgpa, grade_band, model_version }
    """
    row = pd.DataFrame([{f: features[f] for f in _features}])
    row_t = _pipeline.transform(row)
    sgpa = float(_model.predict(row_t)[0])
    sgpa = round(max(0.0, min(10.0, sgpa)), 2)
    return {
        "predicted_sgpa":  sgpa,
        "grade_band":       _grade_band(sgpa),
        "model_version":    MODEL_VERSION,
    }


def get_metrics() -> dict:
    return _metrics


def get_feature_importance() -> dict:
    return _fi
