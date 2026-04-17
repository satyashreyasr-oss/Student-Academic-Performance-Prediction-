"""
Student Performance Predictor — Streamlit App
Deploy: https://share.streamlit.io
"""

import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# ── Config ────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Student Performance Predictor",
    page_icon="🎓",
    layout="wide",
)

ARTIFACT_DIR = Path("ml/artifacts")
DATA_PATH    = Path("DATA/students.csv")

# Column order the pipeline expects
FEATURES = [
    "Age", "Gender", "Study_Hours_per_Day", "Sleep_Hours",
    "Attendance_%", "Assignments_Completed_%", "Avg_Internal_Score",
    "Stress_Level_(1-10)", "Social_Media_Hours",
]

FRIENDLY = {
    "Age":                    "Age",
    "Gender":                 "Gender",
    "Study_Hours_per_Day":    "Study Hours / Day",
    "Sleep_Hours":            "Sleep Hours",
    "Attendance_%":           "Attendance (%)",
    "Assignments_Completed_%":"Assignments Completed (%)",
    "Avg_Internal_Score":     "Avg Internal Score",
    "Stress_Level_(1-10)":    "Stress Level (1–10)",
    "Social_Media_Hours":     "Social Media Hours / Day",
}

GRADE_COLOR = {"A": "🟢", "B": "🔵", "C": "🟡", "D": "🟠", "F": "🔴"}


# ── Loaders ───────────────────────────────────────────────────────────────────
@st.cache_resource(show_spinner="Loading model…")
def load_artifacts():
    model    = joblib.load(ARTIFACT_DIR / "model.pkl")
    pipeline = joblib.load(ARTIFACT_DIR / "pipeline.pkl")
    with open(ARTIFACT_DIR / "metrics.json")          as f: metrics = json.load(f)
    with open(ARTIFACT_DIR / "feature_importance.json") as f: fi     = json.load(f)
    return model, pipeline, metrics, fi


@st.cache_data(show_spinner=False)
def load_csv() -> pd.DataFrame:
    df = pd.read_csv(DATA_PATH)
    df.set_index("student_id", inplace=True)
    return df


# ── Helpers ───────────────────────────────────────────────────────────────────
def grade_band(sgpa: float) -> str:
    if sgpa >= 8.5: return "A"
    if sgpa >= 7.0: return "B"
    if sgpa >= 5.5: return "C"
    if sgpa >= 4.0: return "D"
    return "F"


def run_predict(model, pipeline, inputs: dict) -> float:
    row  = pd.DataFrame([inputs])[FEATURES]
    rowt = pipeline.transform(row)
    sgpa = float(model.predict(rowt)[0])
    return round(max(0.0, min(10.0, sgpa)), 2)


# ── Session state ─────────────────────────────────────────────────────────────
if "history" not in st.session_state:
    st.session_state.history = []   # list of {student_id, predicted, actual}


# ── Load everything ───────────────────────────────────────────────────────────
model, pipeline, metrics, fi = load_artifacts()
df = load_csv()

# ── Header ────────────────────────────────────────────────────────────────────
st.title("🎓 Student Performance Predictor")
st.caption("Predict SGPA (0–10) from academic & lifestyle features · RandomForest model")
st.divider()

# ── Tabs ──────────────────────────────────────────────────────────────────────
tab_predict, tab_dashboard, tab_compare = st.tabs(["🔮 Predict", "📊 Dashboard", "📋 Comparison"])


