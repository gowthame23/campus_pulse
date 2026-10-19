import { createContext, useContext, useEffect, useMemo, useState } from "react";
import { authService } from "../services/authService";
import { complaintService } from "../services/complaintService";
import { pushService } from "../services/pushService";

const AuthContext = createContext(null);
const TOKEN_KEY = "campusPulseToken";
const USER_KEY = "campusPulseUser";
const SESSION_MESSAGE_KEY = "campusPulseSessionMessage";

function readStoredUser() {
  const value = localStorage.getItem(USER_KEY);
  if (!value) return null;
  try {
    const parsed = JSON.parse(value);
    if (parsed && typeof parsed.name === "string" && parsed.name.startsWith("=")) {
      parsed.name = "Student User";
      localStorage.setItem(USER_KEY, JSON.stringify(parsed));
    }
    return parsed;
  } catch {
    localStorage.removeItem(USER_KEY);
    return null;
  }
}

function readAndClearInitialSessionMessage() {
  try {
    // Read from sessionStorage (scoped to current tab only)
    const sMsg = sessionStorage.getItem(SESSION_MESSAGE_KEY);
    if (sMsg) {
      sessionStorage.removeItem(SESSION_MESSAGE_KEY);
      return sMsg;
    }
    // Also clean up any legacy message from localStorage so it never persists
    const lMsg = localStorage.getItem(SESSION_MESSAGE_KEY);
    if (lMsg) {
      localStorage.removeItem(SESSION_MESSAGE_KEY);
      return lMsg;
    }
  } catch {}
  return "";
}

