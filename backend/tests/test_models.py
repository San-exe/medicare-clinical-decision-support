import pytest
from django.utils import timezone
from apps.accounts.models import User
from apps.patients.models import PatientProfile
from apps.doctors.models import DoctorProfile, ClinicalNote
from apps.appointments.models import Appointment
from apps.medical_records.models import MedicalRecord, LabReport, LabResult
from apps.medicines.models import Medication
from apps.predictions.models import DiseasePrediction, SymptomAnalysis
from apps.assistant.models import ChatConversation, ChatMessage
from apps.audit_logs.models import AuditLog


@pytest.mark.django_db
class TestModelRelationshipsAndIntegrity:
    def test_complete_relational_model_suite(self):
        # 1. Create Patient User & Profile
        patient_user = User.objects.create_user(
            email="rel.patient@medicare.local",
            password="Password123!",
            role=User.Roles.PATIENT,
        )
        patient_profile = PatientProfile.objects.create(
            user=patient_user,
            gender="Female",
            blood_group="B+",
        )
        assert patient_user.patient_profile == patient_profile

        # 2. Create Doctor User & Profile
        doctor_user = User.objects.create_user(
            email="rel.doctor@medicare.local",
            password="Password123!",
            role=User.Roles.DOCTOR,
            first_name="Stephen",
            last_name="Strange",
        )
        doctor_profile = DoctorProfile.objects.create(
            user=doctor_user,
            specialization="Neurology",
            hospital="Metro General",
        )
        assert doctor_user.doctor_profile == doctor_profile

        # 3. Appointment linking Patient & Doctor
        apt = Appointment.objects.create(
            patient=patient_user,
            doctor=doctor_user,
            starts_at=timezone.now() + timezone.timedelta(days=1),
            reason="Neurology consult",
        )
        assert apt.patient == patient_user
        assert apt.doctor == doctor_user

        # 4. Clinical Note
        note = ClinicalNote.objects.create(
            doctor=doctor_user,
            patient=patient_user,
            diagnosis="Migraine",
            note="Prescribed prophylactic medication.",
        )
        assert note.doctor == doctor_user
        assert note.patient == patient_user

        # 5. Medical Record
        record = MedicalRecord.objects.create(
            patient=patient_user,
            title="Brain MRI scan notes",
            recorded_at=timezone.now(),
        )
        assert record.patient == patient_user

        # 6. Lab Report & Lab Result
        report = LabReport.objects.create(
            patient=patient_user,
            title="Serum Electrolytes",
            file_type="pdf",
            file_size=1024,
        )
        result = LabResult.objects.create(
            report=report,
            test_name="Potassium",
            value="4.2",
            unit="mmol/L",
            reference_range="3.5-5.0",
        )
        assert result.report == report
        assert report.results.count() == 1

        # 7. Medication
        med = Medication.objects.create(
            patient=patient_user,
            prescribed_by=doctor_user,
            name="Propranolol",
            dosage="40mg",
            frequency="Daily",
        )
        assert med.patient == patient_user
        assert med.prescribed_by == doctor_user

        # 8. Prediction storage
        pred = DiseasePrediction.objects.create(
            patient=patient_user,
            model_name="cardiac_risk_xgboost",
            model_version="1.0.0",
            predicted_condition="Low Risk",
            confidence=0.89,
        )
        assert pred.patient == patient_user

        # 9. Symptom Analysis
        symptom = SymptomAnalysis.objects.create(
            patient=patient_user,
            symptoms_text="Severe throbbing headache with light sensitivity",
        )
        assert symptom.patient == patient_user

        # 10. Assistant Chat Conversation & Messages
        chat = ChatConversation.objects.create(
            user=patient_user,
            title="Questions about headaches",
        )
        msg1 = ChatMessage.objects.create(
            conversation=chat,
            role="user",
            content="What triggers migraines?",
        )
        msg2 = ChatMessage.objects.create(
            conversation=chat,
            role="assistant",
            content="Common triggers include stress, sleep changes, and dietary factors.",
        )
        assert chat.messages.count() == 2

        # 11. Audit Log
        audit = AuditLog.objects.create(
            user=patient_user,
            action=AuditLog.Actions.RECORD_CREATE,
            resource_type="MedicalRecord",
            resource_id=record.id,
        )
        assert audit.user == patient_user
