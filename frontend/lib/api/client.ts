/**
 * Typed API client — cookie sessions + CSRF (PRD §9.6).
 */

import { ApiError, parseProblemDetails } from "@/lib/errors/problem";
import type { SuccessEnvelope } from "@/lib/types";

const getBaseUrl = (): string =>
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000/api/v1";

export type ApiRequestOptions = Omit<RequestInit, "headers"> & {
  csrfToken?: string;
  headers?: Record<string, string>;
  ifUnmodifiedSince?: string;
  idempotencyKey?: string;
};

async function parseErrorResponse(response: Response): Promise<ApiError> {
  const contentType = response.headers.get("content-type") ?? "";
  if (contentType.includes("application/problem+json")) {
    const body = await response.json();
    const problem = parseProblemDetails(body);
    if (problem) return new ApiError(problem);
  }
  return new ApiError({
    type: "about:blank",
    title: response.statusText,
    status: response.status,
    detail: `Request failed with status ${response.status}`,
  });
}

function buildHeaders(options: ApiRequestOptions): Record<string, string> {
  const headers: Record<string, string> = {
    ...(options.headers ?? {}),
  };

  const hasBody = options.body !== undefined && options.body !== null;
  if (hasBody && !headers["Content-Type"]) {
    headers["Content-Type"] = "application/json";
  }

  if (options.csrfToken) {
    headers["X-CSRF-Token"] = options.csrfToken;
  }
  if (options.ifUnmodifiedSince) {
    headers["If-Unmodified-Since"] = options.ifUnmodifiedSince;
  }
  if (options.idempotencyKey) {
    headers["Idempotency-Key"] = options.idempotencyKey;
  }

  return headers;
}

export async function apiFetch<T>(
  path: string,
  options: ApiRequestOptions = {},
): Promise<T> {
  const { csrfToken, ifUnmodifiedSince, idempotencyKey, headers, ...rest } =
    options;
  const url = `${getBaseUrl()}${path.startsWith("/") ? path : `/${path}`}`;

  const response = await fetch(url, {
    ...rest,
    credentials: "include",
    headers: buildHeaders({
      csrfToken,
      ifUnmodifiedSince,
      idempotencyKey,
      headers,
      body: rest.body,
    }),
  });

  if (!response.ok) {
    throw await parseErrorResponse(response);
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return response.json() as Promise<T>;
}

export async function apiFetchEnvelope<T>(
  path: string,
  options: ApiRequestOptions = {},
): Promise<SuccessEnvelope<T>> {
  return apiFetch<SuccessEnvelope<T>>(path, options);
}

export async function apiFetchBlob(
  path: string,
  options: ApiRequestOptions = {},
): Promise<Blob> {
  const { csrfToken, ifUnmodifiedSince, idempotencyKey, headers, ...rest } =
    options;
  const url = `${getBaseUrl()}${path.startsWith("/") ? path : `/${path}`}`;

  const response = await fetch(url, {
    ...rest,
    credentials: "include",
    headers: buildHeaders({
      csrfToken,
      ifUnmodifiedSince,
      idempotencyKey,
      headers,
      body: rest.body,
    }),
  });

  if (!response.ok) {
    throw await parseErrorResponse(response);
  }

  return response.blob();
}

export function downloadBlob(blob: Blob, filename: string): void {
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = filename;
  anchor.click();
  URL.revokeObjectURL(url);
}
