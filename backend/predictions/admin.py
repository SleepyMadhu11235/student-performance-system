from django.contrib import admin

from .models import StudentPrediction


@admin.register(StudentPrediction)
class StudentPredictionAdmin(admin.ModelAdmin):
    list_display = ("student_id", "predicted_label", "confidence_score", "source", "created_at")
    list_filter = ("predicted_label", "source")
    search_fields = ("student_id",)
    readonly_fields = [f.name for f in StudentPrediction._meta.fields]
    ordering = ("-created_at",)
