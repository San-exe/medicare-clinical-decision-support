# MediCare SRS Traceability Matrix (PART 1)

This document maps all MediCare System Requirements Specification (SRS) items to the Part 1 backend implementation, files, endpoints, and automated tests.

---

## PART 1 — IMPLEMENTED REQUIREMENTS

| SRS Requirement | Description | Implemented Files / Components | Endpoint / Model | Automated Test | Status |
|---|---|---|---|---|---|
| **REQ-CORE-01** | Modular Django 5.x REST backend with PostgreSQL 16.x support | `config/settings.py`, `config/urls.py`, `manage.py` | Core project configuration | `test_health.py` | **COMPLETE** |
| **REQ-CORE-02** | Standardized JSON error response format without stack trace leakage | `core/exceptions.py`, `config/settings.py` | `custom_exception_handler` | `test_auth.py`, `test_medical_records.py` | **COMPLETE** |
| **REQ-CORE-03** | Standardized pagination on all collection endpoints | `core/pagination.py` | `StandardResultsSetPagination` (page_size=10, max=100) | `test_admin_and_audit.py` | **COMPLETE** |
| **REQ-CORE-04** | API Health check & Database connectivity verification | `config/urls.py`, `core/utilities.py` | `GET /api/v1/health/` | `test_health.py` | **COMPLETE** |
| **REQ-AUTH-01** | Custom User model using email as authentication identifier | `apps/accounts/models.py` | `User` (email unique, `USERNAME_FIELD="email"`) | `test_auth.py` | **COMPLETE** |
| **REQ-AUTH-02** | User roles (`patient`, `doctor`, `admin`) with separate permissions | `apps/accounts/models.py`, `core/permissions.py` | `User.Roles`, `IsPatient`, `IsDoctor`, `IsAdmin` | `test_permissions.py` | **COMPLETE** |
| **REQ-AUTH-03** | User registration with email uniqueness, password hashing & profile creation | `apps/accounts/serializers.py`, `apps/accounts/views.py`, `services.py` | `POST /api/v1/auth/register/` | `test_auth.py::test_registration_success` | **COMPLETE** |
| **REQ-AUTH-04** | User login with JWT access/refresh tokens embedding claims | `apps/accounts/serializers.py`, `apps/accounts/views.py` | `POST /api/v1/auth/login/` | `test_auth.py::test_login_success` | **COMPLETE** |
| **REQ-AUTH-05** | JWT token refresh mechanism | `apps/accounts/views.py`, `config/settings.py` | `POST /api/v1/auth/refresh/` | `test_auth.py::test_token_refresh` | **COMPLETE** |
| **REQ-AUTH-06** | Real logout with refresh-token blacklisting via SimpleJWT | `apps/accounts/views.py`, `apps/accounts/services.py` | `POST /api/v1/auth/logout/` | `test_auth.py::test_logout_and_blacklisting` | **COMPLETE** |
| **REQ-AUTH-07** | Authenticated user profile retrieval & role escalation prevention | `apps/accounts/views.py`, `apps/accounts/serializers.py` | `GET /api/v1/auth/me/`, `PATCH /api/v1/auth/me/` | `test_auth.py::test_me_endpoint_and_role_escalation_prevention` | **COMPLETE** |
| **REQ-PERM-01** | Separation of Application Admin from Django Staff (`is_staff != admin`) | `core/permissions.py` | `IsAdmin` | `test_permissions.py::test_is_staff_alone_does_not_grant_app_admin_access` | **COMPLETE** |
| **REQ-PERM-02** | Centralized Doctor-Patient authorization boundary | `core/permissions.py` | `doctor_can_access_patient` | `test_permissions.py::test_doctor_patient_authorization_boundary` | **COMPLETE** |
| **REQ-PERM-03** | Patient data isolation (cross-patient access forbidden) | `core/permissions.py`, `apps/medical_records/views.py` | `IsPatientOwner`, Object checks | `test_permissions.py::test_patient_data_isolation` | **COMPLETE** |
| **REQ-PAT-01** | Patient profile management | `apps/patients/models.py`, `apps/patients/views.py` | `GET /api/v1/patient/profile/`, `PATCH /api/v1/patient/profile/` | `test_patient_and_doctor_apis.py::test_patient_profile_get_and_patch` | **COMPLETE** |
| **REQ-PAT-02** | Database-backed patient dashboard aggregations | `apps/patients/services.py`, `apps/patients/views.py` | `GET /api/v1/patient/dashboard/` | `test_patient_and_doctor_apis.py::test_patient_dashboard_database_backed` | **COMPLETE** |
| **REQ-DOC-01** | Doctor profile management | `apps/doctors/models.py`, `apps/doctors/views.py` | `DoctorProfile`, `GET/PATCH /api/v1/doctor/profile/` | `test_models.py` | **COMPLETE** |
| **REQ-DOC-02** | Doctor patient access, records & lab report inspection | `apps/doctors/views.py`, `apps/doctors/services.py` | `GET /api/v1/doctor/patients/`, `.../records/`, `.../reports/` | `test_permissions.py`, `test_patient_and_doctor_apis.py` | **COMPLETE** |
| **REQ-DOC-03** | Clinical observation notes creation & retrieval | `apps/doctors/models.py`, `apps/doctors/views.py` | `POST /api/v1/doctor/patients/<id>/clinical-notes/` | `test_patient_and_doctor_apis.py::test_doctor_clinical_notes_and_insights` | **COMPLETE** |
| **REQ-DOC-04** | Database-backed doctor decision support insights | `apps/doctors/services.py`, `apps/doctors/views.py` | `GET /api/v1/doctor/insights/` | `test_patient_and_doctor_apis.py::test_doctor_clinical_notes_and_insights` | **COMPLETE** |
| **REQ-APT-01** | Appointment model, scheduling, status updates, doctor assignment | `apps/appointments/models.py`, `apps/appointments/views.py` | `GET /api/v1/appointments/`, `POST /api/v1/appointments/`, `PATCH /<id>/` | `test_patient_and_doctor_apis.py::test_appointment_booking_and_access` | **COMPLETE** |
| **REQ-REC-01** | Medical records persistence and object-level authorization | `apps/medical_records/models.py`, `apps/medical_records/views.py` | `MedicalRecord`, `GET /api/v1/records/`, `POST /api/v1/records/` | `test_permissions.py::test_patient_data_isolation` | **COMPLETE** |
| **REQ-LAB-01** | Strong lab report file validation (size, MIME, magic byte signatures) | `core/utilities.py`, `apps/medical_records/services.py` | `validate_uploaded_file` (PDF, JPEG, PNG, WebP) | `test_medical_records.py` | **COMPLETE** |
| **REQ-LAB-02** | Secure server-side filename generation and report storage | `core/utilities.py`, `apps/medical_records/views.py` | `POST /api/v1/records/reports/upload/`, `LabReport`, `LabResult` | `test_medical_records.py::test_valid_pdf_upload` | **COMPLETE** |
| **REQ-MED-01** | Medication model & patient prescription persistence | `apps/medicines/models.py`, `apps/medicines/views.py` | `Medication`, `GET /api/v1/medicines/`, `POST /api/v1/medicines/` | `test_models.py` | **COMPLETE** |
| **REQ-PRED-01**| Prediction & Symptom Analysis database storage foundation | `apps/predictions/models.py`, `apps/predictions/views.py` | `DiseasePrediction`, `SymptomAnalysis`, `GET /api/v1/predictions/` | `test_models.py` | **COMPLETE** |
| **REQ-ASST-01**| Assistant conversation & message storage foundation | `apps/assistant/models.py`, `apps/assistant/views.py` | `ChatConversation`, `ChatMessage`, `GET /api/v1/assistant/history/` | `test_models.py` | **COMPLETE** |
| **REQ-ADM-01**  | Administrator user management with pagination | `apps/admin_panel/views.py` | `GET /api/v1/admin/users/`, `PATCH /api/v1/admin/users/<id>/` | `test_admin_and_audit.py::test_admin_users_pagination` | **COMPLETE** |
| **REQ-ADM-02**  | Genuine database analytics across users, appointments, records | `apps/admin_panel/views.py` | `GET /api/v1/admin/analytics/` | `test_admin_and_audit.py::test_admin_analytics_genuine_database_counts` | **COMPLETE** |
| **REQ-AUD-01**  | Centralized server-controlled audit logging | `apps/audit_logs/models.py`, `apps/audit_logs/services.py` | `AuditLog`, `log_audit_event` | `test_admin_and_audit.py::test_audit_log_server_controlled` | **COMPLETE** |
| **REQ-DOCK-01** | Single canonical Docker, Docker Compose, Nginx deployment foundation | `Dockerfile`, `docker-compose.yml`, `deployment/nginx.conf` | Docker production stack | Manual & Schema Verification | **COMPLETE** |

