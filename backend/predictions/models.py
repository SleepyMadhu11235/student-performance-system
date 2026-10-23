from django.db import models


class StudentPrediction(models.Model):
    """
    One row per prediction (single or bulk). Feature inputs are stored as
    individual columns — this keeps them queryable/aggregatable directly in
    MySQL for the dashboard endpoint — and are also exposed as a single
    JSON-shaped dict via `input_features` for the API layer.
    """

    class Label(models.TextChoices):
        EXCELLENT = "Excellent", "Excellent"
        GOOD = "Good", "Good"
        PASS = "Pass", "Pass"
        FAIL = "Fail", "Fail"

    class Source(models.TextChoices):
        SINGLE = "single", "Single"
        BULK = "bulk", "Bulk"

    student_id = models.CharField(max_length=32, db_index=True)

    attendance_rate = models.FloatField()
    midterm_1 = models.FloatField()
    midterm_2 = models.FloatField()
    assignments_avg = models.FloatField()
    study_hours_weekly = models.FloatField()

    predicted_label = models.CharField(max_length=16, choices=Label.choices, db_index=True)
    confidence_score = models.FloatField()
    rule_based_explanation = models.TextField(blank=True, default="")

    source = models.CharField(max_length=10, choices=Source.choices, default=Source.SINGLE)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["predicted_label", "created_at"]),
            models.Index(fields=["student_id"]),
        ]

    def __str__(self) -> str:
        return f"{self.student_id} -> {self.predicted_label} ({self.confidence_score}%)"

    @property
    def input_features(self) -> dict:
        return {
            "attendance_rate": self.attendance_rate,
            "midterm_1": self.midterm_1,
            "midterm_2": self.midterm_2,
            "assignments_avg": self.assignments_avg,
            "study_hours_weekly": self.study_hours_weekly,
        }
