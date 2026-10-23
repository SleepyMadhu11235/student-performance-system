from django.contrib import admin
from django.http import JsonResponse
from django.urls import include, path


def health_check(request):
    return JsonResponse(
        {
            "status": "ok",
            "service": "student-performance-system-backend",
            "message": "Student Performance Prediction API is running successfully.",
        }
    )


urlpatterns = [
    path("", health_check, name="root-health"),
    path("health", health_check, name="health"),
    path("api/health", health_check, name="api-health"),
    path("admin/", admin.site.urls),
    path("api/", include("predictions.urls")),
]
