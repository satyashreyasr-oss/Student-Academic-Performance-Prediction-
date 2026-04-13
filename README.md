# Student Performance Predictor

A full-stack ML web app that predicts student final exam scores from academic features,
stores predictions, accepts actual results, and computes live accuracy metrics.

## Project Structure

```
Math Exp/
├── ml/
│   ├── generate_data.py     # Creates data/students.csv (1000 rows)
│   ├── train.py             # Trains model → artifacts/
│   ├── data/
│   └── artifacts/           # model.pkl, pipeline.pkl, metrics.json, ...
│
├── backend/
│   ├── main.py              # FastAPI app
│   ├── models.py            # SQLAlchemy DB tables
│   ├── schemas.py           # Pydantic request/response models
│   ├── ml_service.py        # Model loader + predict()
│   ├── database.py          # SQLite setup
│   └── requirements.txt
│
├── frontend/
│   ├── src/
│   │   ├── App.js
│   │   ├── api.js           # Axios wrappers
│   │   └── pages/
│   │       ├── PredictPage.js
│   │       ├── StudentsPage.js
│   │       ├── ActualsPage.js
│   │       └── Dashboard.js
│   └── package.json
│
└── README.md
```

---

## Quick Start

### 1. Train the ML model

```bash
cd "Math Exp/ml"
pip install scikit-learn pandas numpy joblib
mkdir data artifacts
python generate_data.py        # creates data/students.csv
python train.py                # trains model, saves to artifacts/
```

You'll see output like:
```
Best model: GradientBoosting  (val MAE=3.8xx)
Test metrics: { "test_mae": 3.9, "test_rmse": 4.8, "test_r2": 0.92 }
```

### 2. Start the backend

```bash
cd "Math Exp/backend"
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

API docs → http://localhost:8000/docs

### 3. Start the frontend

```bash
cd "Math Exp/frontend"
npm install
npm start
```

App → http://localhost:3000

---

## Features

| Feature | Description |
|---|---|
| **Predict** | Enter 10 academic features → get predicted score + grade band |
| **Students** | Register students (ID, name, section) |
| **Actual Results** | Enter final exam scores after results are published |
| **Dashboard** | MAE / RMSE / R² cards, scatter plot, error histogram, feature importance |

---

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| POST | `/predict` | Predict final score |
| POST | `/students` | Add student |
| GET | `/students` | List students |
| POST | `/records` | Save student feature record |
| POST | `/actuals` | Save actual exam result |
| GET | `/metrics` | Live MAE/RMSE/R² vs DB records |
| GET | `/comparison` | Per-student predicted vs actual |
| GET | `/feature-importance` | Model feature weights |

---

## Input Features

| Feature | Range | Description |
|---|---|---|
| attendance | 0–100% | Class attendance percentage |
| internal_avg | 0–100 | Average of internal/class tests |
| assignment_avg | 0–100 | Average assignment score |
| assignment_rate | 0–100% | % of assignments submitted |
| quiz_avg | 0–100 | Average quiz score |
| prev_gpa | 0–10 | Previous semester GPA |
| study_hours | 0–24 | Daily study hours |
| late_submissions | 0+ | Count of late submissions |
| backlogs | 0+ | Number of failed/backlog subjects |
| participation | 0–10 | Classroom participation rating |

---

## Replacing Synthetic Data with Real Data

1. Export your school's data as a CSV matching `data/students.csv` columns.
2. Replace the file at `ml/data/students.csv`.
3. Re-run `python train.py` — it will retrain and save new artifacts.
4. Restart the backend (`uvicorn`) — it picks up the new model automatically.

---

## Deployment (optional)

- **Backend**: Deploy to Render / Railway — set `DATABASE_URL` env variable to a Postgres URL.
- **Frontend**: `npm run build` → deploy `build/` to Vercel / Netlify.
- Update `ARTIFACT_DIR` in `ml_service.py` to point to your artifact storage.
