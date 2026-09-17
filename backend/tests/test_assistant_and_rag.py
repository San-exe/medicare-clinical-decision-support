import pytest
from unittest.mock import patch, MagicMock
import requests
from django.core.cache import cache
from rest_framework.test import APIClient
from rest_framework import status

from apps.accounts.models import User
from apps.doctors.models import DoctorProfile
from apps.patients.models import PatientProfile
from apps.appointments.models import Appointment
from apps.assistant.models import ChatConversation, ChatMessage
from apps.assistant.services.pubmed_service import pubmed_service
from apps.assistant.services.rag_engine import rag_assistant_engine, MANDATORY_REGULATORY_DISCLAIMER


@pytest.mark.django_db
class TestAssistantAndPubMedRAG:
    """
    Test suite for PubMed E-utilities integration, RAG clinical engine,
    authorization boundaries, conversation persistence, and REST endpoints.
    """

    @pytest.fixture(autouse=True)
    def setup_data(self):
        cache.clear()

        # Doctor 1 & profile
        self.doc1_user = User.objects.create_user(
            email="doc1.rag@medicare.local",
            password="Password123!",
            role=User.Roles.DOCTOR,
            first_name="Gregory",
            last_name="House",
        )
        self.doc1_profile = DoctorProfile.objects.create(
            user=self.doc1_user,
            license_number="DOC-RAG-001",
            specialization="Internal Medicine",
        )

        # Doctor 2 & profile
        self.doc2_user = User.objects.create_user(
            email="doc2.rag@medicare.local",
            password="Password123!",
            role=User.Roles.DOCTOR,
            first_name="James",
            last_name="Wilson",
        )
        self.doc2_profile = DoctorProfile.objects.create(
            user=self.doc2_user,
            license_number="DOC-RAG-002",
            specialization="Oncology",
        )

        # Patient 1 & profile
        self.pat1_user = User.objects.create_user(
            email="pat1.rag@medicare.local",
            password="Password123!",
            role=User.Roles.PATIENT,
            first_name="John",
            last_name="Doe",
        )
        self.pat1_profile = PatientProfile.objects.create(
            user=self.pat1_user,
            emergency_contact="1234567890",
        )

        # Patient 2 & profile
        self.pat2_user = User.objects.create_user(
            email="pat2.rag@medicare.local",
            password="Password123!",
            role=User.Roles.PATIENT,
            first_name="Jane",
            last_name="Smith",
        )
        self.pat2_profile = PatientProfile.objects.create(
            user=self.pat2_user,
            emergency_contact="0987654321",
        )

        from django.utils import timezone
        # Active Appointment: Doctor 1 <-> Patient 1
        Appointment.objects.create(
            doctor=self.doc1_user,
            patient=self.pat1_user,
            status=Appointment.Status.CONFIRMED,
            starts_at=timezone.now() + timezone.timedelta(days=1),
        )

        self.client = APIClient()

    # -------------------------------------------------------------------------
    # PubMed Service Tests
    # -------------------------------------------------------------------------

    @patch("requests.get")
    def test_pubmed_service_mocked_success(self, mock_get):
        # Mock ESearch
        esearch_resp = MagicMock()
        esearch_resp.status_code = 200
        esearch_resp.json.return_value = {
            "esearchresult": {"idlist": ["12345678", "87654321"]}
        }

        # Mock ESummary
        esummary_resp = MagicMock()
        esummary_resp.status_code = 200
        esummary_resp.json.return_value = {
            "result": {
                "12345678": {
                    "title": "Clinical Efficacy of Novel Antihypertensive Regimens.",
                    "source": "The Lancet",
                    "pubdate": "2023 Nov",
                    "authors": [{"name": "Smith J"}, {"name": "Brown A"}],
                },
                "87654321": {
                    "title": "Comprehensive Guidelines for Arterial Hypertension.",
                    "source": "New England Journal of Medicine",
                    "pubdate": "2022",
                    "authors": [{"name": "Johnson K"}],
                },
            }
        }

        mock_get.side_effect = [esearch_resp, esummary_resp]

        result = pubmed_service.search_pubmed("hypertension treatment", limit=2)
        assert result["status"] == "success"
        assert len(result["citations"]) == 2
        assert result["citations"][0]["pmid"] == "12345678"
        assert result["citations"][0]["title"] == "Clinical Efficacy of Novel Antihypertensive Regimens"
        assert result["citations"][0]["journal"] == "The Lancet"
        assert result["citations"][0]["year"] == "2023"
        assert result["cached"] is False

    @patch("requests.get")
    def test_pubmed_service_caching_24h(self, mock_get):
        esearch_resp = MagicMock()
        esearch_resp.status_code = 200
        esearch_resp.json.return_value = {"esearchresult": {"idlist": ["11112222"]}}

        esummary_resp = MagicMock()
        esummary_resp.status_code = 200
        esummary_resp.json.return_value = {
            "result": {
                "11112222": {
                    "title": "Study on Metformin.",
                    "source": "Diabetes Care",
                    "pubdate": "2021",
                    "authors": [{"name": "Adams C"}],
                }
            }
        }

        mock_get.side_effect = [esearch_resp, esummary_resp]

        # Call 1: uncached
        res1 = pubmed_service.search_pubmed("metformin diabetes", limit=1)
        assert res1["cached"] is False
        assert mock_get.call_count == 2

        # Call 2: cached
        res2 = pubmed_service.search_pubmed("metformin diabetes", limit=1)
        assert res2["cached"] is True
        assert mock_get.call_count == 2  # No new network requests
        assert res2["citations"] == res1["citations"]

    @patch("requests.get")
    def test_pubmed_service_timeout_fallback(self, mock_get):
        mock_get.side_effect = requests.Timeout("NCBI Entrez service timed out.")

        res = pubmed_service.search_pubmed("hypertension", limit=2)
        assert res["status"] == "fallback"
        assert len(res["citations"]) > 0
        assert "Guideline" in res["citations"][0]["title"]
        assert "29146124" == res["citations"][0]["pmid"]

    # -------------------------------------------------------------------------
    # RAG Assistant Engine Unit Tests
    # -------------------------------------------------------------------------

    def test_rag_engine_synthesizes_disclaimer_and_citations(self):
        result = rag_assistant_engine.process_chat(
            user=self.pat1_user,
            prompt="What are optimal non-pharmacological therapies for hypertension?",
        )

        assert "conversation_id" in result
        assert "message_id" in result
        assert "response" in result
        assert "citations" in result
        assert result["disclaimer"] == MANDATORY_REGULATORY_DISCLAIMER
        assert "hypertension" in result["response"].lower()

        # Check DB persistence
        conv = ChatConversation.objects.get(id=result["conversation_id"])
        assert conv.user == self.pat1_user
        assert conv.messages.count() == 2  # 1 user + 1 assistant

        user_msg = conv.messages.filter(role="user").first()
        assistant_msg = conv.messages.filter(role="assistant").first()
        assert "non-pharmacological therapies" in user_msg.content
        assert len(assistant_msg.sources) > 0

    # -------------------------------------------------------------------------
    # REST API Endpoint Tests (/api/v1/assistant/chat/ & history/)
    # -------------------------------------------------------------------------

    def test_chat_unauthenticated_forbidden(self):
        res = self.client.post("/api/v1/assistant/chat/", {"prompt": "Hello"}, format="json")
        assert res.status_code == status.HTTP_401_UNAUTHORIZED

    def test_chat_empty_prompt_validation_error(self):
        self.client.force_authenticate(user=self.pat1_user)
        res = self.client.post("/api/v1/assistant/chat/", {"prompt": "  "}, format="json")
        assert res.status_code == status.HTTP_400_BAD_REQUEST

    def test_patient_can_chat_and_continue_conversation(self):
        self.client.force_authenticate(user=self.pat1_user)

        # Initial turn
        payload1 = {"prompt": "What should I know about managing type 2 diabetes?"}
        res1 = self.client.post("/api/v1/assistant/chat/", payload1, format="json")
        assert res1.status_code == status.HTTP_200_OK
        data1 = res1.json()

        conv_id = data1["conversation_id"]
        assert conv_id is not None
        assert data1["disclaimer"] == MANDATORY_REGULATORY_DISCLAIMER
        assert len(data1["citations"]) > 0

        # Subsequent turn on same conversation
        payload2 = {"prompt": "Can exercise help lower blood sugar?", "conversation_id": conv_id}
        res2 = self.client.post("/api/v1/assistant/chat/", payload2, format="json")
        assert res2.status_code == status.HTTP_200_OK
        data2 = res2.json()

        assert data2["conversation_id"] == conv_id
        # Total messages in this conversation should now be 4 (2 user, 2 assistant)
        conv = ChatConversation.objects.get(id=conv_id)
        assert conv.messages.count() == 4

    def test_unauthorized_user_cannot_access_or_append_to_another_users_conversation(self):
        # Patient 1 creates a conversation
        conv = ChatConversation.objects.create(user=self.pat1_user, title="Private Chat")
        ChatMessage.objects.create(conversation=conv, role="user", content="Secret data")

        # Patient 2 tries to append to Patient 1's conversation
        self.client.force_authenticate(user=self.pat2_user)
        payload = {"prompt": "Hijack attempt", "conversation_id": conv.id}
        res = self.client.post("/api/v1/assistant/chat/", payload, format="json")
        assert res.status_code == status.HTTP_403_FORBIDDEN

    def test_doctor_cannot_query_unauthorized_patient_context(self):
        # Doctor 2 has NO relationship with Patient 1
        self.client.force_authenticate(user=self.doc2_user)
        payload = {
            "prompt": "Evaluate patient's lab results",
            "patient_id": self.pat1_user.id,
        }
        res = self.client.post("/api/v1/assistant/chat/", payload, format="json")
        assert res.status_code == status.HTTP_403_FORBIDDEN
        assert "authorization" in res.json()["error"]["message"].lower()

    def test_doctor_can_query_authorized_patient_context(self):
        # Doctor 1 has active confirmed appointment with Patient 1
        self.client.force_authenticate(user=self.doc1_user)
        payload = {
            "prompt": "Evaluate patient's blood pressure trajectory",
            "patient_id": self.pat1_user.id,
        }
        res = self.client.post("/api/v1/assistant/chat/", payload, format="json")
        assert res.status_code == status.HTTP_200_OK
        data = res.json()
        assert data["conversation_id"] is not None
        assert data["disclaimer"] == MANDATORY_REGULATORY_DISCLAIMER

    def test_patient_cannot_query_another_patient_context(self):
        # Patient 1 tries to query with Patient 2's id
        self.client.force_authenticate(user=self.pat1_user)
        payload = {
            "prompt": "Tell me about Jane",
            "patient_id": self.pat2_user.id,
        }
        res = self.client.post("/api/v1/assistant/chat/", payload, format="json")
        assert res.status_code == status.HTTP_403_FORBIDDEN

    def test_assistant_history_isolation(self):
        # Patient 1 has 2 conversations
        conv1 = ChatConversation.objects.create(user=self.pat1_user, title="Pat1 Chat 1")
        ChatMessage.objects.create(conversation=conv1, role="user", content="Msg 1")
        conv2 = ChatConversation.objects.create(user=self.pat1_user, title="Pat1 Chat 2")
        ChatMessage.objects.create(conversation=conv2, role="user", content="Msg 2")

        # Patient 2 has 1 conversation
        conv3 = ChatConversation.objects.create(user=self.pat2_user, title="Pat2 Chat 1")
        ChatMessage.objects.create(conversation=conv3, role="user", content="Pat2 Msg")

        # Query Patient 1 history
        self.client.force_authenticate(user=self.pat1_user)
        res1 = self.client.get("/api/v1/assistant/history/")
        assert res1.status_code == status.HTTP_200_OK
        data1 = res1.json()
        assert data1["count"] == 2
        titles = [c["title"] for c in data1["results"]]
        assert "Pat1 Chat 1" in titles
        assert "Pat1 Chat 2" in titles
        assert "Pat2 Chat 1" not in titles

        # Query Patient 2 history
        self.client.force_authenticate(user=self.pat2_user)
        res2 = self.client.get("/api/v1/assistant/history/")
        assert res2.status_code == status.HTTP_200_OK
        data2 = res2.json()
        assert data2["count"] == 1
        assert data2["results"][0]["title"] == "Pat2 Chat 1"
