import apiClient from "../api/axios";

export const feedbackService = {
  getTemplates: (params) => apiClient.get("/feedback/templates", { params }),
  getTemplateQuestions: (templateId) =>
    apiClient.get(`/feedback/templates/${templateId}/questions`),

  listFeedback: (params) => apiClient.get("/feedback", { params }),
  getPendingServices: () => apiClient.get("/feedback/pending"),
  getAnalytics: () => apiClient.get("/feedback/analytics"),
  getReports: () => apiClient.get("/feedback/reports"),
  getById: (feedbackId) => apiClient.get(`/feedback/${feedbackId}`),

  submit: (data) => apiClient.post("/feedback", data),
  addResponse: (feedbackId, data) =>
    apiClient.post(`/feedback/${feedbackId}/response`, data),
  getResponses: (feedbackId) =>
    apiClient.get(`/feedback/${feedbackId}/responses`),
};
