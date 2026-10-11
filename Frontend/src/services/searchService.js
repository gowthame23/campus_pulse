import apiClient from "../api/axios";

export const searchService = {
  search: (params) => apiClient.get("/search", { params }),
  getSuggestions: (params) => apiClient.get("/search/suggestions", { params }),
  reindex: () => apiClient.post("/search/reindex"),

  getHistory: () => apiClient.get("/search/history"),
  clearHistory: () => apiClient.delete("/search/history"),

  getSavedSearches: () => apiClient.get("/search/saved"),
  saveSearch: (data) => apiClient.post("/search/saved", data),
  deleteSavedSearch: (savedSearchId) =>
    apiClient.delete(`/search/saved/${savedSearchId}`),
};
