import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APIClient
from rest_framework import status
from apps.accounts.models import User
from apps.medical_records.models import LabReport


@pytest.mark.django_db
class TestMedicalRecordsAndUploads:
    @pytest.fixture(autouse=True)
    def setup_patient(self):
        self.patient = User.objects.create_user(
            email="uploader@medicare.local",
            password="Password123!",
            role=User.Roles.PATIENT,
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.patient)

    def test_valid_pdf_upload(self):
        # Valid PDF header: %PDF-1.4 ...
        pdf_content = b"%PDF-1.4 \ntest pdf medical report stream content"
        pdf_file = SimpleUploadedFile("blood_test.pdf", pdf_content, content_type="application/pdf")

        res = self.client.post(
            "/api/v1/records/reports/upload/",
            {"file": pdf_file, "title": "CBC Blood Panel"},
            format="multipart",
        )
        assert res.status_code == status.HTTP_201_CREATED
        data = res.json()
        assert data["title"] == "CBC Blood Panel"
        assert data["file_type"] == "pdf"
        assert LabReport.objects.filter(patient=self.patient).exists()

    def test_valid_png_upload(self):
        # Valid PNG header: \x89PNG\r\n\x1a\n
        png_content = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR" + b"image data"
        png_file = SimpleUploadedFile("xray.png", png_content, content_type="image/png")

        res = self.client.post(
            "/api/v1/records/reports/upload/",
            {"file": png_file, "title": "Chest X-Ray"},
            format="multipart",
        )
        assert res.status_code == status.HTTP_201_CREATED
        assert res.json()["file_type"] == "png"

    def test_disallowed_extension_rejected(self):
        script_file = SimpleUploadedFile("malware.exe", b"MZ\x90\x00executable", content_type="application/octet-stream")
        res = self.client.post(
            "/api/v1/records/reports/upload/",
            {"file": script_file},
            format="multipart",
        )
        assert res.status_code == status.HTTP_400_BAD_REQUEST
        assert "error" in res.json()

    def test_fake_pdf_signature_check_fails(self):
        # Text file pretending to be a PDF (Correction 5)
        fake_pdf = SimpleUploadedFile("fake.pdf", b"This is plain text pretending to be a pdf", content_type="application/pdf")
        res = self.client.post(
            "/api/v1/records/reports/upload/",
            {"file": fake_pdf},
            format="multipart",
        )
        assert res.status_code == status.HTTP_400_BAD_REQUEST
        assert "error" in res.json()

    def test_oversized_file_rejected(self):
        # Over 10MB
        oversized = SimpleUploadedFile("large.pdf", b"%PDF" + b"0" * (10 * 1024 * 1024 + 100), content_type="application/pdf")
        res = self.client.post(
            "/api/v1/records/reports/upload/",
            {"file": oversized},
            format="multipart",
        )
        assert res.status_code == status.HTTP_400_BAD_REQUEST
        assert "error" in res.json()
