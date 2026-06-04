import type { Metadata } from "next";
import { PlaceholderPage } from "@/components/placeholder-page";

export const metadata: Metadata = {
  title: "Examiner Dashboard — MCQ Test Platform",
};

export default function ExaminerDashboardPage() {
  return (
    <PlaceholderPage
      title="Examiner Dashboard"
      description="Question bank CRUD and results management (Phase 5). Future routes: /examiner/sessions/[id], /examiner/settings."
      backHref="/"
      backLabel="Home"
    />
  );
}
