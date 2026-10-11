import apiClient from "../api/axios";

export const programService = {
  list: () => apiClient.get("/programs"),
  create: (payload) => apiClient.post("/programs", payload),
  delete: (programId) => apiClient.delete(`/programs/${programId}`),
};
