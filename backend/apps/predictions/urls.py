from django.urls import path
from .views import (
    PredictionListView,
    SymptomAnalysisListView,
    DiseasePredictionCreateView,
)

urlpatterns = [
    path("", PredictionListView.as_view(), name="prediction-list"),
    path("symptoms/", SymptomAnalysisListView.as_view(), name="symptom-analysis-list"),
    path("disease/", DiseasePredictionCreateView.as_view(), name="disease-prediction-create"),
]
