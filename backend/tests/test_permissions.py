import pytest
from django.utils import timezone
from rest_framework.test import APIClient
from rest_framework import status
from apps.accounts.models import User
from apps.patients.models import PatientProfile
from apps.doctors.models import DoctorProfile
from apps.appointments.models import Appointment
from apps.medical_records.models import MedicalRecord


@pytest.mark.django_db
class TestPermissionsAndAuthorization:
    @pytest.fixture(autouse=True)
    def setup_users(self):
        self.patient_a = User.objects.create_user(
            email="patienta@medicare.local",
            password="Password123!",
            role=User.Roles.PATIENT,
        )
        self.profile_a = PatientProfile.objects.create(user=self.patient_a)

        self.patient_b = User.objects.create_user(
            email="patientb@medicare.local",
            password="Password123!",
            role=User.Roles.PATIENT,
        )
        self.profile_b = PatientProfile.objects.create(user=self.patient_b)

        self.doctor_1 = User.objects.create_user(
            email="doctor1@medicare.local",
            password="Password123!",
            role=User.Roles.DOCTOR,
        )
        self.doc_profile_1 = DoctorProfile.objects.create(
            user=self.doctor_1,
            license_number="LIC-DOC-001",
        )

        self.doctor_unauthorized = User.objects.create_user(
            email="doctor2@medicare.local",
            password="Password123!",
            role=User.Roles.DOCTOR,
        )
        self.doc_profile_2 = DoctorProfile.objects.create(
            user=self.doctor_unauthorized,
            license_number="LIC-DOC-002",
        )

        self.admin_user = User.objects.create_user(
            email="admin@medicare.local",
            password="Password123!",
            role=User.Roles.ADMIN,
        )

        self.staff_only_user = User.objects.create_user(
            email="staffonly@medicare.local",
            password="Password123!",
            role=User.Roles.PATIENT,
            is_staff=True,  # is_staff without role=admin (Correction 3)
        )

        self.client = APIClient()

    def test_patient_cannot_access_doctor_endpoints(self):
        self.client.force_authenticate(user=self.patient_a)
        res = self.client.get("/api/v1/doctor/patients/")
        assert res.status_code == status.HTTP_403_FORBIDDEN

    def test_doctor_cannot_access_admin_endpoints(self):
        self.client.force_authenticate(user=self.doctor_1)
        res = self.client.get("/api/v1/admin/users/")
        assert res.status_code == status.HTTP_403_FORBIDDEN

    def test_is_staff_alone_does_not_grant_app_admin_access(self):
        # Correction 3: is_staff alone does not equal role=admin
        self.client.force_authenticate(user=self.staff_only_user)
        res = self.client.get("/api/v1/admin/users/")
        assert res.status_code == status.HTTP_403_FORBIDDEN

    def test_app_admin_can_access_admin_endpoints(self):
        self.client.force_authenticate(user=self.admin_user)
        res = self.client.get("/api/v1/admin/users/")
        assert res.status_code == status.HTTP_200_OK

    def test_patient_data_isolation(self):
        # Patient A creates a medical record
        record = MedicalRecord.objects.create(
            patient=self.patient_a,
            title="Private Record of Patient A",
            recorded_at=timezone.now(),
        )

        # Patient B attempts to retrieve Patient A's record directly
        self.client.force_authenticate(user=self.patient_b)
        res = self.client.get(f"/api/v1/records/{record.id}/")
        assert res.status_code == status.HTTP_403_FORBIDDEN

    def test_doctor_patient_authorization_boundary(self):
        # Correction 4: Doctor without relationship cannot view patient B's details
        self.client.force_authenticate(user=self.doctor_unauthorized)
        res = self.client.get(f"/api/v1/doctor/patients/{self.patient_b.id}/")
        assert res.status_code == status.HTTP_403_FORBIDDEN

        # Create scheduled appointment establishing relationship for doctor 1
        Appointment.objects.create(
            patient=self.patient_b,
            doctor=self.doctor_1,
            starts_at=timezone.now() + timezone.timedelta(days=1),
            status=Appointment.Status.SCHEDULED,
        )

        # Now doctor 1 is authorized
        self.client.force_authenticate(user=self.doctor_1)
        auth_res = self.client.get(f"/api/v1/doctor/patients/{self.patient_b.id}/")
        assert auth_res.status_code == status.HTTP_200_OK

    def test_comprehensive_multi_tenant_isolation(self):
        from apps.medical_records.models import LabReport
        from apps.medicines.models import Medication
        from apps.predictions.models import DiseasePrediction

        # 1. Provision private resources for Patient A
        rec_a = MedicalRecord.objects.create(
            patient=self.patient_a,
            title="Private Record of Patient A",
            recorded_at=timezone.now(),
        )
        rep_a = LabReport.objects.create(
            patient=self.patient_a,
            title="Private Lab Report",
            file="reports/private_a.pdf",
            file_size=1024,
            file_type="application/pdf",
        )
        apt_a = Appointment.objects.create(
            patient=self.patient_a,
            doctor=self.doctor_1,
            starts_at=timezone.now() + timezone.timedelta(days=7),
            status=Appointment.Status.SCHEDULED,
        )
        med_a = Medication.objects.create(
            patient=self.patient_a,
            name="Confidential Med",
            dosage="20mg",
            frequency="Daily",
        )
        pred_a = DiseasePrediction.objects.create(
            patient=self.patient_a,
            model_name="xgboost",
            model_version="2.0.0",
            predicted_condition="Type 2 Diabetes",
            confidence=0.91,
        )

        # 2. Patient B attempts to directly access or mutate Patient A's resources
        self.client.force_authenticate(user=self.patient_b)

        # Detail endpoints must return 403 Forbidden
        assert self.client.get(f"/api/v1/records/{rec_a.id}/").status_code == status.HTTP_403_FORBIDDEN
        assert self.client.get(f"/api/v1/records/reports/{rep_a.id}/").status_code == status.HTTP_403_FORBIDDEN
        assert self.client.get(f"/api/v1/patient/appointments/{apt_a.id}/").status_code == status.HTTP_403_FORBIDDEN
        assert self.client.patch(f"/api/v1/patient/appointments/{apt_a.id}/", {"notes": "Tampered"}).status_code == status.HTTP_403_FORBIDDEN
        assert self.client.get(f"/api/v1/medicines/{med_a.id}/").status_code == status.HTTP_403_FORBIDDEN

        # List endpoints for Patient B must isolate data (count == 0)
        assert self.client.get("/api/v1/records/").json().get("count", 0) == 0
        assert self.client.get("/api/v1/patient/medical-records/").json().get("count", 0) == 0
        assert self.client.get("/api/v1/records/reports/").json().get("count", 0) == 0
        assert self.client.get("/api/v1/patient/lab-tests/").json().get("count", 0) == 0
        assert self.client.get("/api/v1/patient/appointments/").json().get("count", 0) == 0
        assert self.client.get("/api/v1/medicines/").json().get("count", 0) == 0
        assert self.client.get("/api/v1/patient/medications/").json().get("count", 0) == 0
        assert self.client.get("/api/v1/predictions/").json().get("count", 0) == 0
        assert self.client.get("/api/v1/patient/predictions/").json().get("count", 0) == 0

        # Profile retrieval must strictly return Patient B's identity
        profile_res = self.client.get("/api/v1/patient/profile/")
        assert profile_res.status_code == status.HTTP_200_OK
        assert profile_res.json()["email"] == self.patient_b.email

        # 3. Unauthorized doctor attempts to query Patient A's filtered data
        self.client.force_authenticate(user=self.doctor_unauthorized)
        assert self.client.get(f"/api/v1/doctor/patients/{self.patient_a.id}/").status_code == status.HTTP_403_FORBIDDEN
        assert self.client.get(f"/api/v1/doctor/patients/{self.patient_a.id}/records/").status_code == status.HTTP_403_FORBIDDEN
        assert self.client.get(f"/api/v1/doctor/patients/{self.patient_a.id}/reports/").status_code == status.HTTP_403_FORBIDDEN
        assert self.client.get(f"/api/v1/records/?patient_id={self.patient_a.id}").status_code == status.HTTP_403_FORBIDDEN
        assert self.client.get(f"/api/v1/records/reports/?patient_id={self.patient_a.id}").status_code == status.HTTP_403_FORBIDDEN
        assert self.client.get(f"/api/v1/medicines/?patient_id={self.patient_a.id}").status_code == status.HTTP_403_FORBIDDEN
        assert self.client.get(f"/api/v1/predictions/?patient_id={self.patient_a.id}").status_code == status.HTTP_403_FORBIDDEN

