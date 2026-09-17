import os
from django.conf import settings
from django.db import models
from core.utilities import generate_safe_filename


def report_upload_path(instance, filename):
    """Generates an unguessable safe server path for uploaded medical reports."""
    safe_name = generate_safe_filename(filename)
    return os.path.join("reports", "%Y", "%m", safe_name)


class MedicalRecord(models.Model):
    patient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="medical_records",
    )
    title = models.CharField(max_length=200)
    record_type = models.CharField(max_length=50, blank=True)
    description = models.TextField(blank=True)
    recorded_at = models.DateTimeField(db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-recorded_at"]
        indexes = [
            models.Index(fields=["patient", "-recorded_at"]),
        ]

    def __str__(self):
        return f"{self.title} ({self.patient.email})"


class LabReport(models.Model):
    patient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="lab_reports",
    )
    file = models.FileField(upload_to="reports/%Y/%m/")
    title = models.CharField(max_length=200, blank=True)
    file_type = models.CharField(max_length=50, blank=True)
    file_size = models.PositiveIntegerField(default=0)
    # Part 2 fields left blank for future AI processing
    extracted_text = models.TextField(blank=True)
    analysis_summary = models.TextField(blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ["-uploaded_at"]
        indexes = [
            models.Index(fields=["patient", "-uploaded_at"]),
        ]

    def __str__(self):
        return f"LabReport: {self.title or self.file.name} ({self.patient.email})"


class LabResult(models.Model):
    report = models.ForeignKey(
        LabReport,
        on_delete=models.CASCADE,
        related_name="results",
    )
    test_name = models.CharField(max_length=150)
    value = models.CharField(max_length=100)
    unit = models.CharField(max_length=50, blank=True)
    reference_range = models.CharField(max_length=100, blank=True)
    flag = models.CharField(max_length=30, blank=True)

    class Meta:
        ordering = ["test_name"]

    def __str__(self):
        return f"{self.test_name}: {self.value} {self.unit}"
