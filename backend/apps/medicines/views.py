from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied, NotFound, ValidationError
from core.permissions import IsAuthenticatedUser, doctor_can_access_patient
from core.pagination import StandardResultsSetPagination
from apps.accounts.models import User
from .models import Medication
from .serializers import MedicationSerializer


class MedicationListCreateView(APIView):
    permission_classes = [IsAuthenticatedUser]

    def get(self, request):
        user = request.user
        queryset = Medication.objects.select_related("patient", "prescribed_by")

        if user.role == User.Roles.PATIENT:
            queryset = queryset.filter(patient=user)
        elif user.role == User.Roles.DOCTOR:
            patient_id = request.query_params.get("patient_id")
            if not patient_id:
                raise ValidationError("Query param 'patient_id' is required for doctors.")
            try:
                patient = User.objects.get(id=patient_id, role=User.Roles.PATIENT)
            except User.DoesNotExist:
                raise NotFound("Patient not found.")
            if not doctor_can_access_patient(user, patient):
                raise PermissionDenied("Unauthorized to view this patient's medications.")
            queryset = queryset.filter(patient=patient)
        elif user.role == User.Roles.ADMIN or user.is_superuser:
            pass
        else:
            raise PermissionDenied("Access denied.")

        active_filter = request.query_params.get("is_active")
        if active_filter is not None:
            queryset = queryset.filter(is_active=active_filter.lower() == "true")

        paginator = StandardResultsSetPagination()
        page = paginator.paginate_queryset(queryset, request)
        serializer = MedicationSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)

    def post(self, request):
        user = request.user
        data = request.data.copy()

        if user.role == User.Roles.PATIENT:
            target_patient = user
            prescriber = None
        elif user.role == User.Roles.DOCTOR:
            patient_id = data.get("patient_id")
            if not patient_id:
                raise ValidationError("Field 'patient_id' is required.")
            try:
                target_patient = User.objects.get(id=patient_id, role=User.Roles.PATIENT)
            except User.DoesNotExist:
                raise NotFound("Patient not found.")
            if not doctor_can_access_patient(user, target_patient):
                raise PermissionDenied("Doctor does not have active clinical authorization for this patient.")
            prescriber = user
        else:
            raise PermissionDenied("Only patients or doctors can add medications.")

        serializer = MedicationSerializer(data=data, context={"request": request, "target_patient": target_patient})
        serializer.is_valid(raise_exception=True)

        medication = Medication.objects.create(
            patient=target_patient,
            prescribed_by=prescriber,
            name=serializer.validated_data["name"],
            dosage=serializer.validated_data.get("dosage", ""),
            frequency=serializer.validated_data.get("frequency", ""),
            start_date=serializer.validated_data.get("start_date"),
            end_date=serializer.validated_data.get("end_date"),
            is_active=serializer.validated_data.get("is_active", True),
            notes=serializer.validated_data.get("notes", ""),
        )

        return Response(MedicationSerializer(medication).data, status=status.HTTP_201_CREATED)


class MedicationDetailView(APIView):
    permission_classes = [IsAuthenticatedUser]

    def get(self, request, medication_id):
        try:
            medication = Medication.objects.select_related("patient", "prescribed_by").get(id=medication_id)
        except Medication.DoesNotExist:
            raise NotFound(f"Medication with ID {medication_id} not found.")

        user = request.user
        if user.role == User.Roles.PATIENT and medication.patient != user:
            raise PermissionDenied("Unauthorized to access another patient's medication.")
        elif user.role == User.Roles.DOCTOR and not doctor_can_access_patient(user, medication.patient):
            raise PermissionDenied("Unauthorized to access this medication.")

        return Response(MedicationSerializer(medication).data, status=status.HTTP_200_OK)

    def patch(self, request, medication_id):
        try:
            medication = Medication.objects.select_related("patient").get(id=medication_id)
        except Medication.DoesNotExist:
            raise NotFound(f"Medication with ID {medication_id} not found.")

        user = request.user
        if user.role == User.Roles.PATIENT and medication.patient != user:
            raise PermissionDenied("Unauthorized.")
        elif user.role == User.Roles.DOCTOR and not doctor_can_access_patient(user, medication.patient):
            raise PermissionDenied("Unauthorized.")

        serializer = MedicationSerializer(medication, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)


class OpenFDAReactionsView(APIView):
    """
    GET /api/v1/medicines/openfda/reactions/?drug=<name>
    Retrieves adverse drug reactions and boxed warnings from OpenFDA.
    """
    permission_classes = [IsAuthenticatedUser]

    def get(self, request):
        drug_name = request.query_params.get("drug", "").strip()
        if not drug_name:
            raise ValidationError("Query parameter 'drug' is required.")

        limit_param = request.query_params.get("limit", "5")
        try:
            limit = max(1, min(20, int(limit_param)))
        except ValueError:
            limit = 5

        from .services.openfda_service import openfda_service

        reactions_data = openfda_service.get_adverse_reactions(drug_name, limit=limit)
        warnings_data = openfda_service.get_boxed_warnings_and_precautions(drug_name)

        return Response(
            {
                "drug": drug_name,
                "adverse_reactions": reactions_data.get("adverse_reactions", []),
                "total_reactions": reactions_data.get("total_reactions_reported", 0),
                "has_boxed_warning": warnings_data.get("has_boxed_warning", False),
                "boxed_warnings": warnings_data.get("boxed_warnings", []),
                "precautions": warnings_data.get("precautions", []),
                "status": reactions_data.get("status", "success"),
                "cached": reactions_data.get("cached", False) or warnings_data.get("cached", False),
            },
            status=status.HTTP_200_OK,
        )


class OpenFDAInteractionsView(APIView):
    """
    POST /api/v1/medicines/openfda/interactions/
    Evaluates pairwise drug-drug interactions for a list of medication names.
    """
    permission_classes = [IsAuthenticatedUser]

    def post(self, request):
        drugs = request.data.get("drugs")
        if not drugs or not isinstance(drugs, list):
            raise ValidationError("Field 'drugs' must be a non-empty list of drug names.")

        from .services.openfda_service import openfda_service

        interactions_data = openfda_service.check_interactions(drugs)
        return Response(interactions_data, status=status.HTTP_200_OK)