export function AuthProvider({ children }) {
  const [token, setToken] = useState(localStorage.getItem(TOKEN_KEY));
  const [user, setUser] = useState(readStoredUser());
  const [initializing, setInitializing] = useState(
    Boolean(localStorage.getItem(TOKEN_KEY)),
  );
  const [sessionMessage, setSessionMessage] = useState(
    readAndClearInitialSessionMessage,
  );

  const clearSession = (message = "") => {
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(USER_KEY);
    try {
      localStorage.removeItem(SESSION_MESSAGE_KEY);
      if (message) {
        sessionStorage.setItem(SESSION_MESSAGE_KEY, message);
      } else {
        sessionStorage.removeItem(SESSION_MESSAGE_KEY);
      }
    } catch {}
    setToken(null);
    setUser(null);
    setSessionMessage(message);
  };

  useEffect(() => {
    const expire = () =>
      clearSession("Your session expired. Please login again.");
    window.addEventListener("campus-pulse-session-expired", expire);
    return () =>
      window.removeEventListener("campus-pulse-session-expired", expire);
  }, []);

  useEffect(() => {
    let active = true;
    async function restoreSession() {
      if (!token) {
        setInitializing(false);
        return;
      }
      try {
        const response = await authService.me();
        if (!active) return;
        localStorage.setItem(USER_KEY, JSON.stringify(response.data));
        setUser(response.data);
        window.dispatchEvent(new CustomEvent("campus-pulse-user-loaded", { detail: response.data }));
      } catch (error) {
        if (error.response?.status === 401) {
          clearSession("Your session expired. Please login again.");
        } else {
          // If server is restarting or network temporarily fails, DO NOT clear user session
          console.warn("Could not verify session with server:", error?.message);
        }
      } finally {
        if (active) setInitializing(false);
      }
    }
    restoreSession();
    return () => {
      active = false;
    };
  }, [token]);

  // WebSocket for real-time notifications (connect with single-use ticket)
  useEffect(() => {
    if (!token || !user) return; // only when authenticated
    let ws = null;
    let isCancelled = false;
    let reconnectTimeout = null;
    let reconnectAttempts = 0;

    async function connect() {
      if (isCancelled) return;
      try {
        const apiBase =
          import.meta.env.VITE_API_BASE_URL ||
          import.meta.env.VITE_API_URL ||
          "http://127.0.0.1:8000";
        const wsBase = apiBase.replace(/^http/, "ws");
        const wsUrl = `${wsBase.replace(/\/$/, "")}/notifications/ws/${user.user_id}`;

        let queryParam = "";
        try {
          const ticketRes = await complaintService.getWsTicket();
          if (ticketRes?.data?.ticket) {
            queryParam = `ticket=${encodeURIComponent(ticketRes.data.ticket)}`;
          }
        } catch {
          // Fallback to token if ticket endpoint is unavailable
          const authToken = localStorage.getItem(TOKEN_KEY);
          if (authToken) {
            queryParam = `token=${encodeURIComponent(authToken)}`;
          }
        }

        if (isCancelled) return;

        const sep = wsUrl.includes("?") ? "&" : "?";
        const fullWsUrl = queryParam ? `${wsUrl}${sep}${queryParam}` : wsUrl;
        ws = new WebSocket(fullWsUrl);

        ws.addEventListener("open", () => {
          if (reconnectAttempts > 0) {
            // Reconnected after a drop: notify all views to refetch
            window.dispatchEvent(new CustomEvent("campus-pulse-reconnected"));
          }
          reconnectAttempts = 0;
          authService
            .me()
            .then((res) => {
              if (!isCancelled && res?.data) {
                localStorage.setItem(USER_KEY, JSON.stringify(res.data));
                setUser((prev) =>
                  JSON.stringify(prev) === JSON.stringify(res.data)
                    ? prev
                    : res.data
                );
              }
            })
            .catch(() => {});
          try {
            ws.send("ping");
          } catch {}
        });

        ws.addEventListener("message", (evt) => {
          if (!evt.data) return;
          if (typeof evt.data === "string") {
            const trimmed = evt.data.trim().toLowerCase();
            if (trimmed === "pong" || trimmed === "ping") return;
          }
          try {
            const payload = JSON.parse(evt.data);
            if (payload?.type === "pong" || payload?.type === "ping" || payload?.event === "pong" || payload?.event === "ping") return;
            window.dispatchEvent(
              new CustomEvent("campus-pulse-notification", { detail: payload }),
            );
            window.dispatchEvent(
              new CustomEvent("campus-pulse-ws-event", { detail: payload }),
            );
          } catch {
            window.dispatchEvent(
              new CustomEvent("campus-pulse-notification", {
                detail: { event: "message", data: evt.data },
              }),
            );
          }
        });

        ws.addEventListener("close", (evt) => {
          // On non-normal close, reconnect with exponential backoff using a newly fetched single-use ticket
          if (!isCancelled && evt.code !== 1000) {
            reconnectAttempts++;
            const backoffDelay = Math.min(30000, 1000 * Math.pow(2, Math.min(reconnectAttempts, 5)));
            reconnectTimeout = setTimeout(connect, backoffDelay);
          }
        });
      } catch {
        if (!isCancelled) {
          reconnectAttempts++;
          const backoffDelay = Math.min(30000, 1000 * Math.pow(2, Math.min(reconnectAttempts, 5)));
          reconnectTimeout = setTimeout(connect, backoffDelay);
        }
      }
    }

    // Fallback polling interval every 30s if socket is down
    const fallbackPollTimer = setInterval(() => {
      if (!ws || ws.readyState !== WebSocket.OPEN) {
        window.dispatchEvent(new CustomEvent("campus-pulse-poll"));
      } else {
        try {
          ws.send("ping");
        } catch {}
      }
    }, 30000);

    connect();

    return () => {
      isCancelled = true;
      if (reconnectTimeout) clearTimeout(reconnectTimeout);
      clearInterval(fallbackPollTimer);
      try {
        if (ws && (ws.readyState === WebSocket.OPEN || ws.readyState === WebSocket.CONNECTING)) {
          ws.close(1000, "Component unmounted");
        }
      } catch {}
    };
  }, [token, user]);

  const login = async (credentials) => {
    const response = await authService.login(credentials);
    const { access_token: accessToken, user: currentUser } = response.data;
    localStorage.setItem(TOKEN_KEY, accessToken);
    localStorage.setItem(USER_KEY, JSON.stringify(currentUser));
    try {
      sessionStorage.removeItem(SESSION_MESSAGE_KEY);
      localStorage.removeItem(SESSION_MESSAGE_KEY);
    } catch {}
    setToken(accessToken);
    setUser(currentUser);
    setSessionMessage("");
    window.dispatchEvent(new CustomEvent("campus-pulse-user-loaded", { detail: currentUser }));

    // Trigger push notification subscription after login (not on first page load)
    try {
      pushService.subscribeUser().catch(() => {});
    } catch {}

    return currentUser;
  };

  const logout = async () => {
    const activeToken = token || localStorage.getItem(TOKEN_KEY);
    clearSession();
    try {
      try {
        await Promise.race([
          pushService.unsubscribeUser(),
          new Promise((resolve) => setTimeout(resolve, 500)),
        ]);
      } catch {}
      if (activeToken) {
        await authService.logout(activeToken);
      }
    } catch {
      // Ignore network errors on logout
    }
  };

  const refreshUser = async () => {
    const response = await authService.me();
    localStorage.setItem(USER_KEY, JSON.stringify(response.data));
    setUser(response.data);
    return response.data;
  };

  const clearSessionMessage = () => {
    try {
      sessionStorage.removeItem(SESSION_MESSAGE_KEY);
      localStorage.removeItem(SESSION_MESSAGE_KEY);
    } catch {}
    setSessionMessage("");
  };

  const value = useMemo(
    () => ({
      token,
      user,
      setUser,
      initializing,
      sessionMessage,
      isAuthenticated: Boolean(token && user),
      login,
      logout,
      refreshUser,
      clearSessionMessage,
    }),
    [token, user, initializing, sessionMessage],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) throw new Error("useAuth must be used inside AuthProvider.");
  return context;
}
