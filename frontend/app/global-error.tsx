"use client";

import { useEffect } from "react";

// Root-level boundary: catches errors in the root layout itself, so it must
// render its own <html>/<body> and cannot rely on app styles or components.
export default function GlobalError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    console.error("Fatal application error:", error);
  }, [error]);

  return (
    <html lang="en">
      <body
        style={{
          margin: 0,
          minHeight: "100vh",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          fontFamily: "system-ui, -apple-system, sans-serif",
          backgroundColor: "#f8f9fc",
          color: "#1a1d29",
        }}
      >
        <div style={{ textAlign: "center", padding: "1rem", maxWidth: "28rem" }}>
          <p
            style={{
              fontSize: "4rem",
              fontWeight: 700,
              margin: 0,
              color: "#2d3a8c",
            }}
            aria-label="Error 500"
          >
            500
          </p>
          <h1 style={{ fontSize: "1.5rem", margin: "1rem 0 0.75rem" }}>
            Internal Server Error
          </h1>
          <p style={{ color: "#5a6072", margin: 0 }}>
            Something went wrong on our end. Please try again later.
          </p>
          {error.digest ? (
            <p style={{ fontSize: "0.75rem", color: "#5a6072", marginTop: "1rem" }}>
              Reference ID: <code>{error.digest}</code>
            </p>
          ) : null}
          <button
            onClick={reset}
            style={{
              marginTop: "2rem",
              padding: "0.625rem 1.25rem",
              borderRadius: "0.375rem",
              border: "none",
              backgroundColor: "#2d3a8c",
              color: "#ffffff",
              fontSize: "0.875rem",
              fontWeight: 500,
              cursor: "pointer",
            }}
          >
            Try again
          </button>
        </div>
      </body>
    </html>
  );
}
