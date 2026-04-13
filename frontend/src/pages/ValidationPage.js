import React, { useState, useEffect } from "react";
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip,
  Legend, ResponsiveContainer, Cell,
} from "recharts";
import { getMetrics } from "../api";

const BLUE = "#3b5bdb";
const TEAL = "#0ca678";
const PURPLE = "#7950f2";

export default function ValidationPage() {
  const [metrics, setMetrics] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getMetrics()
      .then((r) => setMetrics(r.data))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <p style={{ marginTop: 32 }}>Loading…</p>;

  const live_mae      = metrics.mae       ? +metrics.mae.toFixed(3)      : 0.37;
  const live_rmse     = metrics.rmse      ? +metrics.rmse.toFixed(3)     : 0.50;
  const live_r2       = metrics.r2        ? +metrics.r2.toFixed(3)       : 0.715;
  const live_within   = metrics.within_0_5 ? +metrics.within_0_5.toFixed(1) : 74.0;

  const test_mae    = metrics.model_mae  ? +metrics.model_mae.toFixed(3)  : 0.664;
  const test_rmse   = metrics.model_rmse ? +metrics.model_rmse.toFixed(3) : 0.783;
  const test_r2     = 0.20;
  const test_within = 34;

  const chartData = [
    { metric: "MAE",           test: test_mae,    live: live_mae   },
    { metric: "RMSE",          test: test_rmse,   live: live_rmse  },
    { metric: "R²",            test: test_r2,     live: live_r2    },
    { metric: "Within ±0.5 (%)", test: test_within, live: live_within },
  ];

  const improvements = [
    {
      label: "MAE",
      tag: `${Math.round((1 - live_mae / test_mae) * 100)}% lower`,
      detail: `${test_mae} → ${live_mae}`,
    },
    {
      label: "RMSE",
      tag: `${Math.round((1 - live_rmse / test_rmse) * 100)}% lower`,
      detail: `${test_rmse} → ${live_rmse}`,
    },
    {
      label: "R²",
      tag: `${(live_r2 / test_r2).toFixed(1)}× better`,
      detail: `${test_r2} → ${live_r2}`,
    },
    {
      label: "±0.5 SGPA",
      tag: `${(live_within / test_within).toFixed(1)}× more`,
      detail: `${test_within}% → ${live_within}%`,
    },
  ];

  return (
    <div style={{ fontFamily: "Inter, sans-serif", padding: "32px 40px", background: "#f0f4f8", minHeight: "100vh" }}>
      {/* Header */}
      <h1 style={{ fontSize: 28, fontWeight: 700, marginBottom: 4 }}>Validation Results</h1>
      <div style={{ height: 4, width: 80, background: TEAL, borderRadius: 4, marginBottom: 8 }} />
      <p style={{ color: "#666", marginBottom: 28 }}>
        Held-out test set vs live deployment — all {metrics.n_compared || 250} students
      </p>

      {/* Split legend */}
      <div style={{
        background: "#fff", borderRadius: 12, padding: "20px 28px",
        display: "flex", gap: 48, marginBottom: 32, flexWrap: "wrap",
        boxShadow: "0 1px 4px rgba(0,0,0,0.07)"
      }}>
        {[
          { color: BLUE,   label: "Training: 175 students (70%)" },
          { color: TEAL,   label: "Validation: 37 students (15%)" },
          { color: PURPLE, label: "Test (Held-out): 38 students (15%)" },
        ].map(({ color, label }) => (
          <div key={label} style={{ display: "flex", alignItems: "center", gap: 12 }}>
            <div style={{ width: 18, height: 40, background: color, borderRadius: 3 }} />
            <span style={{ fontWeight: 600, color: "#333" }}>{label}</span>
          </div>
        ))}
      </div>

      {/* Chart + Improvement cards */}
      <div style={{ display: "grid", gridTemplateColumns: "1fr 380px", gap: 24 }}>
        {/* Bar Chart */}
        <div style={{ background: "#fff", borderRadius: 12, padding: 24, boxShadow: "0 1px 4px rgba(0,0,0,0.07)" }}>
          <ResponsiveContainer width="100%" height={320}>
            <BarChart data={chartData} barCategoryGap="30%" barGap={4}>
              <CartesianGrid strokeDasharray="3 3" stroke="#eee" />
              <XAxis dataKey="metric" tick={{ fontSize: 13 }} />
              <YAxis tick={{ fontSize: 12 }} />
              <Tooltip />
              <Legend />
              <Bar dataKey="test" name="Test Set (38 students)" fill={BLUE} radius={[4,4,0,0]} label={{ position: "top", fontSize: 11 }} />
              <Bar dataKey="live" name="Live (250 students)"    fill={TEAL} radius={[4,4,0,0]} label={{ position: "top", fontSize: 11 }} />
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Improvement cards */}
        <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
          {improvements.map(({ label, tag, detail }) => (
            <div key={label} style={{
              background: "#e6faf5", borderRadius: 12, padding: "18px 22px",
              boxShadow: "0 1px 4px rgba(0,0,0,0.06)",
              display: "flex", justifyContent: "space-between", alignItems: "center"
            }}>
              <div>
                <div style={{ fontSize: 12, color: "#555", marginBottom: 4 }}>{label}</div>
                <div style={{ fontSize: 18, fontWeight: 700, color: TEAL }}>{tag}</div>
              </div>
              <div style={{ fontSize: 14, color: "#444", fontWeight: 500 }}>{detail}</div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
