import { useCallback, useEffect, useState, useContext } from "react";
import { useAuthContext } from "../../context/AuthContext";
import { clearTokens } from "../../services/api";

const STORAGE_KEY = "medicare-demo-user";

function readDemoUser() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    return raw ? JSON.parse(raw) : null;
  } catch {
    return null;
  }
}

export function setDemoUser(user: any) {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(user));
  localStorage.setItem("manus-runtime-user-info", JSON.stringify(user));
  window.dispatchEvent(new Event("medicare-auth-change"));
}

export function clearDemoUser() {
  clearTokens();
  window.dispatchEvent(new Event("medicare-auth-change"));
}

/**
 * useAuth hook: bridges to live AuthContext when mounted inside AuthProvider,
 * or gracefully falls back to local storage sync if mounted standalone.
 */
export function useAuth(options: any = {}) {
  const { redirectOnUnauthenticated = false, redirectPath } = options;

  let authContext: any = null;
  try {
    authContext = useAuthContext();
  } catch {
    // Rendered outside AuthProvider
    authContext = null;
  }

  const [localUser, setLocalUser] = useState(() => readDemoUser());
  const [localLoading, setLocalLoading] = useState(false);

  useEffect(() => {
    if (authContext) return;

    const sync = () => setLocalUser(readDemoUser());
    window.addEventListener("medicare-auth-change", sync);
    window.addEventListener("storage", sync);

    return () => {
      window.removeEventListener("medicare-auth-change", sync);
      window.removeEventListener("storage", sync);
    };
  }, [authContext]);

  const user = authContext ? authContext.user : localUser;
  const loading = authContext ? authContext.loading : localLoading;
  const error = authContext ? authContext.error : null;
  const isAuthenticated = Boolean(user);

  useEffect(() => {
    if (!redirectOnUnauthenticated || loading || user) return;
    if (typeof window === "undefined") return;
    if (redirectPath && window.location.pathname === redirectPath) return;

    if (redirectPath) {
      window.location.href = redirectPath;
    }
  }, [redirectOnUnauthenticated, redirectPath, loading, user]);

  const logout = useCallback(async () => {
    if (authContext) {
      await authContext.logout();
    } else {
      setLocalLoading(true);
      try {
        clearDemoUser();
        setLocalUser(null);
      } finally {
        setLocalLoading(false);
      }
    }
  }, [authContext]);

  const refresh = useCallback(async () => {
    if (authContext) {
      const refreshed = await authContext.refreshUser();
      return { data: refreshed };
    }
    const next = readDemoUser();
    setLocalUser(next);
    return { data: next };
  }, [authContext]);

  return {
    user,
    role: user?.role || null,
    loading,
    error,
    isAuthenticated,
    refresh,
    logout,
    login: authContext?.login,
    register: authContext?.register,
  };
}
