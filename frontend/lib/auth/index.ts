/**
 * Auth context stub (Phase 5).
 * Session state from GET /auth/me; role-aware redirects.
 */

export type UserRole = "EXAMINEE" | "EXAMINER";

export type AuthUser = {
  user_id: string;
  role: UserRole;
  prn?: string;
  name?: string;
  username?: string;
};

export type AuthState = {
  user: AuthUser | null;
  isLoading: boolean;
};
