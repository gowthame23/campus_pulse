import axios from "axios";

const apiClient = axios.create({
  baseURL:
    import.meta.env.VITE_API_BASE_URL ||
    import.meta.env.VITE_API_URL ||
    (typeof window !== "undefined" && window.location.hostname !== "localhost" && window.location.hostname !== "127.0.0.1"
      ? `${window.location.protocol}//${window.location.hostname}:8000`
      : "http://127.0.0.1:8000"),
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
      error?.response?.status === 401 &&
      error?.config?.headers?.Authorization &&
      !isAuthEndpoint
    ) {
      window.dispatchEvent(new CustomEvent("campus-pulse-session-expired"));
    }
    return Promise.reject(error);
  },
);

export function getApiError(error, fallback = "Something went wrong.") {
  const detail = error?.response?.data?.detail;
  if (typeof detail === "string" && detail.trim()) {
    return detail;
  }
  if (Array.isArray(detail) && detail.length > 0) {
    const messages = detail
      .map((item) => (typeof item === "string" ? item : item?.msg || item?.message))
      .filter(Boolean);
    if (messages.length > 0) {
      return messages.join("; ");
    }
  }
  if (detail && typeof detail === "object" && detail.msg) {
    return detail.msg;
  }
  return error?.message || fallback;
}

export default apiClient;
