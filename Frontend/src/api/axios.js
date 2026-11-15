import axios from "axios";

const getBaseUrl = () => {
  const envUrl = import.meta.env.VITE_API_BASE_URL || import.meta.env.VITE_API_URL;
  if (envUrl) {
    // Prevent insecure mixed-content HTTP downgrade in production HTTPS contexts
    if (
      typeof window !== "undefined" &&
      window.location.protocol === "https:" &&
      envUrl.startsWith("http://") &&
      !envUrl.includes("localhost") &&
      !envUrl.includes("127.0.0.1")
    ) {
      return envUrl.replace("http://", "https://");
    }
    return envUrl;
  }
  if (typeof window !== "undefined" && window.location.hostname !== "localhost" && window.location.hostname !== "127.0.0.1") {
    return `${window.location.protocol}//${window.location.hostname}:8000`;
  }
  return "http://127.0.0.1:8000";
};

const apiClient = axios.create({
  baseURL: getBaseUrl(),
  headers: { "Content-Type": "application/json" },
});

apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem("campusPulseToken");
  const isAuthEndpoint =
    config.url?.includes("/auth/login") ||
    config.url?.includes("/auth/forgot-password") ||
    config.url?.includes("/auth/activate") ||
    config.url?.includes("/auth/reset-password");
  if (token && !isAuthEndpoint) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    const isAuthEndpoint =
      error?.config?.url?.includes("/auth/login") ||
      error?.config?.url?.includes("/auth/forgot-password") ||
      error?.config?.url?.includes("/auth/activate") ||
      error?.config?.url?.includes("/auth/reset-password");

    // Only dispatch session expired if it's 401 on an authenticated resource AND a token was present
    if (
      error.response?.status === 401 &&
      !isAuthEndpoint &&
      localStorage.getItem("campusPulseToken")
    ) {
      localStorage.removeItem("campusPulseToken");
      localStorage.removeItem("campusPulseUser");
      localStorage.removeItem("activeRole");
      window.dispatchEvent(new Event("session-expired"));
    }

    // 403 Account Deactivated or Institution Inactive - clear session and redirect to access denied
    if (
      error.response?.status === 403 &&
      (error.response?.data?.detail?.includes("deactivated") ||
        error.response?.data?.detail?.includes("inactive") ||
        error.response?.data?.detail?.includes("suspended"))
    ) {
      localStorage.removeItem("campusPulseToken");
      localStorage.removeItem("campusPulseUser");
      localStorage.removeItem("activeRole");
      window.dispatchEvent(new Event("account-deactivated"));
    }

    return Promise.reject(error);
  }
);

export const getApiError = (error, defaultMsg = "An unexpected error occurred.") => {
  if (typeof error === "string") return error;
  return error?.response?.data?.detail || error?.message || defaultMsg;
};

export default apiClient;
