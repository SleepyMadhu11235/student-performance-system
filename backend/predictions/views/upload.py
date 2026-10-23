import logging

from rest_framework import status
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView

from core.exceptions import AppError
from predictions.models import StudentPrediction
from predictions.services.csv_ingest import process_csv

logger = logging.getLogger("predictions")


class UploadCsvView(APIView):
    """POST /api/upload-csv — batch-predict a class roster CSV."""

    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        file_obj = request.FILES.get("file")
        if file_obj is None:
            raise AppError(
                "No file uploaded. Attach a .csv file under the 'file' field.",
                code="MISSING_FILE",
            )
        if not file_obj.name.lower().endswith(".csv"):
            raise AppError("Only .csv files are accepted.", code="INVALID_FILE_TYPE")

        result = process_csv(file_obj)
        instances = result.pop("instances")

        if instances:
            StudentPrediction.objects.bulk_create(instances)

        logger.info(
            "Bulk upload '%s': %d read, %d predicted, %d skipped",
            file_obj.name,
            result["rows_read"],
            result["predicted"],
            result["skipped"],
        )

        http_status = status.HTTP_201_CREATED if instances else status.HTTP_200_OK
        return Response(result, status=http_status)
