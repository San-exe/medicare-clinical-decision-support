from rest_framework.permissions import BasePermission


class IsAuthenticatedUser(BasePermission):
    """Verifies that the user is authenticated and active."""

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.is_active)


class IsPatient(BasePermission):
    """
    Allows access only to authenticated users with the 'patient' application role.
    """

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.is_active
            and getattr(request.user, "role", None) == "patient"
        )


class IsDoctor(BasePermission):
    """
    Allows access only to authenticated users with the 'doctor' application role.
    """

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.is_active
            and getattr(request.user, "role", None) == "doctor"
        )


class IsAdmin(BasePermission):
    """
    Allows access only to application administrators (role == 'admin').
    Django superuser is permitted as an explicit developer override.
    Per SRS Correction 3, Django 'is_staff' is NOT treated as application admin.
    """

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.is_active
            and (
                getattr(request.user, "role", None) == "admin"
                or getattr(request.user, "is_superuser", False)
            )
        )


class IsPatientOwner(BasePermission):
    """
    Object-level permission ensuring that patient records are strictly accessed
    only by the owning patient.
    """

    def has_object_permission(self, request, view, obj):
        user = request.user
        if not user or not user.is_authenticated:
            return False

        # Admin override
        if getattr(user, "role", None) == "admin" or getattr(user, "is_superuser", False):
            return True

        target_user = getattr(obj, "patient", None) or getattr(obj, "user", None)
        return target_user == user


def doctor_can_access_patient(doctor_user, patient_user):
    """
    Centralized authorization rule for Doctor-Patient access (Correction 4).
    Enforces that a doctor can only access a patient's information if:
      1. Doctor has a scheduled, confirmed, or completed appointment with the patient, OR
      2. Doctor has created clinical observations/notes for the patient, OR
      3. Doctor has prescribed medication for the patient.
    Centralized so Part 2 (reports, predictions, AI) reuses the exact same authority boundary.
    """
    if not doctor_user or not doctor_user.is_authenticated:
        return False
    if getattr(doctor_user, "role", None) != "doctor":
        return False
    if not patient_user:
        return False

    # Avoid circular imports by importing models lazily
    from apps.appointments.models import Appointment
    from apps.doctors.models import ClinicalNote
    from apps.medicines.models import Medication

    has_appointment = Appointment.objects.filter(
        doctor=doctor_user,
        patient=patient_user,
        status__in=["scheduled", "confirmed", "completed"],
    ).exists()

    if has_appointment:
        return True

    has_note = ClinicalNote.objects.filter(
        doctor=doctor_user,
        patient=patient_user,
    ).exists()

    if has_note:
        return True

    has_prescription = Medication.objects.filter(
        prescribed_by=doctor_user,
        patient=patient_user,
    ).exists()

    return has_prescription
