from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from apps.audit_logs.services import log_audit_event
from apps.audit_logs.models import AuditLog

from .serializers import (
    RegisterSerializer,
    UserSerializer,
    UserUpdateSerializer,
    MedicareTokenObtainPairSerializer,
    LogoutSerializer,
)
from .services import register_user, blacklist_refresh_token


class RegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        result = register_user(serializer.validated_data, request=request)
        user_data = UserSerializer(result["user"]).data
        return Response(
            {
                "user": user_data,
                "tokens": result["tokens"],
                "message": "User registered successfully.",
            },
            status=status.HTTP_201_CREATED,
        )


class LoginView(TokenObtainPairView):
    permission_classes = [AllowAny]
    serializer_class = MedicareTokenObtainPairSerializer

    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        if response.status_code == 200:
            email = request.data.get("email")
            from .models import User
            user = User.objects.filter(email__iexact=email).first()
            if user:
                log_audit_event(
                    user=user,
                    action=AuditLog.Actions.USER_LOGIN,
                    resource_type="User",
                    resource_id=user.id,
                    request=request,
                    metadata={"role": user.role},
                )
        return response


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = LogoutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            blacklist_refresh_token(
                serializer.validated_data["refresh"],
                user=request.user,
                request=request,
            )
            return Response(
                {"message": "Logged out successfully. Refresh token invalidated."},
                status=status.HTTP_200_OK,
            )
        except Exception as exc:
            return Response(
                {"error": {"code": "LOGOUT_FAILED", "message": str(exc)}},
                status=status.HTTP_400_BAD_REQUEST,
            )


class MeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        data = UserSerializer(user).data
        # Attach profile details if present
        if user.role == user.Roles.PATIENT and hasattr(user, "patient_profile"):
            from apps.patients.serializers import PatientProfileSerializer
            data["profile"] = PatientProfileSerializer(user.patient_profile).data
        elif user.role == user.Roles.DOCTOR and hasattr(user, "doctor_profile"):
            from apps.doctors.serializers import DoctorProfileSerializer
            data["profile"] = DoctorProfileSerializer(user.doctor_profile).data
        return Response(data, status=status.HTTP_200_OK)

    def patch(self, request):
        serializer = UserUpdateSerializer(request.user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(UserSerializer(request.user).data, status=status.HTTP_200_OK)


class TokenRefreshCustomView(TokenRefreshView):
    permission_classes = [AllowAny]
