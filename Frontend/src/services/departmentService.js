import apiClient from "../api/axios";

export const departmentService = {
  list: (params) => apiClient.get("/departments", { params }),
  getById: (departmentId) => apiClient.get(`/departments/${departmentId}`),
  create: (payload) => apiClient.post("/departments", payload),
  update: (departmentId, payload) =>
    apiClient.patch(`/departments/${departmentId}`, payload),
  delete: (departmentId) => apiClient.delete(`/departments/${departmentId}`),
  assignCoordinator: (departmentId, coordinatorId) =>
    apiClient.post(`/departments/${departmentId}/coordinator`, {
      coordinator_id: coordinatorId || "",
      confirm_replacement: true,
    }),
  assignDepartmentCoordinators: (departmentId, payload) =>
    apiClient.put(`/departments/${departmentId}/coordinators`, payload),
  getEligibleCoordinators: (departmentId) =>
    apiClient.get(`/departments/${departmentId}/eligible-coordinators`),

  listAssignments: (params) =>
    apiClient.get("/departments/coordinators/assignments", { params }),
  assignCoordinatorPair: (payload) =>
    apiClient.post("/departments/coordinators/assignments", payload),
  removeAssignment: (assignmentId) =>
    apiClient.delete(`/departments/coordinators/assignments/${assignmentId}`),
  getUnassignedCombinations: () =>
    apiClient.get("/departments/coordinators/unassigned-combinations"),
  getCoverageGaps: () => apiClient.get("/departments/coverage-gaps"),
  getSlaConfig: (departmentId) => apiClient.get(`/departments/${departmentId}/sla-config`),
  updateSlaConfig: (departmentId, payload) => apiClient.put(`/departments/${departmentId}/sla-config`, payload),
  getOperatingLocations: (departmentId) => apiClient.get(`/departments/${departmentId}/locations`),
  assignLocations: (departmentId, locationIds) =>
    apiClient.put(`/departments/${departmentId}/locations`, {
      location_ids: locationIds,
    }),
  getEligibleEmployees: (departmentId) => apiClient.get(`/departments/${departmentId}/eligible-employees`),
};
