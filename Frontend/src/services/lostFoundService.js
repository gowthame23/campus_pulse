import apiClient from "../api/axios";

export const lostFoundService = {
  listItems: (params) => apiClient.get("/lost-found/items", { params }),
  getItem: (itemId) => apiClient.get(`/lost-found/items/${itemId}`),
  createItem: (data) => apiClient.post("/lost-found/items", data),
  updateItem: (itemId, data) =>
    apiClient.put(`/lost-found/items/${itemId}`, data),
  deleteItem: (itemId) => apiClient.delete(`/lost-found/items/${itemId}`),

  getPhotoBlob: (itemId, filename) =>
    apiClient.get(`/lost-found/items/${itemId}/photo-file/${filename}`, {
      responseType: "blob",
    }),

  markReturned: (itemId) => apiClient.put(`/lost-found/items/${itemId}/return`),
};
