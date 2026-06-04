import type { Metadata } from "next";
import { PlaceholderPage } from "@/components/placeholder-page";

export const metadata: Metadata = {
  title: "Results & Review — MCQ Test Platform",
};

export default function ExamResultsPage() {
  return (
    <PlaceholderPage
      title="Results & Review"
      description="Score summary and answer review after submit (Phase 5)."
      backHref="/exam/test"
      backLabel="Test"
    />
  );
}
