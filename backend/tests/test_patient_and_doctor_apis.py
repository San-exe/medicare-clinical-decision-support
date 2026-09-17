import pytest
from django.utils import timezone
from rest_framework.test import APIClient
from rest_framework import status
from apps.accounts.models import User
from apps.patients.models import PatientProfile
from apps.doctors.models import DoctorProfile, ClinicalNote
from apps.appointments.models import Appointment


@pytest.mark.django_db
class TestPatientAndDoctorAPIs:
    @pytest.fixture(autouse=True)
    def setup_data(self):
        self.patient = User.objects.create_user(
            email="patient.demo@medicare.local",
            password="Password123!",
            role=User.Roles.PATIENT,
        )
        self.patient_profile = PatientProfile.objects.create(
            user=self.patient,
            blood_group="O+",
            phone="9876543210",
        )

        self.doctor = User.objects.create_user(
            email="doctor.demo@medicare.local",
            password="Password123!",
            role=User.Roles.DOCTOR,
            first_name="Gregory",
            last_name="House",
        )
        self.doctor_profile = DoctorProfile.objects.create(
            user=self.doctor,
            specialization="Diagnostics",
            license_number="MD-12345",
        )
        self.client = APIClient()

    def test_patient_profile_get_and_patch(self):
        self.client.force_authenticate(user=self.patient)
        get_res = self.client.get("/api/v1/patient/profile/")
        assert get_res.status_code == status.HTTP_200_OK
        assert get_res.json()["blood_group"] == "O+"

        patch_res = self.client.patch("/api/v1/patient/profile/", {"blood_group": "A-"}, format="json")
        assert patch_res.status_code == status.HTTP_200_OK
        assert patch_res.json()["blood_group"] == "A-"

    def test_patient_dashboard_database_backed(self):
        self.client.force_authenticate(user=self.patient)
        res = self.client.get("/api/v1/patient/dashboard/")
        assert res.status_code == status.HTTP_200_OK
        data = res.json()
        assert "upcoming_appointments_count" in data
        assert "active_medications_count" in data
        assert "medical_records_count" in data
        assert data["upcoming_appointments_count"] == 0

    def test_appointment_booking_and_access(self):
        self.client.force_authenticate(user=self.patient)
        future_time = (timezone.now() + timezone.timedelta(days=2)).isoformat()
        payload = {
            "doctor_id": self.doctor.id,
            "starts_at": future_time,
            "reason": "Annual health checkup",
        }
        create_res = self.client.post("/api/v1/appointments/", payload, format="json")
        assert create_res.status_code == status.HTTP_201_CREATED
        apt_id = create_res.json()["id"]

        # Verify patient ownership
        apt = Appointment.objects.get(id=apt_id)
        assert apt.patient == self.patient
        assert apt.doctor == self.doctor

        # Doctor can see this appointment
        self.client.force_authenticate(user=self.doctor)
        doc_apt_res = self.client.get("/api/v1/doctor/appointments/")
        assert doc_apt_res.status_code == status.HTTP_200_OK
        assert doc_apt_res.json()["count"] >= 1

    def test_doctor_clinical_notes_and_insights(self):
        # Create an appointment establishing the authorization
        Appointment.objects.create(
            patient=self.patient,
            doctor=self.doctor,
            starts_at=timezone.now() + timezone.timedelta(days=1),
            status=Appointment.Status.CONFIRMED,
        )

        self.client.force_authenticate(user=self.doctor)

        # Record clinical note
        note_res = self.client.post(
            f"/api/v1/doctor/patients/{self.patient.id}/clinical-notes/",
            {"diagnosis": "Healthy", "note": "All vital signs within normal range."},
            format="json",
        )
        assert note_res.status_code == status.HTTP_201_CREATED
        assert ClinicalNote.objects.filter(doctor=self.doctor, patient=self.patient).exists()

        # Doctor insights endpoint
        insights_res = self.client.get("/api/v1/doctor/insights/")
        assert insights_res.status_code == status.HTTP_200_OK
        data = insights_res.json()
        assert data["total_patients"] >= 1
        assert data["clinical_notes_recorded"] >= 1
