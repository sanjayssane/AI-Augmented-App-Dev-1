import type { Metadata } from "next";
import { ErrorPage } from "@/components/error-page";

export const metadata: Metadata = {
  title: "404 - Page Not Found | MCQ Test Platform",
};

export default function NotFound() {
  return <ErrorPage statusCode={404} />;
}
