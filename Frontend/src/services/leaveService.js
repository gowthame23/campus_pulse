import apiClient from "../api/axios";

export const leaveService = {
  setLeave: (payload) => apiClient.post("/leaves", payload),
  getMyLeaves: (activeOnly = false) => apiClient.get("/leaves/my", { params: { active_only: activeOnly } }),
  list: (params = {}) => apiClient.get("/leaves", { params }),
  cancelLeave: (leaveId) => apiClient.delete(`/leaves/${leaveId}`),
};

