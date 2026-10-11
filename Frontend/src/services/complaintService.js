import apiClient from "../api/axios";

export const complaintService = {
  list: (params = {}) => apiClient.get("/complaints", { params }),
  getById: (complaintId) => apiClient.get(`/complaints/${complaintId}`),
  create: (payload) => apiClient.post("/complaints", payload),
  update: (complaintId, payload) => apiClient.patch(`/complaints/${complaintId}`, payload),
  delete: (complaintId, reason = "") => apiClient.delete(`/complaints/${complaintId}`, { data: { reason } }),
  requestDeletion: (complaintId, reason) => apiClient.delete(`/complaints/${complaintId}`, { data: { reason } }),
  approveDeletion: (complaintId) => apiClient.post(`/complaints/${complaintId}/approve-deletion`),
  rejectDeletion: (complaintId) => apiClient.post(`/complaints/${complaintId}/reject-deletion`),
  assign: (complaintId, coordinatorId) =>
    apiClient.post(`/complaints/${complaintId}/assign`, {
      coordinator_id: coordinatorId,
    }),
  take: (complaintId) =>
    apiClient.post(`/complaints/${complaintId}/take`),
  updateStatus: (complaintId, status) =>
    apiClient.patch(`/complaints/${complaintId}/status`, { status }),
  resolve: (complaintId, notes) =>
    apiClient.post(`/complaints/${complaintId}/resolve`, { notes }),
  verify: (complaintId) => apiClient.post(`/complaints/${complaintId}/verify`),
  reopen: (complaintId, reason) =>
    apiClient.post(`/complaints/${complaintId}/reopen`, { reason }),
  analytics: () => apiClient.get("/complaints/analytics"),
  unassigned: () => apiClient.get("/complaints/unassigned"),
  changePriority: (complaintId, priority, reason) =>
    apiClient.patch(`/complaints/${complaintId}/priority`, {
      priority,
      reason,
    }),
  getComments: (complaintId) =>
    apiClient.get(`/complaints/${complaintId}/comments`),
  addComment: (complaintId, message, isInternal = false) =>
    apiClient.post(`/complaints/${complaintId}/comments`, {
      message,
      is_internal: isInternal,
    }),
  suggestions: (locationId, query) =>
    apiClient.get("/complaints/suggestions/list", {
      params: { location_id: locationId, q: query },
    }),
  markAffected: (complaintId) =>
    apiClient.post(`/complaints/${complaintId}/affected`),
  escalate: (complaintId, reason) =>
    apiClient.post(`/complaints/${complaintId}/escalate`, { reason }),
  getWorkload: () => apiClient.get("/complaints/workload"),
  getResolved: (params = {}) => apiClient.get("/complaints/resolved", { params }),
};

