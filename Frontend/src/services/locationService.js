import apiClient from "../api/axios";

export const locationService = {
  list: (params) => apiClient.get("/locations", { params }),
  listTypes: (params) => apiClient.get("/locations/types", { params }),
  createType: (payload) => apiClient.post("/locations/types", payload),
  getById: (locationId) => apiClient.get(`/locations/${locationId}`),
  create: (payload) => apiClient.post("/locations", payload),
  update: (locationId, payload) =>
    apiClient.patch(`/locations/${locationId}`, payload),
  delete: (locationId) => apiClient.delete(`/locations/${locationId}`),
  assignAppManager: (locationId, appManagerId) =>
    apiClient.post(`/locations/${locationId}/app-manager`, {
      app_manager_id: appManagerId,
    }),
  unassignAppManager: (locationId) =>
    apiClient.delete(`/locations/${locationId}/app-manager`),
  assignInCharge: (locationId, inChargeId) =>
    apiClient.post(`/locations/${locationId}/in-charge`, {
      in_charge_id: inChargeId,
    }),
  listInChargeAssignments: () =>
    apiClient.get("/locations/in-charge/assignments"),
  unassignInCharge: (locationId) =>
    apiClient.delete(`/locations/${locationId}/in-charge`),
  assignCoordinator: (locationId, coordinatorId) =>
    apiClient.post(`/locations/${locationId}/coordinator`, {
      coordinator_id: coordinatorId,
    }),
  unassignCoordinator: (locationId) =>
    apiClient.delete(`/locations/${locationId}/coordinator`),
};
