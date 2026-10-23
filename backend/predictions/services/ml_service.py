"""
Thin wrapper around the joblib-serialized sklearn Pipeline. Loaded once and
cached in a module-level global; POST /api/retrain calls reload_pipeline()
so subsequent predictions immediately use the freshly trained model without
requiring a server restart.
"""

from __future__ import annotations

import logging
import threading
from typing import Any

import joblib
import pandas as pd
from django.conf import settings

from core.exceptions import AppError

logger = logging.getLogger("predictions")

FEATURE_ORDER = [
    "attendance_rate",
    "midterm_1",
    "midterm_2",
    "assignments_avg",
    "study_hours_weekly",
]

_pipeline = None
_lock = threading.Lock()


def _load_pipeline():
    model_path = settings.ML_MODEL_PATH
    if not model_path.exists():
        raise AppError(
            f"No trained model found at {model_path}. Run train_pipeline.py "
            "(or POST /api/retrain) before requesting predictions.",
            code="MODEL_NOT_TRAINED",
            http_status=503,
        )
    logger.info("Loading model pipeline from %s", model_path)
    return joblib.load(model_path)


def get_pipeline():
    """Lazily load and cache the pipeline; thread-safe for WSGI workers."""
    global _pipeline
    if _pipeline is None:
        with _lock:
            if _pipeline is None:
                _pipeline = _load_pipeline()
    return _pipeline


def reload_pipeline() -> None:
    """Force a fresh load from disk — call this right after retraining."""
    global _pipeline
    with _lock:
        _pipeline = _load_pipeline()


def predict_one(features: dict[str, float]) -> dict[str, Any]:
    pipeline = get_pipeline()
    row = pd.DataFrame([[features[c] for c in FEATURE_ORDER]], columns=FEATURE_ORDER)

    label = pipeline.predict(row)[0]
    proba = pipeline.predict_proba(row)[0]
    probabilities = {cls: round(float(p), 4) for cls, p in zip(pipeline.classes_, proba)}
    confidence = round(max(probabilities.values()) * 100, 2)

    return {"predicted_label": label, "confidence_score": confidence, "probabilities": probabilities}


def predict_many(df: pd.DataFrame) -> list[dict[str, Any]]:
    """Batch version used by the CSV upload endpoint. `df` must already
    contain FEATURE_ORDER columns as numeric values."""
    pipeline = get_pipeline()
    X = df[FEATURE_ORDER]

    labels = pipeline.predict(X)
    probas = pipeline.predict_proba(X)

    results = []
    for label, proba in zip(labels, probas):
        probabilities = {cls: round(float(p), 4) for cls, p in zip(pipeline.classes_, proba)}
        confidence = round(max(probabilities.values()) * 100, 2)
        results.append({"predicted_label": label, "confidence_score": confidence, "probabilities": probabilities})
    return results