# ════════════════════════════════════════════════════════════════════════════
# TAB 1 — PREDICT
# ════════════════════════════════════════════════════════════════════════════
with tab_predict:
    st.subheader("Enter student details")

    # ── Load from dataset ──────────────────────────────────────────────────
    with st.expander("📂 Auto-fill from dataset (optional)"):
        selected_id = st.selectbox("Select student ID", ["— manual entry —"] + list(df.index))
        auto_actual = None
        if selected_id != "— manual entry —":
            row_data   = df.loc[selected_id]
            auto_actual = float(row_data["SGPA"]) if str(row_data.get("SGPA", "")).strip() not in ("", "nan") else None
            st.info(f"Loaded **{selected_id}** · Actual SGPA: **{auto_actual if auto_actual else 'N/A'}**")
        else:
            row_data = None

    def _val(col, default):
        if row_data is not None:
            v = row_data.get(col, default)
            return v if not (isinstance(v, float) and np.isnan(v)) else default
        return default

    # ── Input form ────────────────────────────────────────────────────────
    with st.form("predict_form"):
        c1, c2, c3 = st.columns(3)

        with c1:
            age            = st.number_input("Age",              min_value=15, max_value=40,  value=int(_val("Age", 20)))
            gender         = st.selectbox(  "Gender",            ["Male", "Female"],           index=0 if str(_val("Gender","Male")) == "Male" else 1)
            study_hours    = st.number_input("Study Hours / Day", min_value=0.0, max_value=16.0, step=0.1, value=float(_val("Study_Hours_per_Day", 4.0)))

        with c2:
            sleep_hours    = st.number_input("Sleep Hours",        min_value=2.0, max_value=12.0, step=0.1, value=float(_val("Sleep_Hours", 7.0)))
            attendance     = st.number_input("Attendance (%)",     min_value=0.0, max_value=100.0, step=0.1, value=float(_val("Attendance_%", 80.0)))
            assignments    = st.number_input("Assignments Completed (%)", min_value=0.0, max_value=100.0, step=0.1, value=float(_val("Assignments_Completed_%", 80.0)))

        with c3:
            internal_score = st.number_input("Avg Internal Score", min_value=0.0, max_value=100.0, step=0.1, value=float(_val("Avg_Internal_Score", 35.0)))
            stress         = st.number_input("Stress Level (1–10)", min_value=1, max_value=10, value=int(_val("Stress_Level_(1-10)", 5)))
            social_media   = st.number_input("Social Media Hours / Day", min_value=0.0, max_value=12.0, step=0.1, value=float(_val("Social_Media_Hours", 2.0)))

        actual_input = st.number_input(
            "Actual SGPA (optional — for comparison)",
            min_value=0.0, max_value=10.0, step=0.01,
            value=float(auto_actual) if auto_actual else 0.0,
        )
        submitted = st.form_submit_button("🔮 Predict SGPA", use_container_width=True, type="primary")

    # ── Result ─────────────────────────────────────────────────────────────
    if submitted:
        inputs = {
            "Age":                    age,
            "Gender":                 gender,
            "Study_Hours_per_Day":    study_hours,
            "Sleep_Hours":            sleep_hours,
            "Attendance_%":           attendance,
            "Assignments_Completed_%": assignments,
            "Avg_Internal_Score":     internal_score,
            "Stress_Level_(1-10)":    stress,
            "Social_Media_Hours":     social_media,
        }
        predicted = run_predict(model, pipeline, inputs)
        band      = grade_band(predicted)
        icon      = GRADE_COLOR[band]

        st.divider()
        r1, r2, r3 = st.columns(3)
        r1.metric("Predicted SGPA", f"{predicted:.2f} / 10")
        r2.metric("Grade Band", f"{icon} {band}")
        if actual_input > 0:
            error = round(actual_input - predicted, 2)
            r3.metric("Actual SGPA", f"{actual_input:.2f}", delta=f"{error:+.2f} error")

        # Save to session history
        sid = selected_id if selected_id != "— manual entry —" else f"Manual-{len(st.session_state.history)+1}"
        st.session_state.history.append({
            "student_id": sid,
            "predicted":  predicted,
            "actual":     actual_input if actual_input > 0 else None,
        })
        st.success(f"Prediction saved to Comparison tab  ·  student: **{sid}**")


