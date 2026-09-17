from django.utils import timezone


def get_patient_dashboard_data(patient_user):
    """
    Aggregates real database metrics for the patient's dashboard (Correction 9).
    Never uses fake, hardcoded statistics.
    """
    from apps.appointments.models import Appointment
    from apps.medical_records.models import MedicalRecord, LabReport
    from apps.medicines.models import Medication
    from apps.predictions.models import DiseasePrediction

    now = timezone.now()

    upcoming_appointments = (
        Appointment.objects.filter(
            patient=patient_user,
            status__in=[Appointment.Status.SCHEDULED, Appointment.Status.CONFIRMED],
            starts_at__gte=now,
        )
        .select_related("doctor")
        .order_by("starts_at")
    )

    next_apt = upcoming_appointments.first()
    next_apt_data = None
    if next_apt:
        next_apt_data = {
            "id": next_apt.id,
            "doctor_name": f"{next_apt.doctor.first_name} {next_apt.doctor.last_name}".strip() or next_apt.doctor.email,
            "starts_at": next_apt.starts_at,
            "reason": next_apt.reason,
            "status": next_apt.status,
        }

    active_medications_count = Medication.objects.filter(
        patient=patient_user,
        is_active=True,
    ).count()

    total_records_count = MedicalRecord.objects.filter(patient=patient_user).count()
    total_reports_count = LabReport.objects.filter(patient=patient_user).count()
    total_predictions_count = DiseasePrediction.objects.filter(patient=patient_user).count()

    return {
        "upcoming_appointments_count": upcoming_appointments.count(),
        "next_appointment": next_apt_data,
        "active_medications_count": active_medications_count,
        "medical_records_count": total_records_count,
        "lab_reports_count": total_reports_count,
        "past_predictions_count": total_predictions_count,
    }
