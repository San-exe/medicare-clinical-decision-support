import pytest
from rest_framework.test import APIClient
from rest_framework import status
from apps.accounts.models import User
from apps.audit_logs.models import AuditLog


@pytest.mark.django_db
class TestAdminAndAuditLogs:
    @pytest.fixture(autouse=True)
    def setup_admin(self):
        self.admin = User.objects.create_user(
            email="sysadmin@medicare.local",
            password="AdminPassword123!",
            role=User.Roles.ADMIN,
        )
        self.patient = User.objects.create_user(
            email="patient.audit@medicare.local",
            password="Password123!",
            role=User.Roles.PATIENT,
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.admin)

    def test_admin_users_pagination(self):
        # Create multiple users to test pagination
        for i in range(15):
            User.objects.create_user(
                email=f"user{i}@medicare.local",
                password="Password123!",
                role=User.Roles.PATIENT,
            )

        res = self.client.get("/api/v1/admin/users/?page_size=5")
        assert res.status_code == status.HTTP_200_OK
        data = res.json()
        assert "count" in data
        assert "results" in data
        assert len(data["results"]) == 5
        assert data["count"] >= 17

    def test_admin_update_user_status(self):
        res = self.client.patch(
            f"/api/v1/admin/users/{self.patient.id}/",
            {"is_active": False},
            format="json",
        )
        assert res.status_code == status.HTTP_200_OK
        self.patient.refresh_from_db()
        assert self.patient.is_active is False

        # Verify audit log was recorded for admin action
        log = AuditLog.objects.filter(
            action=AuditLog.Actions.ADMIN_USER_UPDATE,
            resource_id=str(self.patient.id),
        ).first()
        assert log is not None
        assert log.user == self.admin

    def test_admin_analytics_genuine_database_counts(self):
        res = self.client.get("/api/v1/admin/analytics/")
        assert res.status_code == status.HTTP_200_OK
        data = res.json()
        assert "users" in data
        assert data["users"]["total"] >= 2
        assert data["users"]["admins"] >= 1
        assert "appointments" in data
        assert "clinical_data" in data

    def test_audit_log_server_controlled(self):
        # Authenticate as patient and perform an action
        self.client.force_authenticate(user=self.patient)

        # Login event produces server-controlled audit entry
        login_res = self.client.post(
            "/api/v1/auth/login/",
            {"email": "patient.audit@medicare.local", "password": "Password123!"},
            format="json",
        )
        assert login_res.status_code == status.HTTP_200_OK

        log = AuditLog.objects.filter(
            user=self.patient,
            action=AuditLog.Actions.USER_LOGIN,
        ).first()
        assert log is not None
        # Actor is derived strictly from server authentication (Correction 12)
        assert log.user == self.patient
