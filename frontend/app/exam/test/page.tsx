import type { Metadata } from "next";
import { PlaceholderPage } from "@/components/placeholder-page";

export const metadata: Metadata = {
  title: "Test Interface — MCQ Test Platform",
};

export default function ExamTestPage() {
  return (
    <PlaceholderPage
      title="Test Interface"
      description="50-question MCQ test with navigation and auto-save (Phase 5)."
      backHref="/"
      backLabel="Home"
    />
  );
}
