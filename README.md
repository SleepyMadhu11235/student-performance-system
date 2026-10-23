# Student Performance Prediction System

React (Vite) &rarr; Django REST API &rarr; scikit-learn pipeline &rarr; MySQL &rarr; back to React.

```
student-performance-system/
├── frontend/         React 18 + Vite + Tailwind + Recharts
└── backend/
    ├── config/       Django settings, root URLs
    ├── core/         Shared error-envelope / exception handling
    ├── predictions/  The app: model, views, serializers, pydantic schemas, services
    └── ml_pipeline/  train_pipeline.py + the dataset + the trained model, embedded
```

## Run it (two terminals)

**Backend:**
```bash
cd backend
python3 -m venv venv && source venv/bin/activate    # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env        # edit DB credentials, or set DB_ENGINE=sqlite for zero-setup local dev
python3 manage.py migrate
python3 manage.py runserver
```

**Frontend:**
```bash
cd frontend
npm install
cp .env.example .env        # default already points at http://localhost:8000/api
npm run dev
```

Open the URL Vite prints (`http://localhost:5173` by default). The trained model and dataset
from Phase 2 ship inside `backend/ml_pipeline/`, so predictions work immediately — nothing to
train before you can use it.

## What's inside, phase by phase

- **Phase 1 — Frontend UI.** All four pages (Dashboard, Predict, History, Models), a
  "gradebook ledger" design system, fully responsive, originally built against mock data.
- **Phase 2 — ML pipeline.** `train_pipeline.py` generates a realistic synthetic dataset
  (correlated features via a shared latent-ability model, not independent uniform draws — see
  the docstring in `generate_synthetic_dataset()`), trains 4 algorithms, and serializes the
  champion (Random Forest, in the shipped run) as a single scikit-learn `Pipeline`.
- **Phase 3 — Django backend.** All 8 endpoints (`predict`, `upload-csv`, `history` +
  `history/<id>`, `dashboard`, `models`, `retrain`, `export/csv`), pydantic input validation,
  a standard JSON error envelope, rule-based explanations, and rotating file logging. Full
  design rationale in `backend/PHASE3_NOTES.md`.
- **Phase 4 — Integration.** The frontend now calls the real API for everything: live
  dashboard charts, real predictions with real explanations, real CSV upload with real
  progress and per-row skip reporting, server-driven history pagination/search/filter/export,
  and live model metrics with a working retrain button. No mock data remains in the frontend.

## Verified together, end-to-end

Both servers were run side by side in this environment and exercised as the browser would:
every endpoint was called from the actual Vite origin (`http://127.0.0.1:5173`) against the
actual Django server, confirming CORS works and that every field name the React components
read (`student_id`, `pie_data`, `is_champion`, `results`, `count`, ...) matches the real API
responses exactly — predict (success + validation error), CSV upload (valid + skipped rows),
history (pagination + both filters), delete (success + 404), dashboard, models, retrain
(with a follow-up prediction confirming the hot-swapped model), and CSV export all checked out
with no errors in either server's logs.

## Not done yet

Phase 5 — the production `.env`/`requirements`/`package.json` manifests already exist
per-project, but the comprehensive top-level documentation (API JSON contracts, DB schema
reference, deployment guide for Gunicorn/production MySQL/CORS hardening) hasn't been written
yet. Say the word and I'll do that next.
