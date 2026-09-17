import api from "./api";

export const doctorService = {
  /**
   * Retrieves aggregated clinical insights and operational figures for the doctor's dashboard.
   */
  async getDashboard() {
    const response = await api.get("/doctor/dashboard/");
    return response.data;
  },

  /**
   * Retrieves active, authorized patient roster linked to this doctor.
   */
  async getPatients() {
    const response = await api.get("/doctor/patients/");
    return response.data.results || response.data;
  },

  /**
   * Retrieves full profile details for an authorized patient.
   */
  async getPatientDetails(patientId) {
    const response = await api.get(`/doctor/patients/${patientId}/`);
    return response.data;
  },

  /**
   * Retrieves medical records for an authorized patient.
   */
  async getPatientRecords(patientId) {
    const response = await api.get(`/doctor/patients/${patientId}/records/`);
    return response.data.results || response.data;
  },

  /**
   * Retrieves diagnostic lab reports for an authorized patient.
   */
  async getPatientReports(patientId) {
    const response = await api.get(`/doctor/patients/${patientId}/reports/`);
    return response.data.results || response.data;
  },

  /**
   * Retrieves clinical observation notes for an authorized patient.
   */
  async getPatientNotes(patientId) {
    const response = await api.get(`/doctor/patients/${patientId}/clinical-notes/`);
    return response.data;
  },

  /**
   * Records a clinical observation note for an authorized patient.
   * payload: { note: "...", diagnosis: "..." }
   */
  async createClinicalNote(patientId, payload) {
    const response = await api.post(
      `/doctor/patients/${patientId}/clinical-notes/`,
      payload
    );
    return response.data;
  },

  /**
   * Prescribes a new medication for an authorized patient.
   * payload: { patient_id, name, dosage, frequency, notes }
   */
  async prescribeMedication(payload) {
    const response = await api.post("/medicines/", payload);
    return response.data;
  },

  /**
   * Retrieves all appointments scheduled with this doctor.
   */
  async getAppointments() {
    const response = await api.get("/doctor/appointments/");
    return response.data.results || response.data;
  },

  /**
   * Updates the status of an appointment (e.g. 'confirmed', 'completed', 'cancelled').
   */
  async updateAppointmentStatus(appointmentId, status) {
    const response = await api.patch(`/appointments/${appointmentId}/`, {
      status,
    });
    return response.data;
  },

  /**
   * Retrieves doctor's own profile.
   */
  async getProfile() {
    const response = await api.get("/doctor/profile/");
    return response.data;
  },

  /**
   * Updates doctor's own profile.
   */
  async updateProfile(payload) {
    const response = await api.patch("/doctor/profile/", payload);
    return response.data;
  },
};

export default doctorService;
