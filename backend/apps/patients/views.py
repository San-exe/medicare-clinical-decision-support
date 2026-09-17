from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from core.permissions import IsPatient
from .models import PatientProfile
from .serializers import PatientProfileSerializer
from .services import get_patient_dashboard_data


class ProfileView(APIView):
    """
    GET  /api/v1/patient/profile/ - Retrieve authenticated patient's profile
    PATCH /api/v1/patient/profile/ - Update authenticated patient's profile
    """
    permission_classes = [IsPatient]

    def get(self, request):
        profile, _ = PatientProfile.objects.get_or_create(user=request.user)
        serializer = PatientProfileSerializer(profile)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def patch(self, request):
        profile, _ = PatientProfile.objects.get_or_create(user=request.user)
        serializer = PatientProfileSerializer(profile, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)


class DashboardView(APIView):
    """
    GET /api/v1/patient/dashboard/ - Database-backed aggregated patient dashboard
    """
    permission_classes = [IsPatient]

    def get(self, request):
        data = get_patient_dashboard_data(request.user)
        return Response(data, status=status.HTTP_200_OK)
