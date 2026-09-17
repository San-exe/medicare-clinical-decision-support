import pytest
from django.utils import timezone
from rest_framework.test import APIClient
from rest_framework import status
from apps.accounts.models import User
from apps.patients.models import PatientProfile
from apps.doctors.models import DoctorProfile
from apps.appointments.models import Appointment
from apps.predictions.models import DiseasePrediction, SymptomAnalysis, DiseasePredictionHistory
from apps.predictions.services.symptom_parser import (
    parse_symptoms,
    get_canonical_symptom_catalog,
    suggest_related_symptoms,
)
from apps.predictions.services.disease_engine import predict_diseases
from apps.predictions.services.shap_explainer import explain_prediction


@pytest.mark.django_db
class TestPredictionsAndShap:
    """
    Test suite for symptom parsing, disease prediction engine, SHAP explanations,
    and patient authorization boundaries.
    """

    @pytest.fixture(autouse=True)
    def setup_data(self):
        self.patient_a = User.objects.create_user(
            email="patient.pred.a@medicare.local",
            password="Password123!",
            role=User.Roles.PATIENT,
        )
        self.profile_a = PatientProfile.objects.create(user=self.patient_a)

        self.patient_b = User.objects.create_user(
            email="patient.pred.b@medicare.local",
            password="Password123!",
            role=User.Roles.PATIENT,
        )
        self.profile_b = PatientProfile.objects.create(user=self.patient_b)

        self.doctor = User.objects.create_user(
            email="doctor.pred@medicare.local",
            password="Password123!",
            role=User.Roles.DOCTOR,
            first_name="Elena",
            last_name="Rostova",
        )
        self.doc_profile = DoctorProfile.objects.create(
            user=self.doctor,
            license_number="LIC-PRED-99",
            specialization="Internal Medicine",
        )

        self.client = APIClient()

    # --- Unit Tests: Symptom Parsing & Disease Engine ---

    def test_symptom_normalization_with_noisy_input(self):
        noisy_text = "I've been having high temperature, a hacking cough, and severe head hurting since yesterday!!"
        parsed = parse_symptoms(noisy_text)

        canonical = parsed["canonical_symptoms"]
        assert "fever" in canonical
        assert "cough" in canonical
        assert "headache" in canonical

        vector = parsed["feature_vector"]
        assert vector["fever"] == 1
        assert vector["cough"] == 1
        assert vector["headache"] == 1
        assert vector["polyuria"] == 0

        # Test array input with slang
        array_input = ["runny nose", "feverish", "peeing often"]
        parsed_array = parse_symptoms(array_input)
        assert "rhinorrhea" in parsed_array["canonical_symptoms"]
        assert "fever" in parsed_array["canonical_symptoms"]
        assert "polyuria" in parsed_array["canonical_symptoms"]

    def test_disease_prediction_probabilities_and_ranking(self):
        # Diabetes profile: polyuria + polydipsia + weight_loss
        parsed = parse_symptoms(["frequent urination", "excessive thirst", "unexplained weight loss"])
        prediction = predict_diseases(parsed["feature_vector"])

        top = prediction["top_prediction"]
        assert top["disease"] == "Type 2 Diabetes"
        assert top["probability"] > 0.40

        # Assert probability sum equals 1.0 (within float tolerance)
        prob_sum = sum(d["probability"] for d in prediction["ranked_diagnoses"])
        assert abs(prob_sum - 1.0) < 0.001

        # Assert ranked descending
        probs = [d["probability"] for d in prediction["ranked_diagnoses"]]
        assert probs == sorted(probs, reverse=True)

    def test_shap_attribution_schema_and_values(self):
        parsed = parse_symptoms(["fever", "cough", "headache"])
        prediction = predict_diseases(parsed["feature_vector"])
        top_disease = prediction["top_prediction"]["disease"]

        attributions = explain_prediction(parsed["feature_vector"], top_disease)
        assert len(attributions) > 0

        for attr in attributions:
            assert "feature" in attr
            assert "contribution" in attr
            assert "direction" in attr
            assert "baseline" in attr

            assert isinstance(attr["feature"], str)
            assert isinstance(attr["contribution"], (int, float))
            assert attr["direction"] in ["increases_risk", "decreases_risk"]
            assert isinstance(attr["baseline"], (int, float))
            assert attr["contribution"] >= 0

    # --- API Endpoint & Authorization Tests ---

    def test_symptoms_parse_endpoint(self):
        self.client.force_authenticate(user=self.patient_a)
        payload = {"text": "I feel dizzy, nauseous, and my head is throbbing."}
        res = self.client.post("/api/v1/predictions/symptoms/", payload, format="json")

        assert res.status_code == status.HTTP_200_OK
        data = res.json()
        assert "canonical_symptoms" in data
        assert "headache" in data["canonical_symptoms"]
        assert "dizziness" in data["canonical_symptoms"]
        assert "nausea" in data["canonical_symptoms"]
        assert "suggested_symptoms" in data
        assert "catalog" in data

    def test_patient_can_create_disease_prediction_for_self(self):
        self.client.force_authenticate(user=self.patient_a)
        payload = {
            "symptoms": ["fever", "cough", "body aches", "chills"],
        }
        res = self.client.post("/api/v1/predictions/disease/", payload, format="json")

        assert res.status_code == status.HTTP_201_CREATED
        data = res.json()
        assert data["patient_id"] == self.patient_a.id
        assert data["predicted_condition"] == "Influenza"
        assert data["confidence"] > 0.40
        assert "shap_explanations" in data
        assert len(data["shap_explanations"]) > 0
        assert "disclaimer" in data
        assert "clinical decision support system" in data["disclaimer"]

        # Ensure saved to database
        assert DiseasePrediction.objects.filter(patient=self.patient_a, predicted_condition="Influenza").exists()
        assert DiseasePredictionHistory.objects.filter(patient=self.patient_a).count() == 1

    def test_patient_cannot_predict_for_another_patient(self):
        self.client.force_authenticate(user=self.patient_a)
        payload = {
            "patient_id": self.patient_b.id,
            "symptoms": ["fever", "cough"],
        }
        res = self.client.post("/api/v1/predictions/disease/", payload, format="json")
        assert res.status_code == status.HTTP_403_FORBIDDEN
        assert "Patients can only request predictions for themselves" in res.json()["error"]["message"]

    def test_doctor_cannot_predict_for_unauthorized_patient(self):
        self.client.force_authenticate(user=self.doctor)
        payload = {
            "patient_id": self.patient_b.id,
            "symptoms": ["chest pain", "shortness of breath"],
        }
        res = self.client.post("/api/v1/predictions/disease/", payload, format="json")
        assert res.status_code == status.HTTP_403_FORBIDDEN
        assert "Doctor does not have active clinical authorization for this patient." in res.json()["error"]["message"]

    def test_doctor_can_predict_for_authorized_patient(self):
        # Establish relationship via appointment
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
        data = res.json()
        assert data["patient_id"] == self.patient_b.id
        assert data["predicted_condition"] == "Pneumonia"
        assert data["severity"] in ["high", "critical"]
        assert DiseasePrediction.objects.filter(patient=self.patient_b, predicted_condition="Pneumonia").exists()
