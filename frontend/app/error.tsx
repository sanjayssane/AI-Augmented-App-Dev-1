"use client";

import { useEffect } from "react";
import { ApiError } from "@/lib/errors/problem";
import { ErrorPage } from "@/components/error-page";

export default function Error({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    console.error("Unhandled application error:", error);
  }, [error]);

  // Surface the real HTTP status when the failure came from the API.
  const statusCode = error instanceof ApiError ? error.status : 500;
  const requestId =
    error instanceof ApiError ? error.problem.request_id : error.digest;

  return (
    <ErrorPage statusCode={statusCode} requestId={requestId} onRetry={reset} />
  );
}
