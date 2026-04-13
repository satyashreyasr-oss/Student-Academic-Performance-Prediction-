import React, { useState, useEffect } from "react";
import { predict, listCSVStudents, getCSVStudent } from "../api";

const NUM_FIELDS = [
  { key: "age",                   label: "Age",                       min: 15, max: 60,  step: 1   },
  { key: "study_hours_per_day",   label: "Study Hours",               min: 0,  max: 24,  step: 0.1 },
  { key: "sleep_hours",           label: "Sleep Hours",               min: 0,  max: 24,  step: 0.1 },
  { key: "attendance",            label: "Attendance (%)",            min: 0,  max: 100, step: 0.1 },
  { key: "assignments_completed", label: "Assignments Completed (%)", min: 0,  max: 100, step: 0.1 },
  { key: "internal_score",        label: "Avg Internal Score (out of 50)", min: 0, max: 50, step: 0.1 },
  { key: "stress_level",          label: "Stress Level (1–10)",       min: 1,  max: 10,  step: 0.1 },
  { key: "social_media_hours",    label: "Social Media Hours",        min: 0,  max: 24,  step: 0.1 },
];

const EMPTY = {
  age: "", gender: "Male", study_hours_per_day: "",
  sleep_hours: "", attendance: "", assignments_completed: "",
  internal_score: "", stress_level: "", social_media_hours: "",
};

export default function PredictPage() {
  const [studentIds, setStudentIds] = useState([]);
  const [sid,        setSid]        = useState("");
  const [form,       setForm]       = useState(EMPTY);
  const [actualCgpa, setActualCgpa] = useState(null);
  const [result,     setResult]     = useState(null);
  const [error,      setError]      = useState("");
  const [loading,    setLoading]    = useState(false);
  const [loadingData,setLoadingData]= useState(false);

  // Load all student IDs on mount
  useEffect(() => {
    listCSVStudents()
      .then(r => setStudentIds(r.data))
      .catch(() => {});
  }, []);

  // When student selected, auto-fill form
  const loadStudent = async (selectedId) => {
    setSid(selectedId);
    setResult(null); setError(""); setActualCgpa(null);
    if (!selectedId) { setForm(EMPTY); return; }
    setLoadingData(true);
    try {
      const { data } = await getCSVStudent(selectedId);
      setForm({
        age:                   data.age,
        gender:                data.gender,
        study_hours_per_day:   data.study_hours_per_day,
        sleep_hours:           data.sleep_hours,
        attendance:            data.attendance,
        assignments_completed: data.assignments_completed,
        internal_score:        data.internal_score,
        stress_level:          data.stress_level,
        social_media_hours:    data.social_media_hours,
      });
      setActualCgpa(data.actual_sgpa);
    } catch {
      setError("Student not found in dataset");
    } finally {
      setLoadingData(false);
    }
  };

  const handle = (key, val) => setForm(f => ({ ...f, [key]: parseFloat(val) }));

  const submit = async (e) => {
    e.preventDefault();
    setLoading(true); setError(""); setResult(null);
    try {
      const payload = { ...form };
      if (sid.trim()) payload.student_id = sid.trim();
      const { data } = await predict(payload);
      setResult(data);
    } catch (err) {
      const detail = err?.response?.data?.detail;
      setError(typeof detail === "string" ? detail : "Prediction failed");
    } finally {
      setLoading(false);
    }
  };

  const gradeBg = result ? `badge badge-${result.grade_band}` : "";

  return (
    <div>
      <h2 style={{ marginBottom: 24, fontSize: "1.4rem" }}>Predict Student SGPA</h2>

      {/* Step 1: Select student from dataset */}
      <div className="card">
        <h3>Step 1 — Select Student from Dataset</h3>
        <div className="field" style={{ maxWidth: 340 }}>
          <label>Student ID</label>
          <select
            value={sid}
            onChange={e => loadStudent(e.target.value)}
            style={{ width: "100%", padding: "8px 10px", border: "1px solid #30363d", borderRadius: 6, fontSize: "0.9rem", background: "#0d1117", color: "#e2e8f0" }}
          >
            <option value="">— select a student —</option>
            {studentIds.map(id => (
              <option key={id} value={id}>{id}</option>
            ))}
          </select>
        </div>
        {loadingData && <p style={{ color: "#8b949e", marginTop: 8 }}>Loading student data…</p>}
      </div>

      {/* Step 2: Auto-filled form (editable) */}
      <form onSubmit={submit}>
        <div className="card">
          <h3>Step 2 — Student Features {sid && <span style={{ fontWeight: 400, color: "#8b949e" }}>(loaded from {sid})</span>}</h3>
          <div className="form-grid">
            {/* Gender dropdown */}
            <div className="field">
              <label>Gender</label>
              <select
                value={form.gender}
                onChange={e => setForm(f => ({ ...f, gender: e.target.value }))}
                required
                style={{ width: "100%", padding: "8px 10px", border: "1px solid #30363d", borderRadius: 6, fontSize: "0.9rem", background: "#0d1117", color: "#e2e8f0" }}
              >
                <option value="Male">Male</option>
                <option value="Female">Female</option>
              </select>
            </div>

            {/* Numeric fields */}
            {NUM_FIELDS.map(f => (
              <div className="field" key={f.key}>
                <label>{f.label}</label>
                <input
                  type="number"
                  min={f.min} max={f.max} step={f.step}
                  value={form[f.key]}
                  onChange={e => handle(f.key, e.target.value)}
                  required
                />
              </div>
            ))}
          </div>
          <button className="primary" type="submit" disabled={loading || !form.age}>
            {loading ? "Predicting…" : "Predict SGPA"}
          </button>
          {error && <p className="error-msg">{error}</p>}
        </div>
      </form>

      {/* Step 3: Result with comparison */}
      {result && (
        <div className="result-box">
          <div className="score">{result.predicted_sgpa} / 10.0</div>
          <div className="sub" style={{ marginTop: 8 }}>
            Grade Band: <span className={gradeBg}>{result.grade_band}</span>
          </div>

          {/* Show actual vs predicted comparison if student was loaded from CSV */}
          {actualCgpa !== null && (
            <div style={{ marginTop: 16, padding: "12px 20px", background: "#1c2128", borderRadius: 8, display: "inline-block" }}>
              <table style={{ borderCollapse: "collapse", fontSize: "0.95rem" }}>
                <tbody>
                  <tr>
                    <td style={{ padding: "4px 16px 4px 0", color: "#8b949e" }}>Predicted SGPA</td>
                    <td style={{ fontWeight: 700, color: "#58a6ff" }}>{result.predicted_sgpa}</td>
                  </tr>
                  <tr>
                    <td style={{ padding: "4px 16px 4px 0", color: "#8b949e" }}>Actual SGPA (from data)</td>
                    <td style={{ fontWeight: 700, color: "#3fb950" }}>{actualCgpa}</td>
                  </tr>
                  <tr>
                    <td style={{ padding: "4px 16px 4px 0", color: "#8b949e" }}>Error</td>
                    <td style={{ fontWeight: 700, color: Math.abs(result.predicted_sgpa - actualCgpa) <= 0.5 ? "#3fb950" : "#f85149" }}>
                      {(result.predicted_sgpa - actualCgpa) > 0 ? "+" : ""}
                      {(result.predicted_sgpa - actualCgpa).toFixed(2)}
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          )}

          <div className="sub" style={{ marginTop: 8, fontSize: "0.8rem", color: "#8b949e" }}>
            Model: {result.model_version}
            {result.student_id && `  ·  Saved for ${result.student_id}`}
          </div>
        </div>
      )}
    </div>
  );
}
