import api from "./api";

export const patientService = {
  /**
   * Retrieves aggregated database metrics for the authenticated patient's dashboard.
   */
  async getDashboardSummary() {
    const response = await api.get("/patient/dashboard/");
    return response.data;
  },

  /**
   * Retrieves all appointments for the authenticated patient.
   */
  async getAppointments(status) {
    const params = status ? { status } : {};
    const response = await api.get("/patient/appointments/", { params });
    // DRF StandardResultsSetPagination returns { count, next, previous, results }
    return response.data.results || response.data;
  },

  /**
   * Retrieves list of available active doctors for appointment scheduling.
   */
  async getDoctors() {
    const response = await api.get("/doctor/list/");
    return response.data;
  },

  /**
   * Books a new appointment with an authorized doctor.
   * payload: { doctor_id, starts_at, reason, notes }
   */
  async bookAppointment(data) {
    const response = await api.post("/patient/appointments/", data);
    return response.data;
  },

  /**
   * Retrieves all clinical medical records for the authenticated patient.
   */
  async getMedicalRecords() {
    const response = await api.get("/patient/medical-records/");
    return response.data.results || response.data;
  },

  /**
   * Retrieves all lab reports and diagnostic test records for the patient.
   */
  async getLabReports() {
    const response = await api.get("/patient/lab-tests/");
    return response.data.results || response.data;
  },

  /**
   * Uploads a lab report file (PDF/Image) or clinical text.
   * Accepts FormData with 'file', 'title', 'notes', etc.
   */
  async uploadMedicalRecord(formData) {
    const response = await api.post("/patient/reports/upload/", formData, {
      headers: {
        "Content-Type": "multipart/form-data",
      },
    });
    return response.data;
  },

  /**
   * Runs the automated medical report parser and clinical metric extraction engine.
   */
  async analyzeLabReport(reportId) {
    const response = await api.post(`/records/${reportId}/analyze/`);
    return response.data;
  },

  /**
   * Retrieves active/past medications for the authenticated patient.
   */
  async getMedications(isActive) {
    const params = typeof isActive === "boolean" ? { is_active: isActive } : {};
    const response = await api.get("/medicines/", { params });
    return response.data.results || response.data;
  },

  /**
   * Adds a new medication entry.
   */
  async addMedication(data) {
    const response = await api.post("/medicines/", data);
    return response.data;
  },

  /**
   * Queries OpenFDA drug safety endpoints for adverse reactions and boxed warnings.
   */
  async getDrugReactions(drugName, limit = 5) {
    const response = await api.get("/medicines/openfda/reactions/", {
      params: {
        drug: drugName,
        limit,
      },
    });
    return response.data;
  },

  /**
   * Evaluates pairwise or multi-drug interactions against OpenFDA/DrugBank knowledge.
   * payload can be: { drugs: [...] } or { queried_drug: "...", patient_id?: number }
   */
  async checkInteractions(data) {
    const response = await api.post("/medicines/interactions/", data);
    return response.data;
  },

  /**
   * Retrieves authenticated patient profile.
   */
  async getProfile() {
    const response = await api.get("/patient/profile/");
    return response.data;
  },

  /**
   * Updates authenticated patient profile.
   */
  async updateProfile(data) {
    const response = await api.patch("/patient/profile/", data);
    return response.data;
  },
};

export default patientService;

