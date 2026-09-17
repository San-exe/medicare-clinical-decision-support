from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied, NotFound
from core.permissions import IsDoctor, doctor_can_access_patient, IsAuthenticatedUser
from core.pagination import StandardResultsSetPagination
from apps.accounts.models import User
from apps.appointments.models import Appointment
from apps.appointments.serializers import AppointmentSerializer
from apps.medical_records.models import MedicalRecord, LabReport
from apps.medical_records.serializers import MedicalRecordSerializer, LabReportSerializer
from apps.audit_logs.services import log_audit_event
from apps.audit_logs.models import AuditLog

from .models import DoctorProfile, ClinicalNote
from .serializers import (
    DoctorProfileSerializer,
    ClinicalNoteSerializer,
    DoctorPatientSummarySerializer,
)
from .services import get_authorized_patients_for_doctor, get_doctor_insights


def get_patient_or_404(patient_id):
    try:
        return User.objects.get(id=patient_id, role=User.Roles.PATIENT)
    except (User.DoesNotExist, ValueError):
        raise NotFound(f"Patient with ID {patient_id} does not exist.")


class DoctorProfileView(APIView):
    permission_classes = [IsDoctor]

    def get(self, request):
        profile, _ = DoctorProfile.objects.get_or_create(user=request.user)
        serializer = DoctorProfileSerializer(profile)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def patch(self, request):
        profile, _ = DoctorProfile.objects.get_or_create(user=request.user)
        serializer = DoctorProfileSerializer(profile, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)


class DoctorPublicListView(APIView):
    """
    GET /api/v1/doctor/list/
    Lists available doctors (id, full_name, specialization, license_number) for patient booking.
    """
    permission_classes = [IsAuthenticatedUser]

    def get(self, request):
        doctors = (
            User.objects.filter(role=User.Roles.DOCTOR, is_active=True)
            .select_related("doctor_profile")
            .order_by("last_name", "first_name")
        )
        data = []
        for doc in doctors:
            profile = getattr(doc, "doctor_profile", None)
            data.append({
                "id": doc.id,
                "email": doc.email,
                "first_name": doc.first_name,
                "last_name": doc.last_name,
                "name": f"Dr. {doc.first_name} {doc.last_name}".strip() or doc.email,
                "specialization": profile.specialization if profile else "General Medicine",
                "license_number": profile.license_number if profile else "",
                "experience_years": profile.experience_years if profile else 0,
            })
        return Response(data, status=status.HTTP_200_OK)


class PatientsView(APIView):
    """
    GET /api/v1/doctor/patients/
    Lists patients authorized for this doctor.
    """
    permission_classes = [IsDoctor]

    def get(self, request):
        patients = get_authorized_patients_for_doctor(request.user)
        paginator = StandardResultsSetPagination()
        page = paginator.paginate_queryset(patients, request)
        serializer = DoctorPatientSummarySerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)


class PatientDetailView(APIView):
    """
    GET /api/v1/doctor/patients/<id>/
    Retrieves authorized patient profile details.
    """
    permission_classes = [IsDoctor]

    def get(self, request, patient_id):
        patient = get_patient_or_404(patient_id)
        if not doctor_can_access_patient(request.user, patient):
            raise PermissionDenied("You are not authorized to view this patient's records.")
        serializer = DoctorPatientSummarySerializer(patient)
        return Response(serializer.data, status=status.HTTP_200_OK)


class PatientRecordsView(APIView):
    """
    GET /api/v1/doctor/patients/<id>/records/
    Retrieves authorized patient's medical records.
    """
    permission_classes = [IsDoctor]

    def get(self, request, patient_id):
        patient = get_patient_or_404(patient_id)
        if not doctor_can_access_patient(request.user, patient):
            raise PermissionDenied("You are not authorized to view this patient's records.")

        records = MedicalRecord.objects.filter(patient=patient).order_by("-recorded_at")
        paginator = StandardResultsSetPagination()
        page = paginator.paginate_queryset(records, request)
        serializer = MedicalRecordSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)


class PatientReportsView(APIView):
    """
    GET /api/v1/doctor/patients/<id>/reports/
    Retrieves authorized patient's lab reports.
    """
    permission_classes = [IsDoctor]

    def get(self, request, patient_id):
        patient = get_patient_or_404(patient_id)
        if not doctor_can_access_patient(request.user, patient):
            raise PermissionDenied("You are not authorized to view this patient's reports.")

        reports = LabReport.objects.filter(patient=patient).prefetch_related("results").order_by("-uploaded_at")
        paginator = StandardResultsSetPagination()
        page = paginator.paginate_queryset(reports, request)
        serializer = LabReportSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)


class PatientClinicalNotesView(APIView):
    """
    POST /api/v1/doctor/patients/<id>/clinical-notes/
    Creates a clinical observation/note for an authorized patient.
    """
    permission_classes = [IsDoctor]

    def get(self, request, patient_id):
        patient = get_patient_or_404(patient_id)
        if not doctor_can_access_patient(request.user, patient):
            raise PermissionDenied("You are not authorized to view this patient's clinical notes.")
        notes = ClinicalNote.objects.filter(doctor=request.user, patient=patient).order_by("-created_at")
        serializer = ClinicalNoteSerializer(notes, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request, patient_id):
        patient = get_patient_or_404(patient_id)
        if not doctor_can_access_patient(request.user, patient):
            raise PermissionDenied("Doctor does not have active clinical authorization for this patient.")

        note_text = request.data.get("note", "").strip()
        diagnosis = request.data.get("diagnosis", "").strip()

        if not note_text:
            return Response(
                {"error": {"code": "VALIDATION_ERROR", "message": "Clinical note content cannot be empty."}},
                status=status.HTTP_400_BAD_REQUEST,
            )

        note = ClinicalNote.objects.create(
            doctor=request.user,
            patient=patient,
            diagnosis=diagnosis,
            note=note_text,
        )

        log_audit_event(
            user=request.user,
            action=AuditLog.Actions.CLINICAL_NOTE_CREATE,
            resource_type="ClinicalNote",
            resource_id=note.id,
            request=request,
            metadata={"patient_id": patient.id},
        )

        serializer = ClinicalNoteSerializer(note)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class AppointmentsView(APIView):
    """
    GET /api/v1/doctor/appointments/
    Lists appointments scheduled with this doctor.
    """
    permission_classes = [IsDoctor]

    def get(self, request):
        appointments = (
            Appointment.objects.filter(doctor=request.user)
            .select_related("patient", "doctor")
            .order_by("starts_at")
        )
        paginator = StandardResultsSetPagination()
        page = paginator.paginate_queryset(appointments, request)
        serializer = AppointmentSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)


class InsightsView(APIView):
    """
    GET /api/v1/doctor/insights/
    Returns real database metrics for doctor decision support.
    """
    permission_classes = [IsDoctor]

    def get(self, request):
        insights = get_doctor_insights(request.user)
        return Response(insights, status=status.HTTP_200_OK)
