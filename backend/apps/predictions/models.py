from django.conf import settings
from django.db import models


class DiseasePrediction(models.Model):
    patient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="disease_predictions",
    )
    model_name = models.CharField(max_length=100)
    model_version = models.CharField(max_length=50, blank=True)
    input_data = models.JSONField(default=dict)
    predicted_condition = models.CharField(max_length=200, blank=True)
    confidence = models.FloatField(null=True, blank=True)
    explanation = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["patient", "-created_at"]),
        ]

    def __str__(self):
        return f"Prediction for {self.patient.email}: {self.predicted_condition} ({self.created_at:%Y-%m-%d})"


class SymptomAnalysis(models.Model):
    patient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="symptom_analyses",
    )
    symptoms_text = models.TextField()
    result = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Symptom Analysis"
        verbose_name_plural = "Symptom Analyses"
        indexes = [
            models.Index(fields=["patient", "-created_at"]),
        ]

    def __str__(self):
        return f"SymptomAnalysis for {self.patient.email} at {self.created_at:%Y-%m-%d}"


# Canonical alias for Part 2 specification compatibility
DiseasePredictionHistory = DiseasePrediction

