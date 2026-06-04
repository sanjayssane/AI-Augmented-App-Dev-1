/**
 * API client stub — wire to FastAPI in Phase 5.
 * All requests use credentials: 'include' for HttpOnly session cookies.
 */

const getBaseUrl = (): string => {
  return process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000/api/v1";
};

export type ApiRequestOptions = RequestInit & {
  csrfToken?: string;
};

export async function apiFetch<T>(
  path: string,
  options: ApiRequestOptions = {},
): Promise<T> {
  const { csrfToken, headers, ...rest } = options;
  const url = `${getBaseUrl()}${path.startsWith("/") ? path : `/${path}`}`;

  const response = await fetch(url, {
    ...rest,
    credentials: "include",
    headers: {
      "Content-Type": "application/json",
      ...(csrfToken ? { "X-CSRF-Token": csrfToken } : {}),
      ...headers,
    },
  });

  if (!response.ok) {
    throw new Error(`API error: ${response.status} ${response.statusText}`);
  }

  return response.json() as Promise<T>;
}
