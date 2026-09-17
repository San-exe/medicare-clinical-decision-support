from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied, NotFound, ValidationError
from core.permissions import IsAuthenticatedUser, doctor_can_access_patient
from core.pagination import StandardResultsSetPagination
from apps.accounts.models import User
from .models import ChatConversation, ChatMessage
from .serializers import ChatConversationSerializer, ChatMessageSerializer


class AssistantChatView(APIView):
    """
    POST /api/v1/assistant/chat/
    Accepts prompt, optional conversation_id, and optional patient_id.
    Executes context-grounded RAG with PubMed citations and conversation persistence.
    """
    permission_classes = [IsAuthenticatedUser]

    def post(self, request):
        prompt = request.data.get("prompt", "").strip()
        if not prompt:
            raise ValidationError("Field 'prompt' cannot be empty.")

        conversation_id = request.data.get("conversation_id")
        patient_id = request.data.get("patient_id")
        patient_user = None

        # Resolve patient context & enforce permissions
        if patient_id:
            try:
                target_patient = User.objects.get(id=patient_id, role=User.Roles.PATIENT)
            except User.DoesNotExist:
                raise NotFound("Target patient does not exist.")

            if request.user.role == User.Roles.PATIENT and target_patient != request.user:
                raise PermissionDenied("Patients cannot access another patient's clinical context.")
            elif request.user.role == User.Roles.DOCTOR and not doctor_can_access_patient(request.user, target_patient):
                raise PermissionDenied("Doctor does not have active clinical authorization for this patient.")

            patient_user = target_patient
        elif request.user.role == User.Roles.PATIENT:
            patient_user = request.user

        # If conversation_id is provided, verify ownership
        if conversation_id:
            existing = ChatConversation.objects.filter(id=conversation_id).first()
            if not existing:
                raise NotFound(f"Conversation with ID {conversation_id} not found.")
            if existing.user != request.user:
                raise PermissionDenied("You cannot access another user's chat conversation.")

        from .services.rag_engine import rag_assistant_engine

        result = rag_assistant_engine.process_chat(
            user=request.user,
            prompt=prompt,
            patient_user=patient_user,
            conversation_id=conversation_id,
        )

        return Response(result, status=status.HTTP_200_OK)


class AssistantHistoryView(APIView):
    """
    GET /api/v1/assistant/history/
    Retrieves stored chat conversation history for authenticated user.
    """
    permission_classes = [IsAuthenticatedUser]

    def get(self, request):
        conversations = (
            ChatConversation.objects.filter(user=request.user)
            .prefetch_related("messages")
            .order_by("-updated_at")
        )
        paginator = StandardResultsSetPagination()
        page = paginator.paginate_queryset(conversations, request)
        serializer = ChatConversationSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)
