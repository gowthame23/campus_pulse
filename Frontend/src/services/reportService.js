import apiClient from "../api/axios";

export const reportService = {
  getTemplates: (params) => apiClient.get("/reports/templates", { params }),
  createTemplate: (data) => apiClient.post("/reports/templates", data),
  getSchedules: () => apiClient.get("/reports/schedules"),
  createSchedule: (data) => apiClient.post("/reports/schedules", data),

  listReports: (params) => apiClient.get("/reports", { params }),
  getSummary: () => apiClient.get("/reports/summary"),
  getReport: (reportId) => apiClient.get(`/reports/${reportId}`),
  generateReport: (data) => apiClient.post("/reports", data),
  downloadReport: (reportId) =>
    apiClient.get(`/reports/${reportId}/download`, { responseType: "blob" }),
};
