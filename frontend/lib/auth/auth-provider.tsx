"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";
import {
  enterExaminee as apiEnterExaminee,
  fetchCsrfToken,
  fetchCurrentUser,
  loginExaminer as apiLoginExaminer,
  logout as apiLogout,
} from "@/lib/api/auth";
import { fetchCurrentSession } from "@/lib/api/examinee";
import { ApiError } from "@/lib/errors/problem";
import type {
  CurrentUserData,
  ExamineeSessionResource,
  SubmitSessionResult,
  UserRole,
} from "@/lib/types";

export type AuthUser = CurrentUserData;

type AuthContextValue = {
  user: AuthUser | null;
  csrfToken: string | null;
  isLoading: boolean;
  examineeSession: ExamineeSessionResource | null;
  lastSubmitResult: SubmitSessionResult | null;
  setLastSubmitResult: (result: SubmitSessionResult | null) => void;
  refreshCsrf: () => Promise<string>;
  refreshMe: () => Promise<AuthUser | null>;
  refreshExamineeSession: () => Promise<ExamineeSessionResource | null>;
  loginExaminer: (username: string, password: string) => Promise<void>;
  enterExaminee: (payload: {
    prn: string;
    name: string;
    privacy_acknowledged: boolean;
  }) => Promise<ExamineeSessionResource>;
  logout: () => Promise<void>;
};

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<AuthUser | null>(null);
  const [csrfToken, setCsrfToken] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [examineeSession, setExamineeSession] =
    useState<ExamineeSessionResource | null>(null);
  const [lastSubmitResult, setLastSubmitResult] =
    useState<SubmitSessionResult | null>(null);

  const refreshCsrf = useCallback(async () => {
    const token = await fetchCsrfToken();
    setCsrfToken(token);
    return token;
  }, []);

  const refreshMe = useCallback(async () => {
    const profile = await fetchCurrentUser();
    setUser(profile);
    if (profile?.csrf_token) {
      setCsrfToken(profile.csrf_token);
    }
    return profile;
  }, []);

  const refreshExamineeSession = useCallback(async () => {
    try {
      const session = await fetchCurrentSession();
      setExamineeSession(session);
      return session;
    } catch {
      setExamineeSession(null);
      return null;
    }
  }, []);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const bootstrapCsrf = await fetchCsrfToken();
        if (cancelled) return;
        setCsrfToken(bootstrapCsrf);
        const profile = await fetchCurrentUser();
        if (cancelled) return;
        setUser(profile);
        if (profile?.csrf_token) {
          setCsrfToken(profile.csrf_token);
        }
        if (profile?.role === "EXAMINEE") {
          try {
            const session = await fetchCurrentSession();
            if (!cancelled) setExamineeSession(session);
          } catch {
            if (!cancelled) setExamineeSession(null);
          }
        }
      } finally {
        if (!cancelled) setIsLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  const loginExaminer = useCallback(
    async (username: string, password: string) => {
      await apiLoginExaminer(username, password);
      const profile = await refreshMe();
      if (!profile) throw new ApiError({ type: "", title: "Error", status: 500 });
      setExamineeSession(null);
    },
    [refreshMe],
  );

  const enterExaminee = useCallback(
    async (payload: {
      prn: string;
      name: string;
      privacy_acknowledged: boolean;
    }) => {
      let token = csrfToken;
      if (!token) token = await refreshCsrf();
      const res = await apiEnterExaminee(token, payload);
      const profile = await refreshMe();
      setUser(profile);
      setExamineeSession(res.data);
      return res.data;
    },
    [csrfToken, refreshCsrf, refreshMe],
  );

  const logout = useCallback(async () => {
    let token = csrfToken;
    if (!token) token = await refreshCsrf();
    try {
      await apiLogout(token);
    } finally {
      setUser(null);
      setExamineeSession(null);
      setLastSubmitResult(null);
      await refreshCsrf();
    }
  }, [csrfToken, refreshCsrf]);

  const value = useMemo(
    () => ({
      user,
      csrfToken,
      isLoading,
      examineeSession,
      lastSubmitResult,
      setLastSubmitResult,
      refreshCsrf,
      refreshMe,
      refreshExamineeSession,
      loginExaminer,
      enterExaminee,
      logout,
    }),
    [
      user,
      csrfToken,
      isLoading,
      examineeSession,
      lastSubmitResult,
      refreshCsrf,
      refreshMe,
      refreshExamineeSession,
      loginExaminer,
      enterExaminee,
      logout,
    ],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}

export function useRequiredRole(role: UserRole): AuthUser {
  const { user, isLoading } = useAuth();
  if (isLoading) return { user_id: "", role } as AuthUser;
  if (!user || user.role !== role) {
    throw new Error(`Required role: ${role}`);
  }
  return user;
}
