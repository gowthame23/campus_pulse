import apiClient from "../api/axios";

export const teamService = {
  list: (params = {}) => apiClient.get("/teams", { params }),
  getById: (teamId) => apiClient.get(`/teams/${teamId}`),
  getMembers: (teamId) => apiClient.get(`/teams/${teamId}/members`),
  getCoverageGaps: () => apiClient.get("/teams/coverage-gaps"),
  create: (payload) => apiClient.post("/teams", payload),
  update: (teamId, payload) => apiClient.put(`/teams/${teamId}`, payload),
  deactivate: (teamId) => apiClient.delete(`/teams/${teamId}`),
};

