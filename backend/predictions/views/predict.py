import logging
import uuid

from pydantic import ValidationError as PydanticValidationError
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from core.exceptions import AppError
from predictions.models import StudentPrediction
from predictions.schemas import PredictRequestSchema
from predictions.serializers import StudentPredictionSerializer
from predictions.services import ml_service
from predictions.services.explanation import build_explanation

logger = logging.getLogger("predictions")


class PredictView(APIView):
    """POST /api/predict — score a single student record."""

    def post(self, request):
        try:
            payload = PredictRequestSchema(**request.data)
        except PydanticValidationError as exc:
            raise AppError(
                "One or more fields failed validation.",
                code="VALIDATION_ERROR",
                http_status=status.HTTP_400_BAD_REQUEST,
                details=exc.errors(),
            )

        features = payload.model_dump(exclude={"student_id"})
        student_id = payload.student_id or f"STU-{uuid.uuid4().hex[:8].upper()}"

        result = ml_service.predict_one(features)
        explanation = build_explanation(features, result["predicted_label"])

        instance = StudentPrediction.objects.create(
            student_id=student_id,
            predicted_label=result["predicted_label"],
            confidence_score=result["confidence_score"],
            rule_based_explanation=explanation,
            source=StudentPrediction.Source.SINGLE,
            **features,
        )
        logger.info("Predicted %s for %s (confidence=%.1f%%)", instance.predicted_label, student_id, instance.confidence_score)

        serializer = StudentPredictionSerializer(instance)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
