import { useCallback, useEffect } from "react";
import { useAuthContext } from "../../context/AuthContext";

/**
 * useAuth hook: provides access to the canonical backend-authenticated user session
 * from AuthContext.
 */
export function useAuth(options: any = {}) {
  const { redirectOnUnauthenticated = false, redirectPath } = options;

  const authContext = useAuthContext();
  const { user, loading, error, isAuthenticated, role, login, register, logout, refreshUser } = authContext;

  const refresh = useCallback(async () => {
    const refreshed = await refreshUser();
    return { data: refreshed };
  }, [refreshUser]);

  return {
    user,
    role: user?.role || role || null,
    loading,
    error,
    isAuthenticated: Boolean(user),
    refresh,
    logout,
    login,
    register,
  };
}

