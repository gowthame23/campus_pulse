import apiClient from "../api/axios";

export const recognitionService = {
  getFixerOfTheMonth: (scope = "campus") =>
    apiClient.get("/recognitions/fixer-of-the-month", { params: { scope } }),
  getBadges: (coordinatorId = null) =>
    apiClient.get("/recognitions/badges", {
      params: coordinatorId ? { coordinator_id: coordinatorId } : {},
    }),
  getCertificate: (month = null, coordinatorId = null) =>
    apiClient.get("/recognitions/certificate", {
      params: { month, coordinator_id: coordinatorId },
    }),
};

