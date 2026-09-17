from django.urls import path
from .views import (
    MedicalRecordListCreateView,
    MedicalRecordDetailView,
    LabReportListView,
    LabReportUploadView,
    LabReportDetailView,
    MedicalRecordAnalyzeView,
)

urlpatterns = [
    path("", MedicalRecordListCreateView.as_view(), name="record-list-create"),
    path("<int:record_id>/", MedicalRecordDetailView.as_view(), name="record-detail"),
    path("<int:record_id>/analyze/", MedicalRecordAnalyzeView.as_view(), name="record-analyze"),
    path("reports/", LabReportListView.as_view(), name="report-list"),
    path("reports/upload/", LabReportUploadView.as_view(), name="report-upload"),
    path("reports/<int:report_id>/", LabReportDetailView.as_view(), name="report-detail"),
    path("reports/<int:record_id>/analyze/", MedicalRecordAnalyzeView.as_view(), name="report-analyze"),
]
