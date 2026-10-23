from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.views import APIView

from predictions.models import StudentPrediction
from predictions.serializers import StudentPredictionSerializer


class HistoryPagination(PageNumberPagination):
    """Standard offset-style pagination: ?page=2&page_size=25."""

    page_size = 10
    page_size_query_param = "page_size"
    max_page_size = 100


class HistoryListView(APIView):
    """GET /api/history — paginated, filterable by student_id and predicted_label."""

    def get(self, request):
        qs = StudentPrediction.objects.all()

        student_id = request.query_params.get("student_id")
        if student_id:
            qs = qs.filter(student_id__icontains=student_id.strip())

        predicted_label = request.query_params.get("predicted_label")
        if predicted_label:
            qs = qs.filter(predicted_label=predicted_label)

        paginator = HistoryPagination()
        page = paginator.paginate_queryset(qs, request, view=self)
        serializer = StudentPredictionSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)


class HistoryDetailView(APIView):
    """DELETE /api/history/<id> — remove a single prediction record."""

    def delete(self, request, pk):
        instance = get_object_or_404(StudentPrediction, pk=pk)
        instance.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
