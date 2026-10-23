import logging

from django.conf import settings
from pydantic import ValidationError as PydanticValidationError
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from core.exceptions import AppError
from predictions.schemas import RetrainRequestSchema
from predictions.services import ml_service

logger = logging.getLogger("predictions")


class RetrainView(APIView):
    """
    POST /api/retrain — re-run train_pipeline.py synchronously against the
    dataset on disk, then hot-swap the in-memory model so the very next
    prediction uses the freshly trained pipeline.

    Body (all optional): {"force_regenerate": false, "rows": 1500}
    """

    def post(self, request):
        try:
            payload = RetrainRequestSchema(**(request.data or {}))
        except PydanticValidationError as exc:
            raise AppError(
                "Invalid retrain options.",
                code="VALIDATION_ERROR",
                http_status=status.HTTP_400_BAD_REQUEST,
                details=exc.errors(),
            )

        # Imported lazily so a broken ml_pipeline import can't break Django startup.
        from ml_pipeline.train_pipeline import run_pipeline

        logger.info(
            "Retraining triggered via API (force_regenerate=%s, rows=%s)",
            payload.force_regenerate,
            payload.rows,
        )
        try:
            metrics = run_pipeline(
                data_path=settings.ML_DATASET_PATH,
                model_path=settings.ML_MODEL_PATH,
                metrics_path=settings.ML_METRICS_PATH,
                n_rows=payload.rows or 1500,
                force_regenerate=payload.force_regenerate,
            )
        except Exception:
            logger.exception("Retraining failed")
            raise AppError(
                "Retraining failed. Check server logs for details.",
                code="RETRAIN_FAILED",
                http_status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        ml_service.reload_pipeline()
        logger.info("Retraining complete. New champion: %s", metrics["champion_model"])
        return Response(metrics, status=status.HTTP_200_OK)
