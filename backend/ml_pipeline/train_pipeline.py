"""
train_pipeline.py
==================

Self-contained ML module for the Student Performance Prediction System.

Responsibilities:
  1. Generate a synthetic labeled dataset (only if one does not already exist).
  2. Train four candidate classifiers (Random Forest, Decision Tree,
     Gaussian Naive Bayes, K-Nearest Neighbors) on a 70/30 split.
  3. Evaluate each on Accuracy / Precision / Recall / F1 (weighted).
  4. Select the champion model (highest F1) and wrap it with its
     preprocessing step in a single sklearn Pipeline.
  5. Refit that pipeline on the FULL dataset and serialize it to
     model/student_model.pkl via joblib.
  6. Persist the four-way comparison metrics to model/model_metrics.json
     so the Django API (Phase 3, GET /api/models) can serve them directly
     instead of recomputing anything.

Usage:
    python train_pipeline.py
    python train_pipeline.py --rows 2000 --force-regenerate
    python train_pipeline.py --data-path dataset/student_dataset.csv --model-dir model

This module is also designed to be imported directly, e.g. from a Django
view backing POST /api/retrain:

    from train_pipeline import run_pipeline
    results = run_pipeline()
"""

from __future__ import annotations

import argparse
import json
import logging
import os
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd
from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score
from sklearn.model_selection import train_test_split
from sklearn.naive_bayes import GaussianNB
from sklearn.neighbors import KNeighborsClassifier
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("train_pipeline")

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent
DEFAULT_DATA_PATH = BASE_DIR / "dataset" / "student_dataset.csv"
DEFAULT_MODEL_DIR = BASE_DIR / "model"
DEFAULT_MODEL_PATH = DEFAULT_MODEL_DIR / "student_model.pkl"
DEFAULT_METRICS_PATH = DEFAULT_MODEL_DIR / "model_metrics.json"

RANDOM_SEED = 42

FEATURE_COLUMNS = [
    "attendance_rate",
    "midterm_1",
    "midterm_2",
    "assignments_avg",
    "study_hours_weekly",
]
TARGET_COLUMN = "final_score"
LABEL_COLUMN = "label"

# Weights used to build the synthetic ground-truth score. Kept as a module
# constant so the rule-based explanation engine in Phase 3 can reuse the
# exact same weighting when it reasons about feature influence.
SCORE_WEIGHTS = {
    "attendance_rate": 0.18,
    "midterm_1": 0.27,
    "midterm_2": 0.27,
    "assignments_avg": 0.18,
    "study_hours_weekly": 0.10,
}

LABEL_THRESHOLDS = [
    (85, 100, "Excellent"),
    (70, 85, "Good"),
    (50, 70, "Pass"),
    (0, 50, "Fail"),
]


# ---------------------------------------------------------------------------
# 1. Synthetic data generation
# ---------------------------------------------------------------------------


def score_to_label(score: float) -> str:
    """Map a final_score (0-100) to its category label."""
    if score >= 85:
        return "Excellent"
    if score >= 70:
        return "Good"
    if score >= 50:
        return "Pass"
    return "Fail"


def generate_synthetic_dataset(n_rows: int = 1500, seed: int = RANDOM_SEED) -> pd.DataFrame:
    """
    Generate a synthetic student performance dataset.

    Features are NOT drawn independently and uniformly — real students don't
    work that way. Instead each student gets a single latent "ability /
    diligence" factor z in [0, 1] (Beta-distributed), and every feature is a
    noisy, individually-scaled function of that same z. This produces the
    two things a real classroom dataset actually has:

      1. Realistic per-feature marginal ranges — attendance clusters high
         and tight (most students show up most of the time), exam scores
         center lower with more spread, assignments sit a bit above exams
         (effort-based, less time pressure), and weekly study hours average
         a plausible ~14-16 hrs/week rather than being uniform 0-30.
      2. Positive correlation between features — a diligent student tends to
         have good attendance AND good exam scores AND turn in assignments,
         rather than each feature being an independent coin flip. Without
         this, a weighted sum of 5 independent features regresses hard
         toward the mean and almost never produces an "Excellent" outcome.

    Target (unchanged from spec):
        base_score = attendance*0.18 + midterm_1*0.27 + midterm_2*0.27
                     + assignments*0.18 + study_hours*0.10
        final_score = clamp(base_score + uniform(-8, 8), 0, 100)

    Label thresholds (unchanged from spec):
        Excellent [85-100], Good [70-84], Pass [50-69], Fail [<50]

    With seed=42 this yields roughly: Fail ~12%, Pass ~41%, Good ~40%,
    Excellent ~7% — a believable classroom curve with a real, learnable
    at-risk population instead of a near-empty tail.
    """
    rng = np.random.default_rng(seed)

    # Shared latent ability/diligence factor per student, in [0, 1].
    latent_mean, latent_concentration = 0.65, 4
    alpha = latent_mean * latent_concentration
    beta = (1 - latent_mean) * latent_concentration
    z = rng.beta(alpha, beta, n_rows)

    # Each feature = its own baseline + its own scale * z + its own noise.
    # (offset, scale, noise_std) chosen so marginal means/ranges are realistic.
    attendance_rate = np.clip(55 + z * 40 + rng.normal(0, 8, n_rows), 0, 100)
    midterm_1 = np.clip(28 + z * 66 + rng.normal(0, 11, n_rows), 0, 100)
    midterm_2 = np.clip(28 + z * 66 + rng.normal(0, 11, n_rows), 0, 100)
    assignments_avg = np.clip(38 + z * 56 + rng.normal(0, 9, n_rows), 0, 100)
    study_hours_weekly = np.clip(2 + z * 20 + rng.normal(0, 4, n_rows), 0, 30)

    base_score = (
        attendance_rate * SCORE_WEIGHTS["attendance_rate"]
        + midterm_1 * SCORE_WEIGHTS["midterm_1"]
        + midterm_2 * SCORE_WEIGHTS["midterm_2"]
        + assignments_avg * SCORE_WEIGHTS["assignments_avg"]
        + study_hours_weekly * SCORE_WEIGHTS["study_hours_weekly"]
    )
    noise = rng.uniform(-8, 8, n_rows)
    final_score = np.clip(base_score + noise, 0, 100)

    df = pd.DataFrame(
        {
            "attendance_rate": np.round(attendance_rate, 2),
            "midterm_1": np.round(midterm_1, 2),
            "midterm_2": np.round(midterm_2, 2),
            "assignments_avg": np.round(assignments_avg, 2),
            "study_hours_weekly": np.round(study_hours_weekly, 2),
            "final_score": np.round(final_score, 2),
        }
    )
    df[LABEL_COLUMN] = df[TARGET_COLUMN].apply(score_to_label)
    df.insert(0, "student_id", [f"SYN-{i + 1:05d}" for i in range(n_rows)])

    return df


