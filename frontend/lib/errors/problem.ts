/**
 * RFC 7807 application/problem+json stub (Phase 5).
 */

export type ProblemDetails = {
  type: string;
  title: string;
  status: number;
  detail?: string;
  instance?: string;
  request_id?: string;
  errors?: Array<{ field: string; message: string }>;
};

export function parseProblemDetails(body: unknown): ProblemDetails | null {
  if (typeof body !== "object" || body === null) return null;
  const p = body as Record<string, unknown>;
  if (typeof p.title !== "string" || typeof p.status !== "number") return null;
  return body as ProblemDetails;
}
