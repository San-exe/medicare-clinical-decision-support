# MediCare: Intelligent Clinical Decision Support System — Backend (PART 1)

This repository contains the backend core for **MediCare**, an Intelligent Clinical Decision Support System (CDSS) built using Django 5.x, Django REST Framework, PostgreSQL 16.x, and SimpleJWT.

---

## 1. Architecture Overview

```
backend/
├── manage.py
├── requirements.txt
├── .env.example
├── README.md
├── MILESTONE_MAP.md
├── SRS_TRACEABILITY.md
├── Dockerfile                  # Single canonical Dockerfile
├── docker-compose.yml          # Single canonical Docker Compose configuration
│
├── config/
│   ├── __init__.py
│   ├── settings.py             # Django settings with PostgreSQL & JWT configuration
│   ├── urls.py                 # Health check & canonical API route registrations
│   ├── asgi.py
│   └── wsgi.py
│
├── core/
│   ├── __init__.py
│   ├── permissions.py          # IsPatient, IsDoctor, IsAdmin, doctor_can_access_patient
│   ├── exceptions.py           # Standardized JSON error response handler
│   ├── pagination.py           # StandardResultsSetPagination (page_size=10)
│   └── utilities.py            # DB ping, magic byte file validation, safe file naming
│
├── apps/
│   ├── accounts/               # Custom User (email-based), JWT Auth, Me endpoints
│   ├── patients/               # PatientProfile, DB-backed Dashboard aggregations
│   ├── doctors/                # DoctorProfile, ClinicalNote, Doctor Insights
│   ├── appointments/           # Appointment scheduling, status tracking, access control
│   ├── medical_records/        # MedicalRecord, LabReport, LabResult, multipart uploads
│   ├── predictions/            # DiseasePrediction & SymptomAnalysis storage models
│   ├── medicines/              # Medication model & prescription tracking
│   ├── assistant/              # ChatConversation & ChatMessage storage models
│   ├── audit_logs/             # AuditLog model & centralized server-side logging
│   └── admin_panel/            # Admin user management, DB analytics, audit viewer
│
├── deployment/
│   └── nginx.conf              # Single canonical Nginx reverse proxy configuration
│
└── tests/                      # Automated pytest test suite (29 tests)
```

---

## 2. Prerequisites & Setup

- **Python**: 3.12+ (3.13 supported)
- **PostgreSQL**: 16.x (or Docker)
- **Node.js**: 20+ (for protected React frontend)

### Installation & Local Setup

```powershell
# 1. Navigate to backend directory
cd backend

# 2. Configure environment variables
copy .env.example .env

# 3. Create and activate virtual environment
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# 4. Install dependencies
pip install -r requirements.txt

# 5. Run database migrations
python manage.py makemigrations
python manage.py migrate

# 6. Start development server
python manage.py runserver
```

---

## 3. Database Configuration

PostgreSQL is the primary database specified by the MediCare SRS.

Required environment variables:
- `DB_NAME` (or `POSTGRES_DB`)
- `DB_USER` (or `POSTGRES_USER`)
- `DB_PASSWORD` (or `POSTGRES_PASSWORD`)
- `DB_HOST` (or `POSTGRES_HOST`, default: `localhost`)
- `DB_PORT` (or `POSTGRES_PORT`, default: `5432`)

If any required PostgreSQL variables are missing, Django raises an explicit `ImproperlyConfigured` exception.

> **Note**: For running isolated unit tests without an active live PostgreSQL connection, set the explicit flag:
> ```powershell
> $env:USE_SQLITE_TESTS="true"
> ```

---

## 4. Authentication & Authorization

### Authentication Flow (SimpleJWT)
- **Email-based identifier**: The custom `User` model does not use usernames; emails are strictly unique.
- **Access token lifetime**: 30 minutes (configurable via `JWT_ACCESS_MINUTES`).
- **Refresh token lifetime**: 7 days (configurable via `JWT_REFRESH_DAYS`).
- **Token rotation & blacklisting**: Enabled. Logging out explicitly blacklists the refresh token.

### Application Roles & Permissions
- **Roles**: `patient`, `doctor`, `admin`.
- **Application Admin vs Django Staff**: `is_staff` does **NOT** equal application `admin`. Application API authorization requires `request.user.role == "admin"`.
- **Doctor-Patient Authorization Boundary**: Enforced via `doctor_can_access_patient(doctor, patient)`. Access is granted only if the doctor has an active/completed appointment, has authored clinical notes, or has prescribed medications for the patient.
- **Patient Data Isolation**: Object-level permissions prevent patients from accessing another patient's records or appointments.
- **Role Escalation Prevention**: Normal users cannot update their own role, `is_staff`, or `is_superuser` via request payloads.

