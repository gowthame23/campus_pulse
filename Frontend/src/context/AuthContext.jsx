import { createContext, useContext, useEffect, useMemo, useState } from "react";
import { authService } from "../services/authService";

const AuthContext = createContext(null);
const TOKEN_KEY = "campusPulseToken";
const USER_KEY = "campusPulseUser";
const SESSION_MESSAGE_KEY = "campusPulseSessionMessage";

function readStoredUser() {
  const value = localStorage.getItem(USER_KEY);
  if (!value) return null;
  try {
    return JSON.parse(value);
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

  // WebSocket for real-time notifications (connect when authenticated)
  useEffect(() => {
    if (!token || !user) return; // only when authenticated
    let ws;
    try {
      const apiBase =
        import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000";
      const wsBase = apiBase.replace(/^http/, "ws");
      const wsUrl = `${wsBase.replace(/\/$/, "")}/notifications/ws/${user.user_id}`;
      // append token for websocket authentication
      const token = localStorage.getItem(TOKEN_KEY);
      const sep = wsUrl.includes("?") ? "&" : "?";
      const wsUrlWithToken = token
        ? `${wsUrl}${sep}token=${encodeURIComponent(token)}`
        : wsUrl;
      ws = new WebSocket(wsUrlWithToken);

      ws.addEventListener("open", () => {
        // optional: send a ping or initial message
        try {
          ws.send("ping");
        } catch (e) {
          /* ignore */
        }
      });

      ws.addEventListener("message", (evt) => {
        try {
          const payload = JSON.parse(evt.data);
          // Dispatch a custom event so UI components can react
          window.dispatchEvent(
            new CustomEvent("campus-pulse-notification", { detail: payload }),
          );
        } catch (err) {
          // If message is plain text, forward as-is
          window.dispatchEvent(
            new CustomEvent("campus-pulse-notification", {
              detail: { event: "message", data: evt.data },
            }),
          );
        }
      });

      ws.addEventListener("close", () => {
        // no-op; will reconnect on next login or refresh
      });
    } catch (err) {
      // ignore websocket setup errors in UI
    }

    return () => {
      try {
        if (ws && ws.readyState === WebSocket.OPEN) ws.close();
      } catch (e) {}
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
    return currentUser;
  };

  const logout = async () => {
    try {
      if (token) await authService.logout();
    } finally {
      clearSession();
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
