from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied, NotFound
from core.permissions import IsAuthenticatedUser
from core.pagination import StandardResultsSetPagination
from apps.accounts.models import User

from .models import Appointment
from .serializers import (
    AppointmentSerializer,
    AppointmentCreateSerializer,
    AppointmentUpdateSerializer,
)
from .services import create_appointment, update_appointment


class AppointmentListCreateView(APIView):
    permission_classes = [IsAuthenticatedUser]

    def get(self, request):
        user = request.user
        queryset = Appointment.objects.select_related("patient", "doctor")

        if user.role == User.Roles.PATIENT:
            queryset = queryset.filter(patient=user)
        elif user.role == User.Roles.DOCTOR:
            queryset = queryset.filter(doctor=user)
        elif user.role == User.Roles.ADMIN or user.is_superuser:
            pass  # Admins can view all
        else:
            raise PermissionDenied("Access denied.")

        status_filter = request.query_params.get("status")
        if status_filter:
            queryset = queryset.filter(status=status_filter)

        paginator = StandardResultsSetPagination()
        page = paginator.paginate_queryset(queryset, request)
        serializer = AppointmentSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)

    def post(self, request):
        if request.user.role != User.Roles.PATIENT:
            raise PermissionDenied("Only registered patients may book appointments.")

        serializer = AppointmentCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        appointment = create_appointment(
            patient_user=request.user,
            doctor_id=serializer.validated_data["doctor_id"],
            starts_at=serializer.validated_data["starts_at"],
            reason=serializer.validated_data.get("reason", ""),
            notes=serializer.validated_data.get("notes", ""),
            request=request,
        )

        return Response(
            AppointmentSerializer(appointment).data,
            status=status.HTTP_201_CREATED,
        )


class AppointmentDetailView(APIView):
    permission_classes = [IsAuthenticatedUser]

    def get_object(self, appointment_id, user):
        try:
            appointment = Appointment.objects.select_related("patient", "doctor").get(id=appointment_id)
        except Appointment.DoesNotExist:
            raise NotFound(f"Appointment with ID {appointment_id} not found.")

        # Object-level authorization check (Correction 10)
        is_owner_patient = appointment.patient == user
        is_assigned_doctor = appointment.doctor == user
        is_admin = user.role == User.Roles.ADMIN or user.is_superuser

        if not (is_owner_patient or is_assigned_doctor or is_admin):
            raise PermissionDenied("You are not authorized to access this appointment.")

        return appointment

    def get(self, request, appointment_id):
        appointment = self.get_object(appointment_id, request.user)
        return Response(AppointmentSerializer(appointment).data, status=status.HTTP_200_OK)

    def patch(self, request, appointment_id):
        appointment = self.get_object(appointment_id, request.user)
        serializer = AppointmentUpdateSerializer(appointment, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)

        updated = update_appointment(
            appointment=appointment,
            validated_data=serializer.validated_data,
            acting_user=request.user,
            request=request,
        )
        return Response(AppointmentSerializer(updated).data, status=status.HTTP_200_OK)
