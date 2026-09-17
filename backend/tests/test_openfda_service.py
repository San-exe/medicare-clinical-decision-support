import pytest
from unittest.mock import patch, MagicMock
import requests
from django.core.cache import cache
from rest_framework.test import APIClient
from rest_framework import status
from apps.accounts.models import User
from apps.medicines.services.openfda_service import openfda_service, OpenFDAService


@pytest.mark.django_db
class TestOpenFDAServiceAndAPIs:
    """
    Test suite for pharmacological intelligence layer (OpenFDA service),
    caching behavior, network timeout handling, and REST endpoints.
    """

    @pytest.fixture(autouse=True)
    def setup_user_and_cache(self):
        cache.clear()
        self.user = User.objects.create_user(
            email="pharma.user@medicare.local",
            password="Password123!",
            role=User.Roles.DOCTOR,
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    @patch("requests.get")
    def test_get_adverse_reactions_mocked(self, mock_get):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "results": [
                {"term": "HEADACHE", "count": 1540},
                {"term": "NAUSEA", "count": 1210},
                {"term": "DIZZINESS", "count": 980},
            ]
        }
        mock_get.return_value = mock_response

        res = openfda_service.get_adverse_reactions("ibuprofen", limit=3)
        assert res["status"] == "success"
        assert res["drug"] == "ibuprofen"
        assert len(res["adverse_reactions"]) == 3
        assert res["adverse_reactions"][0]["reaction"] == "Headache"
        assert res["adverse_reactions"][0]["reported_cases"] == 1540
        assert res["cached"] is False

    @patch("requests.get")
    def test_get_boxed_warnings_and_precautions_mocked(self, mock_get):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "results": [
                {
                    "boxed_warning": ["WARNING: Tendonitis and tendon rupture may occur."],
                    "warnings": ["Central Nervous System Effects: Convulsions, increased intracranial pressure."],
                    "precautions": ["Patients with renal impairment should adjust dosage."],
                }
            ]
        }
        mock_get.return_value = mock_response

        res = openfda_service.get_boxed_warnings_and_precautions("ciprofloxacin")
        assert res["status"] == "success"
        assert res["has_boxed_warning"] is True
        assert len(res["boxed_warnings"]) == 1
        assert "Tendonitis" in res["boxed_warnings"][0]
        assert len(res["precautions"]) == 1

    @patch("requests.get")
    def test_check_interactions_mocked(self, mock_get):
        def side_effect(url, params=None, timeout=None):
            resp = MagicMock()
            resp.status_code = 200
            search_query = params.get("search", "") if params else ""
            if "warfarin" in search_query:
                resp.json.return_value = {
                    "results": [
                        {
                            "drug_interactions": [
                                "Concomitant use with aspirin increases the risk of severe bleeding and hemorrhage. Avoid coadministration."
                            ]
                        }
                    ]
                }
            else:
                resp.json.return_value = {"results": [{"drug_interactions": []}]}
            return resp

        mock_get.side_effect = side_effect

        res = openfda_service.check_interactions(["warfarin", "aspirin"])
        assert res["status"] == "success"
        assert res["total_interactions"] >= 1
        found = res["interactions_found"][0]
        assert "Aspirin" in (found["drug_a"], found["drug_b"])
        assert "Warfarin" in (found["drug_a"], found["drug_b"])
        assert "bleeding" in found["description"].lower()
        assert found["severity"] in ["high", "moderate"]

    @patch("requests.get")
    def test_caching_behavior_24h(self, mock_get):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "results": [{"term": "FATIGUE", "count": 500}]
        }
        mock_get.return_value = mock_response

        # 1st call -> network request
        first_call = openfda_service.get_adverse_reactions("metformin", limit=1)
        assert first_call["cached"] is False
        assert mock_get.call_count == 1

        # 2nd call -> retrieved from cache (mock not invoked again)
        second_call = openfda_service.get_adverse_reactions("metformin", limit=1)
        assert second_call["cached"] is True
        assert mock_get.call_count == 1
        assert second_call["adverse_reactions"] == first_call["adverse_reactions"]

    @patch("requests.get")
    def test_network_timeout_and_fallback_graceful_handling(self, mock_get):
        mock_get.side_effect = requests.Timeout("Network connection to api.fda.gov timed out.")

        # Test adverse reactions fallback
        rx_fallback = openfda_service.get_adverse_reactions("amoxicillin")
        assert rx_fallback["status"] == "warning"
        assert rx_fallback["adverse_reactions"] == []
        assert "Fallback active" in rx_fallback["message"]

        # Test interactions fallback
        int_fallback = openfda_service.check_interactions(["drugX", "drugY"])
        assert int_fallback["status"] == "warning"
        assert int_fallback["interactions_found"] == []
        assert "Fallback active" in int_fallback["message"]

    @patch("requests.get")
    def test_openfda_reactions_api_endpoint(self, mock_get):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "results": [
                {
                    "term": "RASH", "count": 220,
                    "boxed_warning": [],
                    "warnings": ["Discontinue if allergic rash occurs."],
                    "precautions": ["Dose adjustment for elderly."],
                }
            ]
        }
        mock_get.return_value = mock_response

        res = self.client.get("/api/v1/medicines/openfda/reactions/?drug=amoxicillin&limit=2")
        assert res.status_code == status.HTTP_200_OK
        data = res.json()
        assert data["drug"] == "amoxicillin"
        assert "adverse_reactions" in data
        assert "has_boxed_warning" in data
        assert "precautions" in data

    @patch("requests.get")
    def test_openfda_interactions_api_endpoint(self, mock_get):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"results": [{"drug_interactions": []}]}
        mock_get.return_value = mock_response

        payload = {"drugs": ["paracetamol", "ibuprofen"]}
        res = self.client.post("/api/v1/medicines/openfda/interactions/", payload, format="json")
        assert res.status_code == status.HTTP_200_OK
        data = res.json()
        assert "drugs_analyzed" in data
        assert "interactions_found" in data

    def test_openfda_validation_errors(self):
        # Missing 'drug' param in reactions
        res1 = self.client.get("/api/v1/medicines/openfda/reactions/")
        assert res1.status_code == status.HTTP_400_BAD_REQUEST
        assert "Query parameter 'drug' is required" in res1.json()["error"]["message"]

        # Invalid payload in interactions
        res2 = self.client.post("/api/v1/medicines/openfda/interactions/", {}, format="json")
        assert res2.status_code == status.HTTP_400_BAD_REQUEST
        assert "Field 'drugs' must be a non-empty list" in res2.json()["error"]["message"]
