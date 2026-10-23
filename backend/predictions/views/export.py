import csv

from django.http import StreamingHttpResponse
from rest_framework.views import APIView

from predictions.models import StudentPrediction

EXPORT_COLUMNS = [
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


class _Echo:
    """File-like object whose write() just returns the string it was given —
    the standard trick for streaming CSV rows without buffering the whole
    response body in memory."""

    def write(self, value):
        return value


class ExportCsvView(APIView):
    """GET /api/export/csv — stream the (optionally filtered) history table as a CSV download."""

    def get(self, request):
        qs = StudentPrediction.objects.all()

        student_id = request.query_params.get("student_id")
        if student_id:
            qs = qs.filter(student_id__icontains=student_id.strip())

        predicted_label = request.query_params.get("predicted_label")
        if predicted_label:
            qs = qs.filter(predicted_label=predicted_label)

        writer = csv.writer(_Echo())

        def row_generator():
            yield writer.writerow(EXPORT_COLUMNS)
            for row in qs.iterator():
                yield writer.writerow(
                    [
                        row.id,
                        row.student_id,
                        row.attendance_rate,
                        row.midterm_1,
                        row.midterm_2,
                        row.assignments_avg,
                        row.study_hours_weekly,
                        row.predicted_label,
                        row.confidence_score,
                        row.rule_based_explanation,
                        row.source,
                        row.created_at.isoformat(),
                    ]
                )

        response = StreamingHttpResponse(row_generator(), content_type="text/csv")
        response["Content-Disposition"] = 'attachment; filename="prediction-history.csv"'
        return response
