import apiClient from "../api/axios.js";

export const setupService = {
  getChecklist: async () => {
    const res = await apiClient.get("/setup/checklist");
    return res.data;
  },

  getTemplateBlob: async (type, format = "csv") => {
    const res = await apiClient.get(`/setup/import/template?type=${type}&format=${format}`, {
      responseType: "blob",
    });
    return res.data;
  },

  previewImport: async (type, file) => {
    const formData = new FormData();
    formData.append("file", file);
    formData.append("type", type);
    const res = await apiClient.post("/setup/import/preview", formData, {
      headers: { "Content-Type": "multipart/form-data" },
    });
    return res.data;
  },

  executeImport: async (type, file) => {
    const formData = new FormData();
    formData.append("file", file);
    formData.append("type", type);
    const res = await apiClient.post("/setup/import/execute", formData, {
      headers: { "Content-Type": "multipart/form-data" },
    });
    return res.data;
  },

  resetWorkerPassword: async (userId) => {
    const res = await apiClient.post(`/setup/workers/${userId}/reset-password`);
    return res.data;
  },

  resetTeamMemberPassword: async (teamId, userId) => {
    const res = await apiClient.post(`/teams/${teamId}/members/${userId}/reset-password`);
    return res.data;
  },
};

