"""
Row-by-row CSV ingestion for POST /api/upload-csv. Each row is validated
through the same PredictRequestSchema used by the single-prediction
endpoint, so a class roster and a single manual entry are held to
identical rules. Valid rows are then run through the model in one batched
call rather than one prediction call per row.
"""

from __future__ import annotations

import csv
import io
from typing import Any

import pandas as pd
from pydantic import ValidationError

from predictions.models import StudentPrediction
from predictions.schemas import PredictRequestSchema
from predictions.services import ml_service
from predictions.services.explanation import build_explanation

REQUIRED_COLUMNS = {
    "attendance_rate",
    "midterm_1",
    "midterm_2",
    "assignments_avg",
    "study_hours_weekly",
}

MAX_REPORTED_SKIPS = 50


def process_csv(file_obj) -> dict[str, Any]:
    """
    Returns:
        {
          "rows_read": int, "predicted": int, "skipped": int,
          "skipped_rows": [{"row": int, "reason": str}, ...],
          "instances": [StudentPrediction, ...]   # unsaved, ready for bulk_create
        }
    """
    raw_text = file_obj.read().decode("utf-8-sig")
    reader = csv.DictReader(io.StringIO(raw_text))

    if not reader.fieldnames:
        return _empty_result("File is empty or not a valid CSV.")

    header = {c.strip() for c in reader.fieldnames if c}
    missing_columns = REQUIRED_COLUMNS - header
    if missing_columns:
        return _empty_result(f"Missing required column(s): {', '.join(sorted(missing_columns))}")

    valid_rows: list[dict] = []
    skipped_rows: list[dict] = []
    rows_read = 0

    for i, raw_row in enumerate(reader, start=1):
        rows_read += 1
        cleaned = {k.strip(): v.strip() if isinstance(v, str) else v for k, v in raw_row.items() if k}
        try:
            schema = PredictRequestSchema(
                student_id=cleaned.get("student_id") or None,
                attendance_rate=_to_float(cleaned.get("attendance_rate")),
                midterm_1=_to_float(cleaned.get("midterm_1")),
                midterm_2=_to_float(cleaned.get("midterm_2")),
                assignments_avg=_to_float(cleaned.get("assignments_avg")),
                study_hours_weekly=_to_float(cleaned.get("study_hours_weekly")),
            )
            valid_rows.append(
                {
                    "student_id": schema.student_id or f"BULK-{i:05d}",
                    "attendance_rate": schema.attendance_rate,
                    "midterm_1": schema.midterm_1,
                    "midterm_2": schema.midterm_2,
                    "assignments_avg": schema.assignments_avg,
                    "study_hours_weekly": schema.study_hours_weekly,
                }
            )
        except (ValidationError, TypeError, ValueError) as exc:
            reason = exc.errors()[0]["msg"] if isinstance(exc, ValidationError) and exc.errors() else str(exc)
            skipped_rows.append({"row": i, "reason": reason})

    instances = _predict_and_build_instances(valid_rows)

    return {
        "rows_read": rows_read,
        "predicted": len(instances),
        "skipped": len(skipped_rows),
        "skipped_rows": skipped_rows[:MAX_REPORTED_SKIPS],
        "instances": instances,
    }


def _to_float(value) -> float:
    if value is None or value == "":
        raise ValueError("value is required")
    return float(value)


def _predict_and_build_instances(valid_rows: list[dict]) -> list[StudentPrediction]:
    if not valid_rows:
        return []

    df = pd.DataFrame(valid_rows)
    predictions = ml_service.predict_many(df)

    instances = []
    for row, pred in zip(valid_rows, predictions):
        features = {k: row[k] for k in REQUIRED_COLUMNS}
        explanation = build_explanation(features, pred["predicted_label"])
        instances.append(
            StudentPrediction(
                student_id=row["student_id"],
                predicted_label=pred["predicted_label"],
                confidence_score=pred["confidence_score"],
                rule_based_explanation=explanation,
                source=StudentPrediction.Source.BULK,
                **features,
            )
        )
    return instances


def _empty_result(reason: str) -> dict[str, Any]:
    return {
        "rows_read": 0,
        "predicted": 0,
        "skipped": 0,
        "skipped_rows": [{"row": 0, "reason": reason}],
        "instances": [],
    }