---

## PART 2 — OUT OF SCOPE / NOT IMPLEMENTED

The following capabilities belong strictly to Part 2 and have intentionally **NOT** been implemented:

- **NLP Disease Classifier**: Natural language symptom extraction model — `PART 2 — NOT IMPLEMENTED`
- **Scikit-learn Prediction Models**: Supervised disease classifiers — `PART 2 — NOT IMPLEMENTED`
- **XGBoost Risk Models**: Gradient boosted diagnostic models — `PART 2 — NOT IMPLEMENTED`
- **Model Training / Fine-tuning Pipelines**: Training scripts and datasets — `PART 2 — NOT IMPLEMENTED`
- **SHAP Execution**: Feature importance explainability computation — `PART 2 — NOT IMPLEMENTED`
- **PubMed E-Utilities Client**: Biomedical literature search engine — `PART 2 — NOT IMPLEMENTED`
- **PubMed RAG Engine**: Retrieval-augmented generation for clinical literature — `PART 2 — NOT IMPLEMENTED`
- **OpenFDA Drug API Integration**: Drug label and adverse event lookup — `PART 2 — NOT IMPLEMENTED`
- **DrugBank Integration**: Drug interaction database client — `PART 2 — NOT IMPLEMENTED`
- **LLM Medical Assistant**: Generative clinical question answering — `PART 2 — NOT IMPLEMENTED`
- **OCR / Medical Report AI Processing**: Automated text parsing from lab PDFs — `PART 2 — NOT IMPLEMENTED`

---

## PART 3 — OUT OF SCOPE / NOT IMPLEMENTED

The following capabilities belong strictly to Part 3 and have intentionally **NOT** been implemented to protect the existing UI:

- **Full React Frontend API Integration**: Replacing mock data with live API endpoints — `PART 3 — NOT IMPLEMENTED`
- **UI Architecture Changes**: Redesigning themes, layouts, or routes — `PART 3 — NOT IMPLEMENTED`
- **State Management Migration**: Redesigning context or query hooks — `PART 3 — NOT IMPLEMENTED`
