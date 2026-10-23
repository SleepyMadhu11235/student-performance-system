"""
Deterministic, rule-based explanation for a prediction — explicitly NOT a
model-introspection technique like SHAP. It compares each input against its
own max, ranks them, and narrates the weakest/strongest relative to the
weight that feature carries in the scoring formula (imported directly from
the ML pipeline module so the two never drift apart).
"""

from __future__ import annotations

import sys
from pathlib import Path

# ml_pipeline lives one level up from predictions/services/ at the project root.
sys.path.append(str(Path(__file__).resolve().parent.parent.parent))

from ml_pipeline.train_pipeline import FEATURE_COLUMNS, SCORE_WEIGHTS  # noqa: E402

FEATURE_MAX = {
    "attendance_rate": 100,
    "midterm_1": 100,
    "midterm_2": 100,
    "assignments_avg": 100,
    "study_hours_weekly": 30,
}

FEATURE_DISPLAY_NAMES = {
    "attendance_rate": "Attendance",
    "midterm_1": "Midterm 1",
    "midterm_2": "Midterm 2",
    "assignments_avg": "Assignments",
    "study_hours_weekly": "Weekly study hours",
}


def _weight_tier(key: str) -> str:
    weight = SCORE_WEIGHTS[key]
    if weight >= 0.25:
        return "primary"
    if weight >= 0.15:
        return "supporting"
    return "minor"


def build_explanation(features: dict[str, float], predicted_label: str) -> str:
    ranked = sorted(
        FEATURE_COLUMNS,
        key=lambda key: features[key] / FEATURE_MAX[key],
    )
    weakest_key, strongest_key = ranked[0], ranked[-1]

    weakest_pct = round(features[weakest_key] / FEATURE_MAX[weakest_key] * 100)
    strongest_pct = round(features[strongest_key] / FEATURE_MAX[strongest_key] * 100)

    weakest_name = FEATURE_DISPLAY_NAMES[weakest_key]
    strongest_name = FEATURE_DISPLAY_NAMES[strongest_key]
    weakest_tier = _weight_tier(weakest_key)

    sentence_one = (
        f"This {predicted_label} prediction is most held back by {weakest_name.lower()} "
        f"at {weakest_pct}% of its maximum, the lowest of the five inputs, while "
        f"{strongest_name.lower()} at {strongest_pct}% is comparatively strong."
    )

    if weakest_tier == "primary":
        sentence_two = (
            f"{weakest_name} also carries a primary weight in the scoring model, "
            "so it's the highest-impact area to focus on."
        )
    elif weakest_tier == "supporting":
        sentence_two = (
            f"{weakest_name} carries a supporting weight in the scoring model — "
            "improving it would meaningfully shift the outcome."
        )
    else:
        sentence_two = (
            f"{weakest_name} carries only a minor weight in the scoring model, "
            "so it has limited influence on this outcome by itself."
        )

    return f"{sentence_one} {sentence_two}"
