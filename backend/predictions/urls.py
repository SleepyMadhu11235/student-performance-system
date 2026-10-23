from django.urls import path

from predictions.views import (
    DashboardView,
    ExportCsvView,
    HistoryDetailView,
    HistoryListView,
    ModelsView,
    PredictView,
    RetrainView,
    UploadCsvView,
)

urlpatterns = [
    path("predict", PredictView.as_view(), name="predict"),
    path("upload-csv", UploadCsvView.as_view(), name="upload-csv"),
    path("history", HistoryListView.as_view(), name="history-list"),
    path("history/<int:pk>", HistoryDetailView.as_view(), name="history-detail"),
    path("dashboard", DashboardView.as_view(), name="dashboard"),
    path("models", ModelsView.as_view(), name="models"),
    path("retrain", RetrainView.as_view(), name="retrain"),
    path("export/csv", ExportCsvView.as_view(), name="export-csv"),
]
