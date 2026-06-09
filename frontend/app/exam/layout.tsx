"use client";

import type { ReactNode } from "react";
import { RouteGuard } from "@/components/route-guard";

export default function ExamLayout({ children }: { children: ReactNode }) {
  return (
    <RouteGuard role="EXAMINEE">
      {children}
    </RouteGuard>
  );
}
