from django.urls import path
from .views import (
    MedicationListCreateView,
    MedicationDetailView,
    OpenFDAReactionsView,
    OpenFDAInteractionsView,
    MedicineInteractionView,
)

urlpatterns = [
    path("", MedicationListCreateView.as_view(), name="medication-list-create"),
    path("<int:medication_id>/", MedicationDetailView.as_view(), name="medication-detail"),
    path("interactions/", MedicineInteractionView.as_view(), name="medicine-interactions"),
    path("openfda/reactions/", OpenFDAReactionsView.as_view(), name="openfda-reactions"),
    path("openfda/interactions/", OpenFDAInteractionsView.as_view(), name="openfda-interactions"),
]

