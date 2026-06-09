"use client";

import { useEffect, type ReactNode } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth";
import type { SessionStatus, UserRole } from "@/lib/types";

type RouteGuardProps = {
  children: ReactNode;
  role?: UserRole;
  sessionStatus?: SessionStatus | SessionStatus[];
  redirectTo?: string;
};

export function RouteGuard({
  children,
  role,
  sessionStatus,
  redirectTo = "/",
}: RouteGuardProps) {
  const router = useRouter();
  const { user, isLoading, examineeSession } = useAuth();

  useEffect(() => {
    if (isLoading) return;

    if (role && (!user || user.role !== role)) {
      router.replace(redirectTo);
      return;
    }

    if (sessionStatus && role === "EXAMINEE") {
      const allowed = Array.isArray(sessionStatus)
        ? sessionStatus
        : [sessionStatus];
      if (!examineeSession || !allowed.includes(examineeSession.status)) {
        router.replace(redirectTo);
      }
    }
  }, [
    isLoading,
    user,
    role,
    sessionStatus,
    examineeSession,
    router,
    redirectTo,
  ]);

  if (isLoading) {
    return (
      <div className="flex min-h-[50vh] items-center justify-center">
        <p className="text-muted-foreground">Loading…</p>
      </div>
    );
  }

  if (role && (!user || user.role !== role)) return null;

  if (sessionStatus && role === "EXAMINEE") {
    const allowed = Array.isArray(sessionStatus)
      ? sessionStatus
      : [sessionStatus];
    if (!examineeSession || !allowed.includes(examineeSession.status)) {
      return null;
    }
  }

  return <>{children}</>;
}
