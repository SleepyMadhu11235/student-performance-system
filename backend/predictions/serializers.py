from rest_framework import serializers

from .models import StudentPrediction


class StudentPredictionSerializer(serializers.ModelSerializer):
    class Meta:
        model = StudentPrediction
        fields = [
            "id",
            "student_id",
            "attendance_rate",
            "midterm_1",
            "midterm_2",
            "assignments_avg",
            "study_hours_weekly",
            "predicted_label",
            "confidence_score",
            "rule_based_explanation",
            "source",
            "created_at",
        ]
        read_only_fields = fields
