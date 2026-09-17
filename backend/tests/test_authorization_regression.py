import pytest
from django.utils import timezone
from rest_framework.test import APIClient
from rest_framework import status
from apps.accounts.models import User
from apps.patients.models import PatientProfile
from apps.doctors.models import DoctorProfile, ClinicalNote
from apps.appointments.models import Appointment
from apps.medicines.models import Medication
from core.permissions import doctor_can_access_patient


@pytest.mark.django_db
class TestAuthorizationEdgeCaseRegression:
    """
    Regression test suite verifying strict pre-creation authorization checks:
    1. A doctor cannot create clinical notes for an unauthorized patient.
    2. A doctor cannot prescribe medications for an unauthorized patient.
    3. An authorized doctor (with a valid relationship) can successfully create both.
    """

    @pytest.fixture(autouse=True)
    def setup_data(self):
        # Doctor A
        self.doctor_a = User.objects.create_user(
            email="doctor.a@medicare.local",
            password="Password123!",
            role=User.Roles.DOCTOR,
            first_name="Doctor",
            last_name="Alpha",
        )
        self.doc_profile_a = DoctorProfile.objects.create(
            user=self.doctor_a,
            license_number="MD-ALPHA-001",
            specialization="Cardiology",
        )

        # Patient B (no prior relationship or appointment with Doctor A)
        self.patient_b = User.objects.create_user(
            email="patient.b@medicare.local",
            password="Password123!",
            role=User.Roles.PATIENT,
            first_name="Patient",
            last_name="Beta",
        )
        self.patient_profile_b = PatientProfile.objects.create(
            user=self.patient_b,
            blood_group="B+",
            phone="9876543211",
        )

        self.client = APIClient()

    def test_doctor_cannot_create_clinical_note_for_unauthorized_patient(self):
        """
        Authenticates as Doctor A, attempts to POST a clinical note for Patient B
        (who has no appointment or prior relation with Doctor A), asserting HTTP 403 Forbidden.
        """
        # Ensure no prior authorization exists
        assert not doctor_can_access_patient(self.doctor_a, self.patient_b)

        self.client.force_authenticate(user=self.doctor_a)
        payload = {
            "diagnosis": "Acute Bronchitis",
            "note": "Patient reports severe cough and mild fever.",
        }
        res = self.client.post(
            f"/api/v1/doctor/patients/{self.patient_b.id}/clinical-notes/",
            payload,
            format="json",
        )

        assert res.status_code == status.HTTP_403_FORBIDDEN
        data = res.json()
        assert data["error"]["code"] == "PERMISSION_DENIED"
        assert "Doctor does not have active clinical authorization for this patient." in data["error"]["message"]

        # Ensure no clinical note was saved to the database
        assert not ClinicalNote.objects.filter(doctor=self.doctor_a, patient=self.patient_b).exists()

    def test_doctor_cannot_prescribe_medication_for_unauthorized_patient(self):
        """
        Authenticates as Doctor A, attempts to POST a prescription for Patient B,
        asserting HTTP 403 Forbidden.
        """
        # Ensure no prior authorization exists
        assert not doctor_can_access_patient(self.doctor_a, self.patient_b)

        self.client.force_authenticate(user=self.doctor_a)
        payload = {
            "patient_id": self.patient_b.id,
            "name": "Amoxicillin",
            "dosage": "500mg",
            "frequency": "Three times daily",
            "notes": "Take with meals",
        }
        res = self.client.post(
            "/api/v1/medicines/",
            payload,
            format="json",
        )

        assert res.status_code == status.HTTP_403_FORBIDDEN
        data = res.json()
        assert data["error"]["code"] == "PERMISSION_DENIED"
        assert "Doctor does not have active clinical authorization for this patient." in data["error"]["message"]

        # Ensure no medication was saved to the database
        assert not Medication.objects.filter(prescribed_by=self.doctor_a, patient=self.patient_b).exists()

    def test_doctor_can_create_clinical_note_and_medication_for_authorized_patient(self):
        """
        Establishes a valid clinical relationship via a confirmed appointment,
        and asserts HTTP 201 Created for both clinical notes and prescriptions.
        """
        # Establish valid relationship via confirmed appointment
        appointment = Appointment.objects.create(
            patient=self.patient_b,
            doctor=self.doctor_a,
            starts_at=timezone.now() + timezone.timedelta(days=1),
            status=Appointment.Status.CONFIRMED,
            reason="Cardiology consultation",
        )

        # Verify access helper now recognizes authorization
        assert doctor_can_access_patient(self.doctor_a, self.patient_b)

        self.client.force_authenticate(user=self.doctor_a)

        # 1. Create clinical note
        note_payload = {
            "diagnosis": "Mild Hypertension",
            "note": "Blood pressure slightly elevated at 135/88 mmHg. Advised dietary modifications.",
        }
        note_res = self.client.post(
            f"/api/v1/doctor/patients/{self.patient_b.id}/clinical-notes/",
            note_payload,
            format="json",
        )
        assert note_res.status_code == status.HTTP_201_CREATED
        assert ClinicalNote.objects.filter(doctor=self.doctor_a, patient=self.patient_b).exists()
        assert note_res.json()["diagnosis"] == "Mild Hypertension"

        # 2. Prescribe medication
        med_payload = {
            "patient_id": self.patient_b.id,
            "name": "Lisinopril",
            "dosage": "10mg",
            "frequency": "Once daily in the morning",
            "notes": "Monitor blood pressure weekly",
        }
        med_res = self.client.post(
            "/api/v1/medicines/",
            med_payload,
            format="json",
        )
        assert med_res.status_code == status.HTTP_201_CREATED
        assert Medication.objects.filter(prescribed_by=self.doctor_a, patient=self.patient_b).exists()
        assert med_res.json()["name"] == "Lisinopril"
