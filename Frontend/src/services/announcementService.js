import apiClient from "../api/axios";

export const announcementService = {
  list: (params) => apiClient.get("/announcements", { params }),
  search: (params) => apiClient.get("/announcements/search", { params }),
  getById: (announcementId) =>
    apiClient.get(`/announcements/${announcementId}`),
  create: (data) => apiClient.post("/announcements", data),
  update: (announcementId, data) =>
    apiClient.put(`/announcements/${announcementId}`, data),
  delete: (announcementId) =>
    apiClient.delete(`/announcements/${announcementId}`),

  publish: (announcementId) =>
    apiClient.put(`/announcements/${announcementId}/publish`),
  schedule: (announcementId, data) =>
    apiClient.put(`/announcements/${announcementId}/schedule`, data),
  cancel: (announcementId) =>
    apiClient.put(`/announcements/${announcementId}/cancel`),
  archive: (announcementId) =>
    apiClient.put(`/announcements/${announcementId}/archive`),
  restore: (announcementId) =>
    apiClient.put(`/announcements/${announcementId}/restore`),

  addAttachment: (announcementId, data) =>
    apiClient.post(`/announcements/${announcementId}/attachments`, data),
  getAttachments: (announcementId) =>
    apiClient.get(`/announcements/${announcementId}/attachments`),

  markRead: (announcementId) =>
    apiClient.put(`/announcements/${announcementId}/read`),
  getReadership: (announcementId) =>
    apiClient.get(`/announcements/${announcementId}/reads`),
  acknowledge: (announcementId, data) =>
    apiClient.put(`/announcements/${announcementId}/acknowledge`, data),
  getAdminContact: () => apiClient.get("/announcements/admin-contact"),
};
