"""
Comprehensive DRF API Integration Test Suite for MediCare CDSS (Phase 4).

Verifies:
1. End-to-end POST /api/v1/predictions/disease/ with symptom array returns real XGBoost prediction, TreeSHAP attributions, and clinical safety payload.
2. End-to-end POST /api/v1/predictions/disease/ with free-text symptom input.
3. End-to-end input with mixed vitals (blood pressure, glucose, heart rate) influencing prediction and TreeSHAP attributions.
4. Clinical red-flag symptoms (chest pain, severe hypoxemia) triggering triage escalation in API response.
5. 100% backward compatibility for Person 3 (Frontend) response schema.
6. Role-based authorization boundaries (patient self-service, doctor-patient relationship, admin).
7. Error handling (HTTP 400 on empty input, HTTP 503 on model failure).
8. POST /api/v1/predictions/symptoms/ utilizing ClinicalPreprocessor with fuzzy matching and negation.
"""

from unittest.mock import patch
import pytest
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from apps.accounts.models import User
from apps.appointments.models import Appointment
from apps.doctors.models import DoctorProfile
from apps.patients.models import PatientProfile
from apps.predictions.models import DiseasePrediction, SymptomAnalysis
from ai.engine import ModelNotLoadedError


@pytest.mark.django_db
class TestPredictionsAPIIntegration:
    @pytest.fixture(autouse=True)
    def setup_users(self):
        # Patient A
        self.patient_a = User.objects.create_user(
            email="patient.alice@medicare.local",
            password="Password123!",
            role=User.Roles.PATIENT,
            first_name="Alice",
            last_name="Smith",
        )
        self.profile_a = PatientProfile.objects.create(user=self.patient_a)

        # Patient B
        self.patient_b = User.objects.create_user(
            email="patient.bob@medicare.local",
            password="Password123!",
            role=User.Roles.PATIENT,
            first_name="Bob",
            last_name="Jones",
        )
        self.profile_b = PatientProfile.objects.create(user=self.patient_b)

        # Doctor
        self.doctor = User.objects.create_user(
            email="dr.carter@medicare.local",
            password="Password123!",
            role=User.Roles.DOCTOR,
            first_name="John",
            last_name="Carter",
        )
        self.doctor_profile = DoctorProfile.objects.create(
            user=self.doctor,
            license_number="LIC-MD-55421",
            specialization="Pulmonology",
        )

        self.client = APIClient()

    # -----------------------------------------------------------------------
    # 1. End-to-End Prediction with Symptom Array
    # -----------------------------------------------------------------------
    def test_e2e_disease_prediction_with_symptom_array(self):
        self.client.force_authenticate(user=self.patient_a)
        payload = {
            "symptoms": ["frequent urination", "excessive thirst", "unexplained weight loss", "fatigue"],
        }
        res = self.client.post("/api/v1/predictions/disease/", payload, format="json")

        assert res.status_code == status.HTTP_201_CREATED
        data = res.json()

        # Primary prediction
        assert data["predicted_condition"] == "Type 2 Diabetes"
        assert data["confidence"] > 0.40
        assert data["patient_id"] == self.patient_a.id

        # SHAP explainability
        assert "shap_analysis" in data
        assert "base_value" in data["shap_analysis"]
        assert isinstance(data["shap_analysis"]["features"], list)
        assert len(data["shap_analysis"]["features"]) > 0

        # Clinical safety
        assert "clinical_safety" in data
        assert data["clinical_safety"]["is_definitive_diagnosis"] is False
        assert "Clinical decision support estimate only" in data["clinical_safety"]["disclaimer"]

        # Model metadata
        meta = data["model_metadata"]
        assert meta["model_name"] == "MediCare-MultiDisease-XGBoost"
        assert meta["model_version"] == "1.0.0"
        assert meta["schema_version"] == "1.0.0"
        assert "timestamp" in meta

        # Persisted to DB
        assert DiseasePrediction.objects.filter(
            patient=self.patient_a, predicted_condition="Type 2 Diabetes"
        ).exists()

    # -----------------------------------------------------------------------
    # 2. End-to-End Prediction with Free-Text Query
    # -----------------------------------------------------------------------
    def test_e2e_disease_prediction_with_free_text(self):
        self.client.force_authenticate(user=self.patient_a)
        payload = {
            "text": "I've had a bad persistent cough, very high fever, severe chills and body aches for two days",
        }
        res = self.client.post("/api/v1/predictions/disease/", payload, format="json")

        assert res.status_code == status.HTTP_201_CREATED
        data = res.json()

        assert data["predicted_condition"] == "Influenza"
        assert data["confidence"] > 0.40

        # Verify canonical symptoms were extracted
        canonical = data["canonical_symptoms"]
        assert "fever" in canonical
        assert "cough" in canonical
        assert "chills" in canonical
        assert "body_aches" in canonical

    # -----------------------------------------------------------------------
    # 3. Mixed Vitals Influence Prediction & SHAP
    # -----------------------------------------------------------------------
    def test_e2e_mixed_vitals_influence_prediction_and_shap(self):
        self.client.force_authenticate(user=self.patient_a)
        payload = {
            "symptoms": ["headache", "dizziness"],
            "vitals": {
                "systolic_bp": 178.0,
                "diastolic_bp": 108.0,
                "heart_rate": 84.0,
                "age": 58,
            },
        }
        res = self.client.post("/api/v1/predictions/disease/", payload, format="json")

        assert res.status_code == status.HTTP_201_CREATED
        data = res.json()

        assert data["predicted_condition"] == "Hypertension"
        assert data["confidence"] > 0.50

        # Verify systolic_bp shows up in SHAP features
        features = data["shap_analysis"]["features"]
        bp_feature = next((f for f in features if f["feature"] == "systolic_bp"), None)
        assert bp_feature is not None
        assert bp_feature["direction"] == "increases_risk"
        assert bp_feature["value"] == 178.0

    # -----------------------------------------------------------------------
    # 4. Clinical Red-Flag Symptoms Trigger Risk Escalation
    # -----------------------------------------------------------------------
    def test_e2e_red_flag_symptoms_risk_escalation(self):
        self.client.force_authenticate(user=self.patient_a)
        payload = {
            "symptoms": ["chest pain", "shortness of breath", "cough"],
            "vitals": {"oxygen_saturation": 88.5},
        }
        res = self.client.post("/api/v1/predictions/disease/", payload, format="json")

        assert res.status_code == status.HTTP_201_CREATED
        data = res.json()

        # Chest pain + dyspnea + low SpO2 must trigger HIGH risk level and critical/high severity
        assert data["risk_level"] == "HIGH"
        assert data["triage_level"] == "HIGH"
        assert data["severity"] in ["high", "critical"]

    # -----------------------------------------------------------------------
    # 5. 100% Backward Compatibility with Frontend (Person 3) Contract
    # -----------------------------------------------------------------------
    def test_e2e_legacy_fields_backward_compatibility(self):
        self.client.force_authenticate(user=self.patient_a)
        payload = {"symptoms": ["nausea", "watery diarrhea", "stomach cramps"]}
        res = self.client.post("/api/v1/predictions/disease/", payload, format="json")

        assert res.status_code == status.HTTP_201_CREATED
        data = res.json()

        # All legacy keys expected by frontend components
        assert "id" in data
        assert "patient_id" in data
        assert "predicted_condition" in data
        assert "confidence" in data
        assert "severity" in data
        assert "triage_level" in data
        assert "risk_level" in data
        assert "recommendation" in data
        assert "recommended_action" in data
        assert "canonical_symptoms" in data
        assert "ranked_diagnoses" in data
        assert "ranked_diseases" in data
        assert "differential_diagnoses" in data
        assert "shap_explanations" in data
        assert "shap_analysis" in data
        assert "explanation" in data
        assert "clinical_safety" in data
        assert "disclaimer" in data
        assert "model_metadata" in data
        assert "created_at" in data

        # Check structure inside shap_explanations for symptom.jsx
        shap_obj = data["shap_explanations"]
        assert "base_value" in shap_obj
        assert "features" in shap_obj
        for f in shap_obj["features"]:
            assert "feature" in f
            assert "contribution" in f
            assert "shap_value" in f
            assert "direction" in f

        # Check structure inside ranked_diagnoses for symptom.jsx
        for d in data["ranked_diagnoses"]:
            assert "disease" in d
            assert "probability" in d

    # -----------------------------------------------------------------------
    # 6. Role-Based Authorization & Doctor Boundary Checks
    # -----------------------------------------------------------------------
    def test_e2e_patient_cannot_predict_for_other_patient(self):
        self.client.force_authenticate(user=self.patient_a)
        payload = {
            "patient_id": self.patient_b.id,
            "symptoms": ["fever", "cough"],
        }
        res = self.client.post("/api/v1/predictions/disease/", payload, format="json")
        assert res.status_code == status.HTTP_403_FORBIDDEN

    def test_e2e_doctor_cannot_predict_without_relationship(self):
        self.client.force_authenticate(user=self.doctor)
        payload = {
            "patient_id": self.patient_b.id,
            "symptoms": ["fever", "cough"],
        }
        res = self.client.post("/api/v1/predictions/disease/", payload, format="json")
        assert res.status_code == status.HTTP_403_FORBIDDEN

    def test_e2e_doctor_can_predict_with_confirmed_appointment(self):
        Appointment.objects.create(
            patient=self.patient_b,
            doctor=self.doctor,
            starts_at=timezone.now() + timezone.timedelta(days=1),
            status=Appointment.Status.CONFIRMED,
        )
        self.client.force_authenticate(user=self.doctor)
        payload = {
            "patient_id": self.patient_b.id,
            "symptoms": ["dyspnea", "cough", "chest tightness", "high temperature"],
        }
        res = self.client.post("/api/v1/predictions/disease/", payload, format="json")
        assert res.status_code == status.HTTP_201_CREATED
        assert res.json()["patient_id"] == self.patient_b.id

    # -----------------------------------------------------------------------
    # 7. Error Handling: 400 Bad Request & 503 Model Unavailable
    # -----------------------------------------------------------------------
    def test_e2e_empty_input_returns_400(self):
        self.client.force_authenticate(user=self.patient_a)
        res = self.client.post("/api/v1/predictions/disease/", {}, format="json")
        assert res.status_code == status.HTTP_400_BAD_REQUEST

    def test_e2e_unauthenticated_returns_401(self):
        res = self.client.post("/api/v1/predictions/disease/", {"symptoms": ["fever"]}, format="json")
        assert res.status_code == status.HTTP_401_UNAUTHORIZED

    def test_e2e_model_not_loaded_returns_503(self):
        self.client.force_authenticate(user=self.patient_a)
        with patch("apps.predictions.views.get_engine") as mock_get_engine:
            mock_get_engine.side_effect = ModelNotLoadedError("Artifacts missing on disk")
            res = self.client.post(
                "/api/v1/predictions/disease/",
                {"symptoms": ["fever", "cough"]},
                format="json",
            )
            assert res.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
            err = res.json()["error"]
            assert err["code"] == "MODEL_UNAVAILABLE"
            assert "currently initializing or unavailable" in err["message"]

    # -----------------------------------------------------------------------
    # 8. Symptom Analysis Endpoint with Preprocessor Fuzzy Matching & Negation
    # -----------------------------------------------------------------------
    def test_symptom_analysis_endpoint_fuzzy_and_negation(self):
        self.client.force_authenticate(user=self.patient_a)
        # Typo 'fevr', 'hedache' + bounded negation 'no chest pain' + contrastive conjunction 'but persistent cough'
        payload = {
            "text": "I have a high fevr and bad hedache, no chest pain, but persistent cough",
        }
        res = self.client.post("/api/v1/predictions/symptoms/", payload, format="json")

        assert res.status_code == status.HTTP_200_OK
        data = res.json()

        # Canonical symptoms parsed with fuzzy typo tolerance
        canonical = data["canonical_symptoms"]
        assert "fever" in canonical
        assert "headache" in canonical
        assert "cough" in canonical
        assert "chest_pain" not in canonical

        # Negated symptoms captured
        negated = data["negated_symptoms"]
        assert "chest_pain" in negated

        # Feature vector and catalog
        assert data["feature_vector"]["fever"] == 1
        assert data["feature_vector"]["chest_pain"] == 0
        assert "suggested_symptoms" in data
        assert "catalog" in data

        # Persisted to DB for patient
        assert SymptomAnalysis.objects.filter(patient=self.patient_a).exists()