def load_or_generate_dataset(
    data_path: Path = DEFAULT_DATA_PATH,
    n_rows: int = 1500,
    force_regenerate: bool = False,
) -> pd.DataFrame:
    """
    Load dataset/student_dataset.csv if it exists; otherwise generate it.
    `force_regenerate=True` overwrites an existing file (used for local
    experimentation, not wired into the retrain API endpoint).
    """
    data_path = Path(data_path)
    data_path.parent.mkdir(parents=True, exist_ok=True)

    if data_path.exists() and not force_regenerate:
        logger.info("Found existing dataset at %s — loading it.", data_path)
        df = pd.read_csv(data_path)
        missing = set(FEATURE_COLUMNS + [LABEL_COLUMN]) - set(df.columns)
        if missing:
            raise ValueError(
                f"Existing dataset at {data_path} is missing required columns: {sorted(missing)}"
            )
        return df

    logger.info("No dataset found at %s — generating %d synthetic rows.", data_path, n_rows)
    df = generate_synthetic_dataset(n_rows=n_rows)
    df.to_csv(data_path, index=False)
    logger.info("Synthetic dataset written to %s", data_path)
    return df


# ---------------------------------------------------------------------------
# 2. Modeling
# ---------------------------------------------------------------------------


@dataclass
class ModelResult:
    name: str
    accuracy: float
    precision: float
    recall: float
    f1: float
    pipeline: Pipeline

    def metrics_dict(self) -> dict[str, Any]:
        return {
            "model": self.name,
            "accuracy": round(self.accuracy, 4),
            "precision": round(self.precision, 4),
            "recall": round(self.recall, 4),
            "f1": round(self.f1, 4),
        }


def get_candidate_models() -> dict[str, Any]:
    """The four algorithms required by the spec, each with a fixed seed
    (where applicable) for reproducible evaluation runs."""
    return {
        "Random Forest": RandomForestClassifier(
            n_estimators=200, max_depth=None, random_state=RANDOM_SEED
        ),
        "Decision Tree": DecisionTreeClassifier(random_state=RANDOM_SEED),
        "Gaussian NB": GaussianNB(),
        "K-Nearest Neighbors": KNeighborsClassifier(n_neighbors=7),
    }


def train_and_evaluate_models(
    X_train: pd.DataFrame,
    X_test: pd.DataFrame,
    y_train: pd.Series,
    y_test: pd.Series,
) -> list[ModelResult]:
    """Fit each candidate inside a Pipeline(scaler -> classifier), score it
    on the held-out test split, and return all four results."""
    results: list[ModelResult] = []

    for name, estimator in get_candidate_models().items():
        pipeline = Pipeline(
            steps=[
                ("scaler", StandardScaler()),
                ("classifier", estimator),
            ]
        )
        pipeline.fit(X_train, y_train)
        y_pred = pipeline.predict(X_test)

        result = ModelResult(
            name=name,
            accuracy=accuracy_score(y_test, y_pred),
            precision=precision_score(y_test, y_pred, average="weighted", zero_division=0),
            recall=recall_score(y_test, y_pred, average="weighted", zero_division=0),
            f1=f1_score(y_test, y_pred, average="weighted", zero_division=0),
            pipeline=pipeline,
        )
        results.append(result)
        logger.info(
            "%-22s acc=%.4f  prec=%.4f  rec=%.4f  f1=%.4f",
            name,
            result.accuracy,
            result.precision,
            result.recall,
            result.f1,
        )

    return results


