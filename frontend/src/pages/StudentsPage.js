import React, { useState, useEffect } from "react";
import { createStudent, listStudents } from "../api";

export default function StudentsPage() {
  const [sid,      setSid]      = useState("");
  const [students, setStudents] = useState([]);
  const [msg,      setMsg]      = useState("");
  const [error,    setError]    = useState("");

  const load = () => listStudents().then(r => setStudents(r.data));

  useEffect(() => { load(); }, []);

  const submit = async (e) => {
    e.preventDefault();
    setMsg(""); setError("");
    try {
      await createStudent({ student_id: sid, name: sid });
      setMsg("Student added successfully.");
      setSid("");
      load();
    } catch (err) {
      setError(err?.response?.data?.detail || "Error adding student");
    }
  };

  return (
    <div>
      <h2 style={{ marginBottom: 24, fontSize: "1.4rem" }}>Students</h2>

      <div className="card">
        <h3>Add Student</h3>
        <form onSubmit={submit}>
          <div className="field" style={{ maxWidth: 300 }}>
            <label>Student ID</label>
            <input
              value={sid}
              placeholder="e.g. S001"
              onChange={e => setSid(e.target.value)}
              required
            />
          </div>
          <button className="primary" type="submit">Add Student</button>
          {msg   && <p className="success-msg">{msg}</p>}
          {error && <p className="error-msg">{error}</p>}
        </form>
      </div>

      <div className="card">
        <h3>All Students ({students.length})</h3>
        <table>
          <thead>
            <tr><th>Student ID</th></tr>
          </thead>
          <tbody>
            {students.map(s => (
              <tr key={s.id}>
                <td>{s.student_id}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
