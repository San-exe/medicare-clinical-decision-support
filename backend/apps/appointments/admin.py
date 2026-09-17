from django.contrib import admin
from .models import Appointment


@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = ("id", "patient", "doctor", "starts_at", "status", "created_at")
    list_filter = ("status", "starts_at", "created_at")
    search_fields = ("patient__email", "doctor__email", "reason", "notes")
    readonly_fields = ("created_at", "updated_at")
