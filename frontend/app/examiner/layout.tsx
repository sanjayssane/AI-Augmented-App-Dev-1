"use client";

import type { ReactNode } from "react";
import { RouteGuard } from "@/components/route-guard";

export default function ExaminerLayout({ children }: { children: ReactNode }) {
  return <RouteGuard role="EXAMINER">{children}</RouteGuard>;
}
