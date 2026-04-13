import React, { useState, useEffect } from "react";
import {
  ScatterChart, Scatter, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, ReferenceLine, BarChart, Bar, Cell,
  Legend,
} from "recharts";
import { getMetrics, getComparison, getFeatureImp } from "../api";

export default function Dashboard() {
  const [metrics,  setMetrics]  = useState(null);
  const [compare,  setCompare]  = useState([]);
  const [fi,       setFi]       = useState({});
  const [loading,  setLoading]  = useState(true);

  useEffect(() => {
    Promise.all([getMetrics(), getComparison(), getFeatureImp()])
      .then(([m, c, f]) => {
        setMetrics(m.data);
        setCompare(c.data);
        setFi(f.data);
      })
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <p style={{ marginTop: 32 }}>Loading dashboard…</p>;
  if (!metrics) return <p style={{ marginTop: 32, color: "#f85149" }}>Backend error — make sure the backend is running on port 8000 and refresh.</p>;

  // Feature importance chart data
  const fiData = Object.entries(fi)
    .map(([name, value]) => ({ name: name.replace(/_/g, " "), value: parseFloat((value * 100).toFixed(2)) }))
    .sort((a, b) => b.value - a.value);

  // Error histogram buckets (SGPA scale)
  const buckets = { "0–0.2": 0, "0.2–0.5": 0, "0.5–1.0": 0, "1.0–2.0": 0, ">2.0": 0 };
  compare.forEach(r => {
    const e = r.abs_error;
    if (e <= 0.2)      buckets["0–0.2"]++;
    else if (e <= 0.5) buckets["0.2–0.5"]++;
    else if (e <= 1.0) buckets["0.5–1.0"]++;
    else if (e <= 2.0) buckets["1.0–2.0"]++;
    else               buckets[">2.0"]++;
  });
  const histData = Object.entries(buckets).map(([k, v]) => ({ range: k, count: v }));

  const COLORS = ["#3182ce", "#38a169", "#d69e2e", "#e53e3e", "#805ad5"];

  return (
    <div>
      <h2 style={{ marginBottom: 24, fontSize: "1.4rem" }}>Dashboard</h2>

      {/* Metric cards – live (from DB comparisons) */}
      <div className="metric-row">
        {[
          { label: "Students compared", value: metrics.n_compared },
          { label: "Live MAE",          value: metrics.n_compared ? metrics.mae.toFixed(2) : "—" },
          { label: "Live RMSE",         value: metrics.n_compared ? metrics.rmse.toFixed(2) : "—" },
          { label: "Live R²",           value: metrics.n_compared ? metrics.r2.toFixed(3) : "—" },
          { label: "Within ±0.5 SGPA",  value: metrics.n_compared ? `${metrics.within_0_5}%` : "—" },
        ].map(m => (
          <div className="metric-card" key={m.label}>
            <div className="value">{m.value}</div>
            <div className="label">{m.label}</div>
          </div>
        ))}
      </div>

      {/* Training metrics reference */}
      <div className="card" style={{ marginBottom: 20 }}>
        <h3>Training / Test Set Metrics (from last training run)</h3>
        <div style={{ display: "flex", gap: 32 }}>
          {[
            ["MAE",  metrics.model_mae],
            ["RMSE", metrics.model_rmse],
            ["R²",   metrics.model_r2],
          ].map(([l, v]) => (
            <div key={l}>
              <span style={{ fontWeight: 700, fontSize: "1.4rem", color: "#58a6ff" }}>{v}</span>
              <span style={{ marginLeft: 6, color: "#8b949e", fontSize: "0.85rem" }}>{l}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Predicted vs Actual scatter */}
      {compare.length > 0 && (
        <div className="card">
          <h3>Predicted vs Actual SGPA</h3>
          <ResponsiveContainer width="100%" height={320}>
            <ScatterChart>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="predicted" name="Predicted" domain={[0,10]} label={{ value:"Predicted SGPA", position:"insideBottom", offset:-4 }} />
              <YAxis dataKey="actual"    name="Actual"    domain={[0,10]} label={{ value:"Actual SGPA", angle:-90, position:"insideLeft" }} />
              <Tooltip cursor={{ strokeDasharray: "3 3" }} />
              <ReferenceLine segment={[{x:0,y:0},{x:10,y:10}]} stroke="#e53e3e" strokeDasharray="4 4" label="Perfect" />
              <Scatter data={compare} fill="#3182ce" opacity={0.7} />
            </ScatterChart>
          </ResponsiveContainer>
        </div>
      )}

      {/* Error histogram */}
      {compare.length > 0 && (
        <div className="card">
          <h3>Prediction Error Distribution (SGPA)</h3>
          <ResponsiveContainer width="100%" height={240}>
            <BarChart data={histData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="range" />
              <YAxis allowDecimals={false} />
              <Tooltip />
              <Bar dataKey="count" name="Students" radius={[4,4,0,0]}>
                {histData.map((_, i) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}

      {/* Feature importance */}
      {fiData.length > 0 && (
        <div className="card">
          <h3>Feature Importance (%)</h3>
          <ResponsiveContainer width="100%" height={260}>
            <BarChart data={fiData} layout="vertical">
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis type="number" unit="%" />
              <YAxis type="category" dataKey="name" width={130} tick={{ fontSize: 12 }} />
              <Tooltip formatter={v => `${v}%`} />
              <Bar dataKey="value" fill="#58a6ff" radius={[0,4,4,0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}

      {/* Per-student comparison table */}
      {compare.length > 0 && (
        <div className="card">
          <h3>Per-Student Comparison</h3>
          <table>
            <thead>
              <tr>
                <th>Student ID</th><th>Name</th>
                <th>Predicted SGPA</th><th>Actual SGPA</th>
                <th>Error</th><th>Abs Error</th>
              </tr>
            </thead>
            <tbody>
              {compare.map(r => (
                <tr key={r.student_id}>
                  <td>{r.student_id}</td>
                  <td>{r.name}</td>
                  <td>{r.predicted}</td>
                  <td>{r.actual}</td>
                  <td style={{ color: r.error < 0 ? "#f85149" : "#3fb950" }}>
                    {r.error > 0 ? "+" : ""}{r.error}
                  </td>
                  <td>{r.abs_error}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {compare.length === 0 && (
        <div className="card" style={{ textAlign: "center", color: "#8b949e", padding: 48 }}>
          No comparison data yet. Make predictions and then enter actual results to see graphs here.
        </div>
      )}
    </div>
  );
}
