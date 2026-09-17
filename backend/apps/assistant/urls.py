from django.urls import path
from .views import AssistantHistoryView, AssistantChatView

urlpatterns = [
    path("chat/", AssistantChatView.as_view(), name="assistant-chat"),
    path("history/", AssistantHistoryView.as_view(), name="assistant-history"),
]
