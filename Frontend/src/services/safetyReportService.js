import apiClient from "../api/axios";

export const safetyReportService = {
  getStatus: () => apiClient.get("/safety-reports/status"),
  list: () => apiClient.get("/safety-reports"),
  getByCaseCode: (caseCode) => apiClient.get(`/safety-reports/${caseCode}`),
  create: (payload) => apiClient.post("/safety-reports", payload),
  sendMessage: (caseCode, body) =>
    apiClient.post(`/safety-reports/${caseCode}/messages`, { body }),
  decide: (reportId, outcome, reason = "") =>
    apiClient.post(`/safety-reports/${reportId}/decision`, { outcome, reason }),
  reveal: (reportId, reason) =>
    apiClient.post(`/safety-reports/${reportId}/reveal`, { reason }),
};

