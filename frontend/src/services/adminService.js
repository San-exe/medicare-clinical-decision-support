import api from "./api";

export const adminService = {
  /**
   * Retrieves live platform analytics: total users, role breakdown, appointments, and predictions.
   */
  async getAnalytics() {
    const response = await api.get("/admin/analytics/");
    return response.data;
  },

  /**
   * Retrieves paginated user registry with optional filtering (role, search, is_active).
   */
  async getUsers(params = {}) {
    const response = await api.get("/admin/users/", { params });
    return response.data;
  },

  /**
   * Updates a user's account status (is_active, role, etc.).
   */
  async updateUserStatus(userId, payload) {
    const response = await api.patch(`/admin/users/${userId}/`, payload);
    return response.data;
  },

  /**
   * Retrieves immutable server-controlled audit trail logs.
   */
  async getAuditLogs(params = {}) {
    const response = await api.get("/admin/audit-logs/", { params });
    return response.data;
  },
};

export default adminService;
