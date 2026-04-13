import React from "react";
import { Routes, Route, NavLink } from "react-router-dom";
import PredictPage   from "./pages/PredictPage";
import Dashboard     from "./pages/Dashboard";
import ActualsPage   from "./pages/ActualsPage";

export default function App() {
  return (
    <div className="layout">
      <aside className="sidebar">
        <h2>Student Performance Predictor</h2>
        <nav>
          <NavLink to="/"         end>Dashboard</NavLink>
          <NavLink to="/predict">Predict</NavLink>
          <NavLink to="/actuals"> Enter Actual Results</NavLink>
        </nav>
      </aside>

      <main className="main-content">
        <Routes>
          <Route path="/"          element={<Dashboard />} />
          <Route path="/predict"   element={<PredictPage />} />
          <Route path="/actuals"   element={<ActualsPage />} />
        </Routes>
      </main>
    </div>
  );
}