# ════════════════════════════════════════════════════════════════════════════
# TAB 2 — DASHBOARD
# ════════════════════════════════════════════════════════════════════════════
with tab_dashboard:
    st.subheader("Model Performance")

    # ── Metric cards ──────────────────────────────────────────────────────
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Test MAE",    f"{metrics['test_mae']:.4f}")
    m2.metric("Test RMSE",   f"{metrics['test_rmse']:.4f}")
    m3.metric("Test R²",     f"{metrics['test_r2']:.4f}")
    m4.metric("Within ±5%",  f"{metrics['within_5pct']:.1f}%")

    st.caption(f"Model: **{metrics['model']}**  ·  Test set size: **{metrics['n_test']}** students")
    st.divider()

    # ── Feature importance ────────────────────────────────────────────────
    st.subheader("Feature Importance")
    fi_df = (
        pd.DataFrame(list(fi.items()), columns=["Feature", "Importance"])
        .sort_values("Importance", ascending=True)
    )
    fi_df["Feature"] = fi_df["Feature"].map(lambda x: FRIENDLY.get(x, x))

    fig_fi = px.bar(
        fi_df, x="Importance", y="Feature", orientation="h",
        color="Importance", color_continuous_scale="Blues",
        title="Feature Importance (RandomForest)",
        labels={"Importance": "Importance Score"},
    )
    fig_fi.update_layout(coloraxis_showscale=False, height=400)
    st.plotly_chart(fig_fi, use_container_width=True)

    # ── SGPA distribution from dataset ────────────────────────────────────
    st.divider()
    st.subheader("SGPA Distribution in Dataset")
    fig_hist = px.histogram(
        df.reset_index(), x="SGPA", nbins=30,
        color_discrete_sequence=["#4F8BF9"],
        title="Distribution of Actual SGPA (training data)",
    )
    fig_hist.update_layout(height=350)
    st.plotly_chart(fig_hist, use_container_width=True)


# ════════════════════════════════════════════════════════════════════════════
# TAB 3 — COMPARISON
# ════════════════════════════════════════════════════════════════════════════
with tab_compare:
    st.subheader("Predicted vs Actual — This Session")

    history = st.session_state.history
    has_actuals = any(h["actual"] is not None for h in history)

    if not history:
        st.info("No predictions yet. Go to the **Predict** tab to get started.")
    else:
        hist_df = pd.DataFrame(history)
        hist_df["error"]     = hist_df.apply(lambda r: round(r["actual"] - r["predicted"], 2) if r["actual"] else None, axis=1)
        hist_df["abs_error"] = hist_df["error"].abs()

        # ── Summary metrics ───────────────────────────────────────────────
        if has_actuals:
            valid = hist_df.dropna(subset=["actual"])
            n = len(valid)
            mae  = valid["abs_error"].mean()
            rmse = np.sqrt((valid["error"]**2).mean())
            within = (valid["abs_error"] <= 0.5).sum() / n * 100

            s1, s2, s3, s4 = st.columns(4)
            s1.metric("Students Compared", n)
            s2.metric("Session MAE",  f"{mae:.3f}")
            s3.metric("Session RMSE", f"{rmse:.3f}")
            s4.metric("Within ±0.5 SGPA", f"{within:.1f}%")
            st.divider()

            # ── Scatter: predicted vs actual ──────────────────────────────
            fig_scatter = px.scatter(
                valid, x="actual", y="predicted",
                hover_data=["student_id", "error"],
                color="abs_error", color_continuous_scale="RdYlGn_r",
                title="Predicted vs Actual SGPA",
                labels={"actual": "Actual SGPA", "predicted": "Predicted SGPA"},
            )
            # Perfect prediction line
            mn, mx = valid[["actual","predicted"]].min().min(), valid[["actual","predicted"]].max().max()
            fig_scatter.add_trace(go.Scatter(
                x=[mn, mx], y=[mn, mx],
                mode="lines", line=dict(dash="dash", color="grey"),
                name="Perfect prediction",
            ))
            st.plotly_chart(fig_scatter, use_container_width=True)

        # ── Table ─────────────────────────────────────────────────────────
        st.subheader("All Predictions This Session")
        display_df = hist_df.rename(columns={
            "student_id": "Student", "predicted": "Predicted SGPA",
            "actual": "Actual SGPA", "error": "Error", "abs_error": "Abs Error",
        })
        st.dataframe(display_df, use_container_width=True, hide_index=True)

        if st.button("🗑️ Clear session history"):
            st.session_state.history = []
            st.rerun()
