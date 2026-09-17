from django.contrib import admin
from .models import Medication


@admin.register(Medication)
class MedicationAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "patient", "dosage", "frequency", "is_active", "start_date", "created_at")
    list_filter = ("is_active", "created_at")
    search_fields = ("name", "patient__email", "dosage")
