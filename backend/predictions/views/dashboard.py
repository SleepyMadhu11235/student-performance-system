from datetime import timedelta

from django.db.models import Avg, Count
from django.utils import timezone
from rest_framework.response import Response
from rest_framework.views import APIView

from predictions.models import StudentPrediction

AT_RISK_FEATURES = [
    ("Attendance", "attendance_rate"),
    ("Midterm 1", "midterm_1"),
    ("Midterm 2", "midterm_2"),
    ("Assignments", "assignments_avg"),
    ("Study Hrs", "study_hours_weekly"),
]

WEEKS_OF_TREND = 8


class DashboardView(APIView):
    """GET /api/dashboard — aggregate counts, rates, and chart-ready arrays."""

    def get(self, request):
        qs = StudentPrediction.objects.all()
        total = qs.count()

        counts = {label: 0 for label in StudentPrediction.Label.values}
        for row in qs.values("predicted_label").annotate(n=Count("id")):
            counts[row["predicted_label"]] = row["n"]

        pass_count = counts["Excellent"] + counts["Good"] + counts["Pass"]
        pass_rate = round(pass_count / total * 100, 1) if total else 0.0

        avg_confidence = qs.aggregate(avg=Avg("confidence_score"))["avg"] or 0
        avg_confidence = round(avg_confidence, 1)

        pie_data = [{"name": label, "value": counts[label]} for label in StudentPrediction.Label.values]

        bar_data = self._at_risk_feature_averages(qs)
        line_data = self._weekly_trend(qs)

        return Response(
            {
                "total": total,
                "pass_rate": pass_rate,
                "avg_confidence": avg_confidence,
                "counts": counts,
                "pie_data": pie_data,
                "bar_data": bar_data,
                "line_data": line_data,
            }
        )

    @staticmethod
    def _at_risk_feature_averages(qs):
        at_risk = qs.filter(predicted_label=StudentPrediction.Label.FAIL)
        agg_kwargs = {col: Avg(col) for _, col in AT_RISK_FEATURES}
        averages = at_risk.aggregate(**agg_kwargs)
        return [
            {"feature": display_name, "average": round(averages[col] or 0, 1)}
            for display_name, col in AT_RISK_FEATURES
        ]

    @staticmethod
    def _weekly_trend(qs):
        now = timezone.now()
        window_start = now - timedelta(days=WEEKS_OF_TREND * 7)
        recent = qs.filter(created_at__gte=window_start).values("created_at", "predicted_label")

        buckets = [
            {"week": f"Wk {WEEKS_OF_TREND - w}", **{label: 0 for label in StudentPrediction.Label.values}}
            for w in range(WEEKS_OF_TREND - 1, -1, -1)
        ]

        for row in recent:
            diff_weeks = (now - row["created_at"]).days // 7
            if 0 <= diff_weeks < WEEKS_OF_TREND:
                bucket_index = (WEEKS_OF_TREND - 1) - diff_weeks
                buckets[bucket_index][row["predicted_label"]] += 1

        return buckets
