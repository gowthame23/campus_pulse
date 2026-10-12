import apiClient from "../api/axios";

export const emergencyService = {
  getCategories: (activeOnly = true) =>
    apiClient.get("/emergency/categories", { params: { active_only: activeOnly } }),

  createCategory: (payload) =>
    apiClient.post("/emergency/categories", payload),

  updateCategory: (categoryId, payload) =>
    apiClient.put(`/emergency/categories/${categoryId}`, payload),

  deleteCategory: (categoryId) =>
    apiClient.delete(`/emergency/categories/${categoryId}`),

  getContacts: (params = {}) =>
    apiClient.get("/emergency/contacts", { params }),

  createContact: (payload) =>
    apiClient.post("/emergency/contacts", payload),

  updateContact: (contactId, payload) =>
    apiClient.put(`/emergency/contacts/${contactId}`, payload),

  deleteContact: (contactId) =>
    apiClient.delete(`/emergency/contacts/${contactId}`),

  getStatus: () =>
    apiClient.get("/emergency/status"),

  getCallList: (category, locationId = null) =>
    apiClient.get("/emergency/call-list", {
      params: { category, location_id: locationId },
    }),

  createEmergency: (payload) =>
    apiClient.post("/emergency/create", payload),

  recordReached: (complaintId, reached) =>
    apiClient.post(`/emergency/complaints/${complaintId}/reached`, { reached }),

  acknowledgeEmergency: (complaintId) =>
    apiClient.post(`/emergency/complaints/${complaintId}/acknowledge`),

  markOutcome: (complaintId, outcome) =>
    apiClient.post(`/emergency/complaints/${complaintId}/outcome`, { outcome }),

  getPinnedEmergencies: () =>
    apiClient.get("/emergency/pinned"),

  getStats: () =>
    apiClient.get("/emergency/stats"),
};
