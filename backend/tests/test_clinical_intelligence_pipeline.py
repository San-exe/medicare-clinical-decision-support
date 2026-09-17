import io
import zlib
import pytest
from unittest.mock import patch, MagicMock
import requests
from django.utils import timezone
from rest_framework.test import APIClient
from rest_framework import status

from apps.accounts.models import User
from apps.patients.models import PatientProfile
from apps.doctors.models import DoctorProfile
from apps.appointments.models import Appointment
from apps.medicines.models import Medication
from apps.medical_records.models import LabReport, LabResult
from apps.medicines.services.interaction_service import interaction_service
from apps.medical_records.services.report_parser import (
    extract_text_from_stream,
    parse_report_content,
    classify_potassium,
    classify_sodium,
)
from integrations.drugbank_client import DrugBankClient, drugbank_client
from ai.rag_service import answer_with_evidence


@pytest.mark.django_db
class TestClinicalIntelligencePipeline:
    """
    Comprehensive test suite for Person 2 scope:
    - DrugBank adapter credentials handling and uncredentialed safety
    - Medicine interactions workflow (pairwise and patient-grounded)
    - Doctor-patient authorization boundaries on clinical medication queries
    - PDF FlateDecode decompressed stream parsing
    - OCR image graceful handling
    - AI RAG orchestration boundary
    - Extended clinical electrolytes and lab classification
    """

    @pytest.fixture(autouse=True)
    def setup_data(self):
        self.patient = User.objects.create_user(
            email="patient.intel@medicare.local",
            password="Password123!",
            role=User.Roles.PATIENT,
            first_name="Alice",
            last_name="Intel",
        )
        self.patient_profile = PatientProfile.objects.create(user=self.patient)

        self.patient_other = User.objects.create_user(
            email="patient.other@medicare.local",
            password="Password123!",
            role=User.Roles.PATIENT,
            first_name="Bob",
            last_name="Other",
        )
        self.patient_other_profile = PatientProfile.objects.create(user=self.patient_other)

        self.doctor_auth = User.objects.create_user(
            email="doc.auth@medicare.local",
            password="Password123!",
            role=User.Roles.DOCTOR,
            first_name="Gregory",
            last_name="House",
        )
        self.doc_profile_auth = DoctorProfile.objects.create(
            user=self.doctor_auth,
            license_number="LIC-AUTH-999",
            specialization="Internal Medicine",
        )

        self.doctor_unauth = User.objects.create_user(
            email="doc.unauth@medicare.local",
            password="Password123!",
            role=User.Roles.DOCTOR,
            first_name="Unauth",
            last_name="Doctor",
        )
        self.doc_profile_unauth = DoctorProfile.objects.create(
            user=self.doctor_unauth,
            license_number="LIC-UNAUTH-000",
            specialization="Dermatology",
        )

        # Active appointment linking Doctor Auth to Patient
        Appointment.objects.create(
            doctor=self.doctor_auth,
            patient=self.patient,
            status=Appointment.Status.CONFIRMED,
            starts_at=timezone.now() + timezone.timedelta(days=2),
        )

        # Active medication for Patient: Warfarin
        self.med_warfarin = Medication.objects.create(
            patient=self.patient,
            prescribed_by=self.doctor_auth,
            name="Warfarin",
            dosage="5mg",
            frequency="Once daily",
            is_active=True,
        )

        self.client = APIClient()

    # -------------------------------------------------------------------------
    # 1. DrugBank Adapter Tests
    # -------------------------------------------------------------------------

    def test_drugbank_unconfigured_safe_fallback(self):
        client = DrugBankClient(api_key="")
        assert not client.is_configured

        res_info = client.get_drug_info("aspirin")
        assert res_info["status"] == "unavailable"
        assert res_info["configured"] is False
        assert "DRUGBANK_API_KEY" in res_info["message"]

        res_int = client.check_interactions(["warfarin", "aspirin"])
        assert res_int["status"] == "unavailable"
        assert res_int["configured"] is False

    @patch("requests.get")
    def test_drugbank_configured_mocked_success(self, mock_get):
        client = DrugBankClient(api_key="mock-valid-key-xyz")
        assert client.is_configured

        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "drugs": [
                {
                    "drugbank_id": "DB00945",
                    "name": "Aspirin",
                    "description": "Analgesic and antiplatelet agent.",
                    "indication": "Treatment of mild to moderate pain and fever.",
                }
            ]
        }
        mock_get.return_value = mock_resp

        res = client.get_drug_info("aspirin")
        assert res["status"] == "success"
        assert res["drugbank_id"] == "DB00945"
        assert "Antiplatelet" in res["description"] or "Analgesic" in res["description"]

        headers = mock_get.call_args[1].get("headers", {})
        assert headers.get("Authorization") == "mock-valid-key-xyz"

    @patch("requests.get")
    def test_drugbank_timeout_graceful_handling(self, mock_get):
        client = DrugBankClient(api_key="mock-key")
        mock_get.side_effect = requests.Timeout("Connection timed out")

        res = client.get_drug_info("ibuprofen")
        assert res["status"] == "timeout"
        assert res["configured"] is True
        assert "timed out" in res["message"].lower()

    # -------------------------------------------------------------------------
    # 2. Canonical Medicine Interactions Workflow Tests
    # -------------------------------------------------------------------------

    @patch("apps.medicines.services.openfda_service.OpenFDAService.check_interactions")
    def test_interaction_service_pairwise_explicit_drugs(self, mock_check):
        mock_check.return_value = {
            "status": "success",
            "interactions_found": [
                {
                    "drug_a": "Warfarin",
                    "drug_b": "Aspirin",
                    "severity": "high",
                    "description": "Risk of severe hemorrhage and gastrointestinal bleeding.",
                    "source_id": "FDA-LBL-001",
                }
            ],
            "total_interactions": 1,
            "cached": False,
        }

        result = interaction_service.evaluate_interactions(drugs=["Warfarin", "Aspirin"])
        assert result["status"] == "success"
        assert result["total_interactions"] == 1
        assert result["has_critical_interaction"] is True
        interaction = result["interactions"][0]
        assert "Warfarin" in (interaction["drug_a"], interaction["drug_b"])
        assert "Aspirin" in (interaction["drug_a"], interaction["drug_b"])
        assert interaction["severity"] == "high"

    @patch("apps.medicines.services.openfda_service.OpenFDAService.check_interactions")
    def test_interaction_service_with_patient_active_medications(self, mock_check):
        mock_check.return_value = {
            "status": "success",
            "interactions_found": [
                {
                    "drug_a": "Warfarin",
                    "drug_b": "Aspirin",
                    "severity": "high",
                    "description": "Increased bleeding risk.",
                }
            ],
        }

        # Query single medication "Aspirin" against patient (who is taking "Warfarin")
        result = interaction_service.evaluate_interactions(
            queried_drug="Aspirin",
            patient_user=self.patient,
        )
        assert result["patient_id"] == self.patient.id
        assert result["patient_medications_loaded"] >= 1
        assert "Aspirin" in result["drugs_analyzed"]
        assert "Warfarin" in result["drugs_analyzed"]
        assert result["total_interactions"] == 1

    # -------------------------------------------------------------------------
    # 3. REST API Interaction Endpoint & Authorization Boundary Tests
    # -------------------------------------------------------------------------

    @patch("apps.medicines.services.openfda_service.OpenFDAService.check_interactions")
    def test_patient_can_query_own_drug_interactions(self, mock_check):
        mock_check.return_value = {"status": "success", "interactions_found": []}

        self.client.force_authenticate(user=self.patient)
        payload = {"queried_drug": "Metformin"}
        res = self.client.post("/api/v1/medicines/interactions/", payload, format="json")

        assert res.status_code == status.HTTP_200_OK
        data = res.json()
        assert data["patient_id"] == self.patient.id
        assert "Metformin" in data["drugs_analyzed"]
        assert "Warfarin" in data["drugs_analyzed"]

    def test_patient_cannot_query_another_patients_medication_interactions(self):
        self.client.force_authenticate(user=self.patient)
        payload = {"queried_drug": "Metformin", "patient_id": self.patient_other.id}
        res = self.client.post("/api/v1/medicines/interactions/", payload, format="json")

        assert res.status_code == status.HTTP_403_FORBIDDEN
        assert "Patients cannot access another patient's medication" in res.json()["error"]["message"]

    def test_doctor_without_relationship_cannot_query_patient_interactions(self):
        self.client.force_authenticate(user=self.doctor_unauth)
        payload = {"queried_drug": "Metformin", "patient_id": self.patient.id}
        res = self.client.post("/api/v1/medicines/interactions/", payload, format="json")

        assert res.status_code == status.HTTP_403_FORBIDDEN
        assert "Doctor does not have active clinical authorization" in res.json()["error"]["message"]

    @patch("apps.medicines.services.openfda_service.OpenFDAService.check_interactions")
    def test_authorized_doctor_can_query_patient_interactions(self, mock_check):
        mock_check.return_value = {"status": "success", "interactions_found": []}

        self.client.force_authenticate(user=self.doctor_auth)
        payload = {"queried_drug": "Ibuprofen", "patient_id": self.patient.id}
        res = self.client.post("/api/v1/medicines/interactions/", payload, format="json")

        assert res.status_code == status.HTTP_200_OK
        data = res.json()
        assert data["patient_id"] == self.patient.id
        assert "Ibuprofen" in data["drugs_analyzed"]
        assert "Warfarin" in data["drugs_analyzed"]

    # -------------------------------------------------------------------------
    # 4. PDF FlateDecode Stream Text Extraction Tests
    # -------------------------------------------------------------------------

    def test_pdf_flatedecode_stream_decompression(self):
        # Construct synthetic PDF byte stream with FlateDecode compressed content
        stream_raw_text = b"BT /F1 12 Tf (Fasting Blood Glucose: 110 mg/dL) Tj ET\nBT (Serum Creatinine: 1.4 mg/dL) Tj ET"
        compressed_stream = zlib.compress(stream_raw_text)

        pdf_bytes = (
            b"%PDF-1.4\n"
            b"1 0 obj\n"
            b"<< /Length " + str(len(compressed_stream)).encode("ascii") + b" /Filter /FlateDecode >>\n"
            b"stream\n" + compressed_stream + b"\nendstream\n"
            b"endobj\n"
            b"%%EOF"
        )

        extracted = extract_text_from_stream(pdf_bytes, file_type="pdf")
        assert "Fasting Blood Glucose: 110 mg/dL" in extracted
        assert "Serum Creatinine: 1.4 mg/dL" in extracted

        # Run parser on decompressed PDF text
        analysis = parse_report_content(pdf_bytes, title="Lab Stream Test", file_type="pdf")
        assert analysis["total_metrics_extracted"] == 2
        metrics_by_name = {m["test_name"]: m for m in analysis["metrics"]}
        assert metrics_by_name["Fasting Blood Glucose"]["flag"] == "elevated"
        assert metrics_by_name["Serum Creatinine"]["flag"] == "high"

    # -------------------------------------------------------------------------
    # 5. Image OCR Graceful Degradation Tests
    # -------------------------------------------------------------------------

    def test_image_ocr_graceful_fallback(self):
        # Valid 1x1 PNG header + data
        png_bytes = (
            b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR"
            b"\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89"
            b"\x00\x00\x00\rIDATx\x9cc`\x00\x00\x00\x02\x00\x01H\xaf\xa4q"
            b"\x00\x00\x00\x00IEND\xaeB`\x82"
        )

        analysis = parse_report_content(png_bytes, title="Scanned Image Report", file_type="png")
        # Should gracefully return without raising unhandled exceptions
        assert "extracted_text" in analysis
        assert "metrics" in analysis
        assert analysis["ocr_status"] in ("unavailable", "empty", "success", "failed")

    # -------------------------------------------------------------------------
    # 6. AI RAG Boundary & Extractive Fallback Tests
    # -------------------------------------------------------------------------

    @patch("apps.assistant.services.pubmed_service.pubmed_service.search_pubmed")
    def test_answer_with_evidence_functional_boundary(self, mock_search):
        mock_search.return_value = {
            "status": "success",
            "citations": [
                {
                    "pmid": "33481280",
                    "title": "Evidence-Based Clinical Decision Support Systems",
                    "journal": "Lancet Digital Health",
                    "year": "2021",
                    "abstract": "Clinical decision support systems enhance diagnosis and reduce prescription errors.",
                }
            ],
        }

        result = answer_with_evidence("How do clinical decision support systems benefit triage?")
        assert result["status"] == "success"
        assert len(result["citations"]) == 1
        assert "disclaimer" in result
        assert "33481280" in result["response"] or "Evidence-Based" in result["response"]
        assert result["grounded"] is True

    # -------------------------------------------------------------------------
    # 7. Extended Clinical Electrolytes Classification Tests
    # -------------------------------------------------------------------------

    def test_potassium_and_sodium_classification(self):
        # Potassium
        assert classify_potassium(4.2)[0] == "normal"
        assert classify_potassium(3.1)[0] == "low"
        assert classify_potassium(5.5)[0] == "high"
        assert classify_potassium(6.5)[0] == "critical"

        # Sodium
        assert classify_sodium(140)[0] == "normal"
        assert classify_sodium(130)[0] == "low"
        assert classify_sodium(150)[0] == "high"
        assert classify_sodium(115)[0] == "critical"

        # Text extraction
        report_text = "Serum Potassium: 5.6 mmol/L. Serum Sodium: 132 mmol/L."
        analysis = parse_report_content(report_text)
        metrics = {m["test_name"]: m for m in analysis["metrics"]}
        assert "Potassium" in metrics
        assert metrics["Potassium"]["flag"] == "high"
        assert "Sodium" in metrics
        assert metrics["Sodium"]["flag"] == "low"
