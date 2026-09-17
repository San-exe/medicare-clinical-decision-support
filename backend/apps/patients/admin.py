from django.contrib import admin
from .models import PatientProfile


@admin.register(PatientProfile)
class PatientProfileAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "gender", "blood_group", "phone", "created_at")
    search_fields = ("user__email", "phone", "emergency_contact")
    list_filter = ("gender", "blood_group")
    readonly_fields = ("created_at", "updated_at")
