from rest_framework import serializers
from .models import DiseasePrediction, SymptomAnalysis


class DiseasePredictionSerializer(serializers.ModelSerializer):
    patient_email = serializers.EmailField(source="patient.email", read_only=True)

    class Meta:
        model = DiseasePrediction
        fields = [
            "id",
            "patient",
            "patient_email",
            "model_name",
            "model_version",
            "input_data",
            "predicted_condition",
            "confidence",
            "explanation",
            "created_at",
        ]
        read_only_fields = fields


class SymptomAnalysisSerializer(serializers.ModelSerializer):
    patient_email = serializers.EmailField(source="patient.email", read_only=True)

    class Meta:
        model = SymptomAnalysis
        fields = [
            "id",
            "patient",
            "patient_email",
            "symptoms_text",
            "result",
            "created_at",
        ]
        read_only_fields = fields
