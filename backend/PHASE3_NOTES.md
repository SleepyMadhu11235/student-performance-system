# Phase 3 — Django Backend & API

Not wired to the Phase 1 frontend yet (that's Phase 4). Verified end-to-end against a
local SQLite database inside this sandbox — see "Already verified" below.

## Run it

```bash
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env
# Edit .env — set your MySQL credentials, or set DB_ENGINE=sqlite to skip
# MySQL entirely for local dev/testing (see note below).

python3 manage.py makemigrations predictions
python3 manage.py migrate
python3 manage.py createsuperuser   # optional, for /admin
python3 manage.py runserver
```

The API is now live at `http://127.0.0.1:8000/api/...`. `ml_pipeline/model/student_model.pkl`
and `model_metrics.json` from Phase 2 ship inside this project, so predictions work
immediately — you don't have to retrain before testing.

## Design decisions worth knowing about

- **MySQL driver: PyMySQL, not mysqlclient.** `config/__init__.py` installs PyMySQL as a
  drop-in for `MySQLdb`, so Django's standard `django.db.backends.mysql` engine works without
  compiling `mysqlclient` against system MySQL headers. Same DB behavior, zero native build step.
- **`DB_ENGINE=sqlite` switch.** Purely a local-dev/testing convenience (see `.env.example`).
  Production should use `DB_ENGINE=mysql` (the default). I used the sqlite path to test
  everything below inside this sandbox, since it doesn't have a MySQL server running.
- **Pydantic for input, DRF for everything else.** Request bodies (`POST /api/predict`,
  `POST /api/retrain`) are validated with pydantic schemas in `predictions/schemas.py`, raised
  as a shared `AppError` on failure. Output serialization, pagination, and routing all use
  standard DRF (`predictions/serializers.py`, `predictions/views/`).
- **Standard error envelope, everywhere.** `core/exceptions.py` is wired in as
  `REST_FRAMEWORK["EXCEPTION_HANDLER"]`. Every error — pydantic validation, a 404, an
  `AppError`, or a genuine unhandled bug — comes back as
  `{"error": {"code": ..., "message": ..., "details": ...}}` with the right HTTP status, and
  is logged (`logs/app.log`, rotating, 5MB x 3 backups) before it reaches the client.
- **`student_id` is optional on `POST /api/predict`.** The Phase 1 single-prediction form
  doesn't collect one, so the backend auto-generates `STU-XXXXXXXX` when it's missing. CSV
  rows without a `student_id` column get `BULK-00001` etc. instead.
- **Rule-based explanation, not SHAP.** `predictions/services/explanation.py` compares each
  input against its own max, ranks them, and narrates the weakest one relative to the weight
  *that exact feature* carries in `SCORE_WEIGHTS` — imported directly from
  `ml_pipeline/train_pipeline.py` so the explanation can never drift out of sync with the
  actual scoring formula.
- **`/api/retrain` is synchronous**, per the spec's "async or synchronous" allowance. It calls
  `train_pipeline.run_pipeline()` in-process (typically 1-2s on this dataset size) and then
  hot-swaps the cached model via `ml_service.reload_pipeline()`, so the very next prediction
  uses the freshly trained pipeline with no server restart. Worth moving to a task queue
  (Celery, django-q) if the dataset grows large enough for this to become a slow request.
- **`/api/export/csv` streams.** Uses `StreamingHttpResponse` + a generator + `queryset.iterator()`
  rather than building the whole CSV in memory, so it scales to a large history table.
- **History pagination is `?page=&page_size=`** (DRF's `PageNumberPagination`) — offset-style,
  capped at `page_size=100`.

## Endpoint reference

| Method & path              | Notes |
|---|---|
| `POST /api/predict`        | Body: 5 features (required) + `student_id` (optional). Returns the created record, 201. |
| `POST /api/upload-csv`     | Multipart `file` field, `.csv` only. Row-by-row validation; bad rows are skipped and reported, not fatal. |
| `GET /api/history`         | Query params: `student_id`, `predicted_label`, `page`, `page_size`. |
| `DELETE /api/history/<id>` | 204 on success, standard 404 envelope if the id doesn't exist. |
| `GET /api/dashboard`       | `total`, `pass_rate`, `avg_confidence`, `counts`, `pie_data`, `bar_data` (Fail-tier feature averages), `line_data` (8-week trend by label). |
| `GET /api/models`          | Reads `ml_pipeline/model/model_metrics.json` directly — same shape Phase 2 already produces. |
| `POST /api/retrain`        | Body optional: `{"force_regenerate": false, "rows": 1500}`. |
| `GET /api/export/csv`      | Same filters as `/api/history`, streamed, unpaginated. |

## Already verified in this environment

Ran the full server against a local SQLite DB and exercised every endpoint with `curl`:

- `POST /api/predict` — valid request (label + confidence + rule-based explanation returned,
  record persisted); missing-field and out-of-range requests both return the standard 400
  validation envelope with pydantic's per-field details.
- `POST /api/upload-csv` — a 5-row roster with one missing value and one out-of-range value:
  3 predicted, 2 skipped, each skip reported with its row number and reason. Non-`.csv` files
  are rejected with `INVALID_FILE_TYPE`.
- `GET /api/history` — pagination (`page`, `page_size`) and both filters (`student_id`,
  `predicted_label`) all confirmed against real inserted rows.
- `DELETE /api/history/<id>` — 204 for a real id; standard `NOT_FOUND` envelope for a
  nonexistent one.
- `GET /api/models` — returns Phase 2's `model_metrics.json` as-is.
- `POST /api/retrain` — retrained in ~1.5s against the existing dataset, returned fresh
  metrics, and a follow-up `/api/predict` call confirmed the reloaded model was actually used.
- `GET /api/export/csv` — streamed correctly filtered CSV rows with proper headers.
- `GET /api/dashboard` — counts, pass rate, avg confidence, and all three chart arrays matched
  the rows actually in the database after the calls above.
- CORS — confirmed `access-control-allow-origin` is returned for the configured frontend
  origin (`http://localhost:5173`).
- `python manage.py check`, `makemigrations`, and `migrate` all run clean with no warnings.

## Not done yet (by design — later phases)

- Nothing in Phase 1's React app calls this API yet. That's Phase 4.
- No auth/permissions layer — this system doesn't have user accounts in the spec, so every
  endpoint is currently open. Worth flagging if this is ever exposed beyond a local network.
