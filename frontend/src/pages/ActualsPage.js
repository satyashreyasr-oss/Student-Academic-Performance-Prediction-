import React, { useState, useEffect } from "react";
import { saveActual, listCSVStudents, getCSVStudent } from "../api";

export default function ActualsPage() {
  const [studentIds, setStudentIds] = useState([]);
  const [sid,        setSid]        = useState("");
  const [score,      setScore]      = useState("");
  const [msg,        setMsg]        = useState("");
  const [error,      setError]      = useState("");
  const [loading,    setLoading]    = useState(false);

  useEffect(() => {
    listCSVStudents().then(r => setStudentIds(r.data)).catch(() => {});
  }, []);

  // When student selected, auto-fetch SGPA from CSV data
  const onStudentSelect = async (selectedId) => {
    setSid(selectedId);
    setScore(""); setMsg(""); setError("");
    if (!selectedId) return;
    setLoading(true);
    try {
      const { data } = await getCSVStudent(selectedId);
      if (data.actual_sgpa !== null && data.actual_sgpa !== undefined) {
        setScore(String(data.actual_sgpa));
      }
    } catch {
      setError("Could not fetch SGPA for this student");
    } finally {
      setLoading(false);
    }
  };

  const submit = async (e) => {
    e.preventDefault();
    setMsg(""); setError("");
    try {
      await saveActual({ student_id: sid, actual_sgpa: parseFloat(score) });
      setMsg(`Actual SGPA saved for ${sid}.`);
      setSid(""); setScore("");
    } catch (err) {
      const detail = err?.response?.data?.detail;
      setError(typeof detail === "string" ? detail : "Error saving result");
    }
  };

  return (
    <div>
      <h2 style={{ marginBottom: 24, fontSize: "1.4rem" }}>Enter Actual Results</h2>

      <div className="card">
        <h3>Enter / Update Actual SGPA</h3>
        <form onSubmit={submit}>
          <div className="form-grid" style={{ gridTemplateColumns: "1fr 1fr" }}>
            <div className="field">
              <label>Student ID</label>
              <select
                value={sid}
                onChange={e => onStudentSelect(e.target.value)}
                required
                style={{ width: "100%", padding: "8px 10px", border: "1px solid #30363d", borderRadius: 6, fontSize: "0.9rem", background: "#0d1117", color: "#e2e8f0" }}
              >
                <option value="">— select student —</option>
                {studentIds.map(id => (
                  <option key={id} value={id}>{id}</option>
                ))}
              </select>
            </div>

            <div className="field">
              <label>Actual SGPA (0–10) {score && <span style={{ color: "#3fb950", fontSize: "0.8rem" }}>— auto-filled from form data</span>}</label>
              <input
                type="number" min={0} max={10} step={0.01}
                value={score}
                onChange={e => setScore(e.target.value)}
                required
                readOnly={!!score && !!sid}
                style={score && sid ? { opacity: 0.85, cursor: "not-allowed" } : {}}
              />
            </div>
          </div>

          {loading && <p style={{ color: "#8b949e", marginTop: 8 }}>Fetching SGPA from Google Form data…</p>}
          <button className="primary" type="submit" disabled={!sid || !score}>Save Result</button>
          {msg   && <p className="success-msg">{msg}</p>}
          {error && <p className="error-msg">{error}</p>}
        </form>

        <p style={{ marginTop: 16, fontSize: "0.82rem", color: "#8b949e" }}>
          SGPA is automatically fetched from the Google Form responses when you select a student.
        </p>
      </div>
    </div>
  );
}
