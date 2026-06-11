"use client";

import Link from "next/link";
import { AlertTriangle, FileQuestion, Lock, ServerCrash, ShieldX } from "lucide-react";
import { Button } from "@/components/ui/button";

const STATUS_CONTENT: Record<
  number,
  { title: string; description: string; icon: React.ComponentType<{ className?: string }> }
> = {
  400: {
    title: "Bad Request",
    description: "The request could not be understood by the server. Please check your input and try again.",
    icon: AlertTriangle,
  },
  401: {
    title: "Unauthorized",
    description: "You need to sign in to access this page. Your session may have expired.",
    icon: Lock,
  },
  403: {
    title: "Access Forbidden",
    description: "You do not have permission to access this resource.",
    icon: ShieldX,
  },
  404: {
    title: "Page Not Found",
    description: "The page you are looking for does not exist or may have been moved.",
    icon: FileQuestion,
  },
  500: {
    title: "Internal Server Error",
    description: "Something went wrong on our end. Please try again later.",
    icon: ServerCrash,
  },
  503: {
    title: "Service Unavailable",
    description: "The service is temporarily unavailable. Please try again in a few minutes.",
    icon: ServerCrash,
  },
};

const FALLBACK = {
  title: "Unexpected Error",
  description: "An unexpected error occurred. Please try again later.",
  icon: AlertTriangle,
};

export type ErrorPageProps = {
  /** HTTP status code to display (e.g. 404, 500). */
  statusCode: number;
  /** Override the default title for the status code. */
  title?: string;
  /** Override the default description for the status code. */
  description?: string;
  /** Optional request ID for support correlation. */
  requestId?: string;
  /** Optional retry handler (renders a "Try again" button). */
  onRetry?: () => void;
};

export function ErrorPage({
  statusCode,
  title,
  description,
  requestId,
  onRetry,
}: ErrorPageProps) {
  const content = STATUS_CONTENT[statusCode] ?? FALLBACK;
  const Icon = content.icon;
  const isServerError = statusCode >= 500;

  return (
    <div className="flex min-h-[80vh] items-center justify-center px-4">
      <div className="w-full max-w-md text-center">
        <div
          className={`mx-auto mb-6 flex h-20 w-20 items-center justify-center rounded-full ${
            isServerError ? "bg-destructive/10" : "bg-muted"
          }`}
          aria-hidden="true"
        >
          <Icon
            className={`h-10 w-10 ${
              isServerError ? "text-destructive" : "text-muted-foreground"
            }`}
          />
        </div>

        <p
          className="text-6xl font-bold tracking-tight text-primary"
          aria-label={`Error ${statusCode}`}
        >
          {statusCode}
        </p>
        <h1 className="mt-4 text-2xl font-semibold text-foreground">
          {title ?? content.title}
        </h1>
        <p className="mt-3 text-muted-foreground">
          {description ?? content.description}
        </p>

        {requestId ? (
          <p className="mt-4 text-xs text-muted-foreground">
            Reference ID: <code className="font-mono">{requestId}</code>
          </p>
        ) : null}

        <div className="mt-8 flex items-center justify-center gap-3">
          {onRetry ? (
            <Button onClick={onRetry}>Try again</Button>
          ) : null}
          <Button variant={onRetry ? "outline" : "default"} asChild>
            <Link href="/">Return to home</Link>
          </Button>
        </div>
      </div>
    </div>
  );
}
