from django.contrib import admin
from .models import DiseasePrediction, SymptomAnalysis


@admin.register(DiseasePrediction)
class DiseasePredictionAdmin(admin.ModelAdmin):
    list_display = ("id", "patient", "model_name", "predicted_condition", "confidence", "created_at")
    list_filter = ("model_name", "created_at")
    search_fields = ("patient__email", "predicted_condition", "model_name")
    readonly_fields = ("created_at",)


@admin.register(SymptomAnalysis)
class SymptomAnalysisAdmin(admin.ModelAdmin):
    list_display = ("id", "patient", "created_at")
    search_fields = ("patient__email", "symptoms_text")
    readonly_fields = ("created_at",)