def select_champion(results: list[ModelResult]) -> ModelResult:
    """Highest weighted F1-score wins. Ties are broken by accuracy."""
    champion = max(results, key=lambda r: (r.f1, r.accuracy))
    logger.info("Champion model selected: %s (f1=%.4f)", champion.name, champion.f1)
    return champion


def build_production_pipeline(champion_name: str, X: pd.DataFrame, y: pd.Series) -> Pipeline:
    """
    Refit a fresh, identically-configured pipeline for the champion algorithm
    on the FULL dataset (train + test) so the deployed model benefits from
    every available row, not just the 70% training split used for scoring.
    """
    estimator = get_candidate_models()[champion_name]
    pipeline = Pipeline(
        steps=[
            ("scaler", StandardScaler()),
            ("classifier", estimator),
        ]
    )
    pipeline.fit(X, y)
    return pipeline


# ---------------------------------------------------------------------------
# 3. Persistence
# ---------------------------------------------------------------------------


def save_pipeline(pipeline: Pipeline, model_path: Path = DEFAULT_MODEL_PATH) -> None:
    model_path = Path(model_path)
    model_path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(pipeline, model_path)
    logger.info("Serialized production pipeline to %s", model_path)


def save_metrics(
    results: list[ModelResult],
    champion_name: str,
    metrics_path: Path = DEFAULT_METRICS_PATH,
    dataset_rows: int = 0,
) -> dict[str, Any]:
    metrics_path = Path(metrics_path)
    metrics_path.parent.mkdir(parents=True, exist_ok=True)

    payload = {
        "trained_at": datetime.now(timezone.utc).isoformat(),
        "dataset_rows": dataset_rows,
        "champion_model": champion_name,
        "models": [
            {**r.metrics_dict(), "is_champion": r.name == champion_name} for r in results
        ],
    }
    with open(metrics_path, "w") as f:
        json.dump(payload, f, indent=2)
    logger.info("Wrote model comparison metrics to %s", metrics_path)
    return payload


# ---------------------------------------------------------------------------
# 4. Orchestration
# ---------------------------------------------------------------------------


def run_pipeline(
    data_path: Path = DEFAULT_DATA_PATH,
    model_path: Path = DEFAULT_MODEL_PATH,
    metrics_path: Path = DEFAULT_METRICS_PATH,
    n_rows: int = 1500,
    force_regenerate: bool = False,
) -> dict[str, Any]:
    """
    Full end-to-end run: load/generate data -> split -> train & evaluate
    four models -> pick champion -> refit on full data -> serialize
    pipeline + metrics. Returns the same payload written to
    model_metrics.json so callers (e.g. the Django /api/retrain view) can
    use it without re-reading the file.
    """
    df = load_or_generate_dataset(data_path=data_path, n_rows=n_rows, force_regenerate=force_regenerate)

    X = df[FEATURE_COLUMNS]
    y = df[LABEL_COLUMN]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.3, random_state=RANDOM_SEED, stratify=y
    )
    logger.info(
        "Split dataset: %d train rows / %d test rows (stratified by label)",
        len(X_train),
        len(X_test),
    )

    results = train_and_evaluate_models(X_train, X_test, y_train, y_test)
    champion = select_champion(results)

    production_pipeline = build_production_pipeline(champion.name, X, y)
    save_pipeline(production_pipeline, model_path=model_path)
    metrics_payload = save_metrics(
        results, champion.name, metrics_path=metrics_path, dataset_rows=len(df)
    )

    return metrics_payload


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Train the student performance prediction pipeline.")
    parser.add_argument(
        "--data-path",
        type=str,
        default=str(DEFAULT_DATA_PATH),
        help="Path to dataset/student_dataset.csv (generated here if missing).",
    )
    parser.add_argument(
        "--model-dir",
        type=str,
        default=str(DEFAULT_MODEL_DIR),
        help="Directory to write student_model.pkl and model_metrics.json into.",
    )
    parser.add_argument(
        "--rows",
        type=int,
        default=1500,
        help="Number of synthetic rows to generate if the dataset does not exist.",
    )
    parser.add_argument(
        "--force-regenerate",
        action="store_true",
        help="Overwrite an existing dataset file with a freshly generated one.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    model_dir = Path(args.model_dir)

    results = run_pipeline(
        data_path=Path(args.data_path),
        model_path=model_dir / "student_model.pkl",
        metrics_path=model_dir / "model_metrics.json",
        n_rows=args.rows,
        force_regenerate=args.force_regenerate,
    )

    print("\n" + "=" * 60)
    print(f"Champion model : {results['champion_model']}")
    print(f"Dataset rows   : {results['dataset_rows']}")
    print("-" * 60)
    for m in results["models"]:
        flag = " <- champion" if m["is_champion"] else ""
        print(
            f"{m['model']:<22} acc={m['accuracy']:.4f}  prec={m['precision']:.4f}  "
            f"rec={m['recall']:.4f}  f1={m['f1']:.4f}{flag}"
        )
    print("=" * 60)


if __name__ == "__main__":
    main()
