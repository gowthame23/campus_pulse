import apiClient from "../api/axios";

export const teamService = {
  list: (params = {}) => apiClient.get("/teams", { params }),
  getById: (teamId) => apiClient.get(`/teams/${teamId}`),
  getMembers: (teamId) => apiClient.get(`/teams/${teamId}/members`),
  getCoverageGaps: () => apiClient.get("/teams/coverage-gaps"),
  create: (payload) => apiClient.post("/teams", payload),
  update: (teamId, payload) => apiClient.put(`/teams/${teamId}`, payload),
  deactivate: (teamId) => apiClient.delete(`/teams/${teamId}`),
  getEligibleCoordinators: (teamId, position) =>
    apiClient.get("/teams/eligible-coordinators", { params: { team_id: teamId, position } }),
  getWorkMemberships: (params = {}) => apiClient.get("/teams/work-memberships", { params }),
  assignWorkMembership: (payload) => apiClient.post("/teams/work-memberships", payload),
  removeWorkMembership: (membershipId) =>
    apiClient.delete(`/teams/work-memberships/${membershipId}`),
  getEmployeesOverview: () => apiClient.get("/teams/employees-overview"),
  listEmployeesOverview: () => apiClient.get("/teams/employees-overview"),
};

