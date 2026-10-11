import apiClient from "../api/axios";

export const auditService = {
  getDashboard: () => apiClient.get("/audit/dashboard"),
  list: (params) => apiClient.get("/audit", { params }),
  getById: (auditId) => apiClient.get(`/audit/${auditId}`),
  getEntityTimeline: (entityType, entityId) =>
    apiClient.get(`/audit/entity/${entityType}/${entityId}`),
  exportLogs: (format = "csv", params = {}) =>
    apiClient.get("/audit/export", {
      params: { format, ...params },
      responseType: "blob",
    }),
  archiveLogs: (retentionDays = 180) =>
    apiClient.post("/audit/archive", null, {
      params: { retention_days: retentionDays },
    }),
};
