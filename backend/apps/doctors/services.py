from django.utils import timezone
from apps.accounts.models import User
from apps.appointments.models import Appointment
from .models import ClinicalNote


def get_authorized_patients_for_doctor(doctor_user):
    """
    Returns queryset of Patients authorized to be accessed by this Doctor.
    Based on appointments, clinical notes, or medication prescriptions.
    """
    appointment_patient_ids = Appointment.objects.filter(
        doctor=doctor_user
    ).values_list("patient_id", flat=True)

    note_patient_ids = ClinicalNote.objects.filter(
        doctor=doctor_user
    ).values_list("patient_id", flat=True)

    from apps.medicines.models import Medication
    med_patient_ids = Medication.objects.filter(
        prescribed_by=doctor_user
    ).values_list("patient_id", flat=True)

    all_patient_ids = set(appointment_patient_ids) | set(note_patient_ids) | set(med_patient_ids)

    return User.objects.filter(
        id__in=all_patient_ids,
        role=User.Roles.PATIENT,
    ).select_related("patient_profile").order_by("first_name", "last_name")


def get_doctor_insights(doctor_user):
    """
    Calculates real database metrics for doctor insights (Correction 9).
    """
    now = timezone.now()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    today_end = now.replace(hour=23, minute=59, second=59, microsecond=999999)

    doctor_appointments = Appointment.objects.filter(doctor=doctor_user)
    today_appointments_count = doctor_appointments.filter(
        starts_at__range=(today_start, today_end)
    ).count()

    completed_appointments_count = doctor_appointments.filter(
        status=Appointment.Status.COMPLETED
    ).count()

    total_patients_count = get_authorized_patients_for_doctor(doctor_user).count()
    notes_count = ClinicalNote.objects.filter(doctor=doctor_user).count()

    return {
        "total_patients": total_patients_count,
        "today_appointments_count": today_appointments_count,
        "completed_appointments_count": completed_appointments_count,
        "total_appointments_count": doctor_appointments.count(),
        "clinical_notes_recorded": notes_count,
    }
