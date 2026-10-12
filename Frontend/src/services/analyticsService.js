import apiClient from "../api/axios";

export const analyticsService = {
  getDashboard: () => apiClient.get("/analytics/dashboard"),
  getComplaints: (params) => apiClient.get("/analytics/complaints", { params }),
  getSla: (params) => apiClient.get("/analytics/sla", { params }),
  getDepartments: (params) =>
    apiClient.get("/analytics/departments", { params }),
  getCoordinators: (params) =>
    apiClient.get("/analytics/coordinators", { params }),
  getHostels: (params) => apiClient.get("/analytics/hostels", { params }),
  getUsers: () => apiClient.get("/analytics/users"),
  getNotifications: () => apiClient.get("/analytics/notifications"),
  getHealthMap: () => apiClient.get("/dashboard/health-map"),
  exportReport: (reportType, format = "csv", params = {}) =>
    apiClient.get("/analytics/export", {
      params: { report_type: reportType, format, ...params },
      responseType: "blob",
    }),
};
