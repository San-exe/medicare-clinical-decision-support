from django.conf import settings
from django.db import models


class AuditLog(models.Model):
    class Actions(models.TextChoices):
        USER_REGISTER = "USER_REGISTER", "User Registration"
        USER_LOGIN = "USER_LOGIN", "User Login"
        USER_LOGOUT = "USER_LOGOUT", "User Logout"
        TOKEN_REFRESH = "TOKEN_REFRESH", "Token Refresh"
        REPORT_UPLOAD = "REPORT_UPLOAD", "Lab Report Upload"
        RECORD_CREATE = "RECORD_CREATE", "Medical Record Create"
        RECORD_UPDATE = "RECORD_UPDATE", "Medical Record Update"
        APPOINTMENT_CREATE = "APPOINTMENT_CREATE", "Appointment Create"
        APPOINTMENT_UPDATE = "APPOINTMENT_UPDATE", "Appointment Update"
        CLINICAL_NOTE_CREATE = "CLINICAL_NOTE_CREATE", "Clinical Note Create"
        ADMIN_USER_UPDATE = "ADMIN_USER_UPDATE", "Admin User Update"
        ADMIN_ACCESS = "ADMIN_ACCESS", "Admin Access"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="audit_logs",
    )
    action = models.CharField(max_length=100, db_index=True)
    resource_type = models.CharField(max_length=100, blank=True, db_index=True)
    resource_id = models.CharField(max_length=100, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["action", "-created_at"]),
            models.Index(fields=["resource_type", "-created_at"]),
            models.Index(fields=["user", "-created_at"]),
        ]

    def __str__(self):
        actor = self.user.email if self.user else "Anonymous"
        return f"[{self.created_at:%Y-%m-%d %H:%M:%S}] {actor} - {self.action}"
