import apiClient from "../api/axios";

export const userService = {
  list: (role) => apiClient.get("/users", { params: role ? { role } : {} }),
  getById: (userId) => apiClient.get(`/users/${userId}`),
  create: (payload) => apiClient.post("/users", payload),
  update: (userId, payload) => apiClient.patch(`/users/${userId}`, payload),

  // Enforced v1.0 Admin / App Manager workflows
  toggleStatus: (userId, active) =>
    apiClient.patch(`/users/${userId}/status`, {
      status: active ? "Active" : "Inactive",
    }),
  updateStatus: (userId, status) =>
    apiClient.patch(`/users/${userId}/status`, { status }),
  resetPassword: (userId, newPassword) =>
    apiClient.put(`/users/${userId}/reset-password`, {
      new_password: newPassword,
    }),
  getDeletionImpact: (userId) =>
    apiClient.get(`/users/${userId}/deletion-impact`),
  forceDelete: (userId) => apiClient.delete(`/users/${userId}`),
  listRecycleBin: () => apiClient.get("/users/recycle-bin"),
  restoreUser: (userId) => apiClient.post(`/users/${userId}/restore`),
  exportUsers: (params) =>
    apiClient.get("/users/export", { params, responseType: "blob" }),
  downloadSampleTemplate: (format = "csv") =>
    apiClient.get("/users/import/sample-template", {
      params: { format },
      responseType: "blob",
    }),
  importUsers: (file, options = {}) => {
    const formData = new FormData();
    formData.append("file", file);
    const params = {};
    if (options.default_program) params.default_program = options.default_program;
    if (options.default_academic_year) params.default_academic_year = options.default_academic_year;
    if (options.default_year) params.default_year = options.default_year;
    if (options.default_location_id) params.default_location_id = options.default_location_id;
    if (options.update_existing !== undefined) params.update_existing = options.update_existing;
    return apiClient.post("/users/import", formData, {
      params,
      headers: {
        "Content-Type": "multipart/form-data",
      },
    });
  },
};

