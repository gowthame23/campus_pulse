import apiClient from "../api/axios";

export const backupService = {
  getSummary: () => apiClient.get("/backups/summary"),
  listBackups: (params) => apiClient.get("/backups", { params }),
  getBackup: (backupId) => apiClient.get(`/backups/${backupId}`),
  createBackup: (data) => apiClient.post("/backups", data),
  downloadBackup: (backupId) =>
    apiClient.get(`/backups/${backupId}/download`, { responseType: "blob" }),

  verifyBackup: (backupId) => apiClient.post(`/backups/${backupId}/verify`),
  restoreBackup: (backupId) => apiClient.post(`/backups/${backupId}/restore`),
  listRestoreHistory: () => apiClient.get("/backups/restore-history"),
  listSchedules: () => apiClient.get("/backups/schedules"),
};
