import apiClient from "../api/axios";

export const notificationService = {
  list: (params) => apiClient.get("/notifications", { params }),
  listPaginated: (params) =>
    apiClient.get("/notifications/paginated", { params }),
  getUnreadCount: () => apiClient.get("/notifications/unread-count"),
  getById: (id) => apiClient.get(`/notifications/${id}`),
  clear: () => apiClient.delete("/notifications"),
  delete: (notificationId) =>
    apiClient.delete(`/notifications/${notificationId}`),
  markRead: (notificationId) =>
    apiClient.put(`/notifications/${notificationId}/read`),
  markAllRead: () => apiClient.put("/notifications/read-all"),
  getPreferences: () => apiClient.get("/notifications/preferences"),
  updatePreferences: (data) =>
    apiClient.put("/notifications/preferences", data),
};
