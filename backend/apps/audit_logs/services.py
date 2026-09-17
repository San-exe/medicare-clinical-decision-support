import logging
from .models import AuditLog

logger = logging.getLogger(__name__)


def get_client_ip(request):
    """Extract client IP address from request headers safely."""
    if not request:
        return None
    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if x_forwarded_for:
        ip = x_forwarded_for.split(",")[0].strip()
    else:
        ip = request.META.get("REMOTE_ADDR")
    return ip


def log_audit_event(user=None, action="", resource_type="", resource_id="", request=None, metadata=None):
    """
    Centralized server-side audit logging function (Correction 12).
    Always derives the acting user from the authenticated session / request.
    Sanitizes metadata to ensure no passwords or secrets are ever recorded.
    """
    try:
        actor = user
        if actor is None and request and hasattr(request, "user") and request.user.is_authenticated:
            actor = request.user

        ip_address = get_client_ip(request)

        clean_metadata = {}
        if isinstance(metadata, dict):
            for k, v in metadata.items():
                # Strip any sensitive fields
                if any(secret_word in k.lower() for secret_word in ("password", "token", "secret", "authorization")):
                    continue
                clean_metadata[k] = str(v)

        return AuditLog.objects.create(
            user=actor,
            action=action,
            resource_type=resource_type,
            resource_id=str(resource_id) if resource_id is not None else "",
            ip_address=ip_address,
            metadata=clean_metadata,
        )
    except Exception as exc:
        logger.error("Failed to write audit log: %s", exc)
        return None
