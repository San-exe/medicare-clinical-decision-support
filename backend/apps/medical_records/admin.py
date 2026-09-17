from django.contrib import admin
from .models import MedicalRecord, LabReport, LabResult


class LabResultInline(admin.TabularInline):
    model = LabResult
    extra = 0


@admin.register(MedicalRecord)
class MedicalRecordAdmin(admin.ModelAdmin):
    list_display = ("id", "patient", "title", "record_type", "recorded_at", "created_at")
    list_filter = ("record_type", "recorded_at")
    search_fields = ("patient__email", "title", "description")
    readonly_fields = ("created_at", "updated_at")


@admin.register(LabReport)
class LabReportAdmin(admin.ModelAdmin):
    list_display = ("id", "patient", "title", "file_type", "file_size", "uploaded_at")
    list_filter = ("file_type", "uploaded_at")
    search_fields = ("patient__email", "title", "file")
    readonly_fields = ("uploaded_at",)
    inlines = [LabResultInline]


@admin.register(LabResult)
class LabResultAdmin(admin.ModelAdmin):
    list_display = ("id", "report", "test_name", "value", "unit", "reference_range", "flag")
    search_fields = ("test_name", "report__patient__email")
