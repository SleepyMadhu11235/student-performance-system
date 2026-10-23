import json

from django.conf import settings
from rest_framework.response import Response
from rest_framework.views import APIView

from core.exceptions import AppError


class ModelsView(APIView):
    """GET /api/models — the four-way algorithm comparison from the last training run."""

    def get(self, request):
        metrics_path = settings.ML_METRICS_PATH
        if not metrics_path.exists():
            raise AppError(
                f"No trained model metrics found at {metrics_path}. "
                "Run train_pipeline.py or POST /api/retrain first.",
                code="METRICS_NOT_FOUND",
                http_status=503,
            )
        with open(metrics_path) as f:
            payload = json.load(f)
        return Response(payload)
