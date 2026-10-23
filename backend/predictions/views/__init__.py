from predictions.views.dashboard import DashboardView
from predictions.views.export import ExportCsvView
from predictions.views.history import HistoryDetailView, HistoryListView
from predictions.views.model_info import ModelsView
from predictions.views.predict import PredictView
from predictions.views.retrain import RetrainView
from predictions.views.upload import UploadCsvView

__all__ = [
    "DashboardView",
    "ExportCsvView",
    "HistoryDetailView",
    "HistoryListView",
    "ModelsView",
    "PredictView",
    "RetrainView",
    "UploadCsvView",
]
