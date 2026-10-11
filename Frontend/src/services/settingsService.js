import apiClient from "../api/axios";

export const settingsService = {
  getAll: () => apiClient.get("/settings"),
  getCategory: (category) => apiClient.get(`/settings/${category}`),
  getByKey: (settingKey) => apiClient.get(`/settings/key/${settingKey}`),
  updateKey: (settingKey, data) =>
    apiClient.put(`/settings/key/${settingKey}`, data),
  bulkUpdate: (data) => apiClient.put("/settings", data),
  resetCategory: (category) => apiClient.post(`/settings/${category}/reset`),
  resetAll: (data = {}) => apiClient.post("/settings/reset-all", data),

  // Existing helpers
  getDuplicates: () => apiClient.get("/settings/duplicates"),
  resolveDuplicate: (payload) =>
    apiClient.post("/settings/resolve-duplicate", payload),
  getConfig: () => apiClient.get("/settings"),
  updateConfig: (payload) => apiClient.put("/settings", payload),
  exportBackup: () => apiClient.get("/settings/backup"),
  restoreBackup: (payload) => apiClient.post("/settings/restore", payload),
};