---

## 5. API Endpoints Reference

All endpoints are prefixed with `/api/v1/`.

### Health & Auth
- `GET  /api/v1/health/` — Health & DB readiness check
- `POST /api/v1/auth/register/` — Register patient or doctor
- `POST /api/v1/auth/login/` — Obtain JWT access & refresh tokens
- `POST /api/v1/auth/refresh/` — Refresh access token
- `POST /api/v1/auth/logout/` — Blacklist refresh token
- `GET  /api/v1/auth/me/` — Retrieve authenticated user profile
- `PATCH /api/v1/auth/me/` — Update user profile

### Patient Workflows
- `GET   /api/v1/patient/profile/` — Own profile details
- `PATCH /api/v1/patient/profile/` — Update own profile
- `GET   /api/v1/patient/dashboard/` — Real DB-backed patient summary
- `GET   /api/v1/patient/appointments/` — List own appointments
- `POST  /api/v1/patient/appointments/` — Book an appointment
- `PATCH /api/v1/patient/appointments/<id>/` — Reschedule or cancel appointment
- `GET   /api/v1/patient/medical-records/` — List own medical records
- `GET   /api/v1/patient/lab-tests/` — List own lab reports & test results
- `POST  /api/v1/patient/reports/upload/` — Upload lab report (validated)
- `GET   /api/v1/patient/medications/` — List own medications
- `GET   /api/v1/patient/predictions/` — Prediction history
- `GET   /api/v1/patient/symptom-analyses/` — Symptom analysis history

### Doctor Workflows
- `GET  /api/v1/doctor/profile/` — Own doctor profile
- `PATCH /api/v1/doctor/profile/` — Update doctor profile
- `GET  /api/v1/doctor/patients/` — List authorized patients
- `GET  /api/v1/doctor/patients/<id>/` — Authorized patient detail
- `GET  /api/v1/doctor/patients/<id>/records/` — Authorized patient records
- `GET  /api/v1/doctor/patients/<id>/reports/` — Authorized patient reports
- `POST /api/v1/doctor/patients/<id>/clinical-notes/` — Record clinical note
- `GET  /api/v1/doctor/appointments/` — Scheduled appointments
- `GET  /api/v1/doctor/insights/` — Real DB-derived decision support metrics

### Admin Workflows
- `GET   /api/v1/admin/users/` — Paginated user list with filters
- `PATCH /api/v1/admin/users/<id>/` — Update user status / role
- `GET   /api/v1/admin/audit-logs/` — Paginated audit log records
- `GET   /api/v1/admin/analytics/` — Real DB-derived platform metrics

### Assistant Workflows
- `GET  /api/v1/assistant/history/` — Conversation & message history

---

## 6. Strong File Validation (Medical Reports)

Uploaded lab reports are verified by:
1. **File size**: Max 10 MB.
2. **File extension**: `.pdf`, `.jpeg`, `.jpg`, `.png`, `.webp`.
3. **MIME type**: `application/pdf`, `image/jpeg`, `image/png`, `image/webp`.
4. **Magic Byte Signatures**:
   - PDF: `%PDF`
   - PNG: `\x89PNG\r\n\x1a\n`
   - JPEG: `\xff\xd8\xff`
   - WebP: `RIFF...WEBP`
5. **Safe Storage**: Filenames are sanitized and saved using UUID4 server-side names under `media/reports/%Y/%m/`.

---

## 7. Running Automated Tests

Run the full pytest test suite:

```powershell
# Using SQLite test database for isolated testing
$env:USE_SQLITE_TESTS="true"
.\.venv\Scripts\pytest
```

**Test Results Summary**:
- Total tests: **29**
- Passed: **29 (100%)**
- Time: ~1.5 minutes

---

## 8. Docker Deployment

Single canonical Docker Compose configuration:

```bash
docker-compose up --build -d
```

Services:
- `db`: PostgreSQL 16 Alpine with healthcheck.
- `backend`: Gunicorn WSGI server running 3 workers.
- `nginx`: Alpine reverse proxy routing `/api/`, `/admin/`, `/static/`, `/media/`.
