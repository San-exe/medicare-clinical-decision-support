from django.contrib import admin
from .models import DoctorProfile, ClinicalNote


@admin.register(DoctorProfile)
class DoctorProfileAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "license_number", "specialization", "hospital", "is_verified", "created_at")
    list_filter = ("is_verified", "specialization")
    search_fields = ("user__email", "license_number", "hospital")
    readonly_fields = ("created_at", "updated_at")


@admin.register(ClinicalNote)
class ClinicalNoteAdmin(admin.ModelAdmin):
    list_display = ("id", "doctor", "patient", "diagnosis", "created_at")
    search_fields = ("doctor__email", "patient__email", "diagnosis", "note")
    list_filter = ("created_at",)
    readonly_fields = ("created_at", "updated_at")
