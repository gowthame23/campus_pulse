import apiClient from "../api/axios";

export const authService = {
  login: (payload) => apiClient.post("/auth/login", payload),
  logout: (token) =>
    apiClient.post(
      "/auth/logout",
      {},
      token ? { headers: { Authorization: `Bearer ${token}` } } : undefined,
    ),
  me: () => apiClient.get("/auth/me"),
  changePassword: (payload) => apiClient.post("/auth/change-password", payload),
  resetPassword: (payload) => apiClient.post("/auth/reset-password", payload),
  requestPasswordReset: (payload) =>
    apiClient.post("/auth/password-reset/request", payload),
  verifyPasswordReset: (payload) =>
    apiClient.post("/auth/password-reset/verify", payload),
  completePasswordReset: (payload) =>
    apiClient.post("/auth/password-reset/complete", payload),
  verifyActivation: (token) =>
    apiClient.get("/auth/activate/verify", { params: { token } }),
  completeActivation: (payload) =>
    apiClient.post("/auth/activate/complete", payload),
};
