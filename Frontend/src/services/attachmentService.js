import apiClient from "../api/axios";

export const attachmentService = {
  list: (complaintId) =>
    apiClient.get(`/complaints/${complaintId}/attachments`),
  download: (complaintId, attachmentId) =>
    apiClient.get(
      `/complaints/${complaintId}/attachments/${attachmentId}/download`,
      { responseType: "blob" },
    ),
  upload: (complaintId, files, category = "Additional") => {
    const formData = new FormData();
    files.forEach((file) => {
      formData.append("files", file);
    });
    formData.append("category", category);
    return apiClient.post(`/complaints/${complaintId}/attachments`, formData, {
      headers: {
        "Content-Type": "multipart/form-data",
      },
    });
  },
  delete: (complaintId, attachmentId) =>
    apiClient.delete(`/complaints/${complaintId}/attachments/${attachmentId}`),
};
