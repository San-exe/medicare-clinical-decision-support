from django.utils import timezone
from rest_framework import serializers
from apps.accounts.models import User
from .models import Appointment


class AppointmentSerializer(serializers.ModelSerializer):
    patient_email = serializers.EmailField(source="patient.email", read_only=True)
    patient_name = serializers.SerializerMethodField()
    doctor_email = serializers.EmailField(source="doctor.email", read_only=True)
    doctor_name = serializers.SerializerMethodField()

    class Meta:
        model = Appointment
        fields = [
            "id",
            "patient",
            "patient_email",
            "patient_name",
            "doctor",
            "doctor_email",
            "doctor_name",
            "starts_at",
            "reason",
            "status",
            "notes",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "patient", "created_at", "updated_at"]

    def get_patient_name(self, obj):
        name = f"{obj.patient.first_name} {obj.patient.last_name}".strip()
        return name if name else obj.patient.email

    def get_doctor_name(self, obj):
        name = f"Dr. {obj.doctor.first_name} {obj.doctor.last_name}".strip()
        return name if name != "Dr." else f"Dr. {obj.doctor.email}"


class AppointmentCreateSerializer(serializers.ModelSerializer):
    doctor_id = serializers.IntegerField(write_only=True)

    class Meta:
        model = Appointment
        fields = ["doctor_id", "starts_at", "reason", "notes"]

    def validate_doctor_id(self, value):
        try:
            doctor = User.objects.get(id=value, role=User.Roles.DOCTOR, is_active=True)
        except User.DoesNotExist:
            raise serializers.ValidationError("A valid active doctor with this ID was not found.")
        return value

    def validate_starts_at(self, value):
        if value < timezone.now():
            raise serializers.ValidationError("Appointment time cannot be scheduled in the past.")
        return value


class AppointmentUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Appointment
        fields = ["status", "starts_at", "reason", "notes"]
