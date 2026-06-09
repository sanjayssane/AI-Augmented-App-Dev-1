/**
 * RFC 7807 application/problem+json handling.
 */

export type ProblemDetails = {
  type: string;
  title: string;
  status: number;
  detail?: string;
  instance?: string;
  request_id?: string;
  errors?: Array<{ field: string; message: string }>;
  locked_until?: string;
  active_count?: number;
};

export class ApiError extends Error {
  constructor(
    public readonly problem: ProblemDetails,
  ) {
    super(problem.detail ?? problem.title);
    this.name = "ApiError";
  }

  get status(): number {
    return this.problem.status;
  }

  get typeSuffix(): string {
    const parts = this.problem.type.split("/");
    return parts[parts.length - 1] ?? "";
  }
}

export function parseProblemDetails(body: unknown): ProblemDetails | null {
  if (typeof body !== "object" || body === null) return null;
  const p = body as Record<string, unknown>;
  if (typeof p.title !== "string" || typeof p.status !== "number") return null;
  return body as ProblemDetails;
}

const USER_MESSAGES: Record<string, string> = {
  "invalid-credentials": "Invalid username or password",
  "exam-already-completed": "This registration number has already completed the test.",
  "identity-mismatch": "The provided details do not match our records.",
  "rate-limit-exceeded": "Too many requests. Please try again later.",
  "service-unavailable": "The question bank is not ready. Please contact your examiner.",
  "session-not-found": "No active session found. Please register again.",
  conflict: "Your answer could not be saved because it was updated elsewhere. Retrying…",
  locked: "This account is temporarily locked due to too many failed login attempts.",
  forbidden: "You do not have permission to perform this action.",
  unauthenticated: "Your session has expired. Please sign in again.",
};

export function getUserFacingMessage(problem: ProblemDetails): string {
  const suffix = problem.type.split("/").pop() ?? "";
  if (USER_MESSAGES[suffix]) return USER_MESSAGES[suffix];
  if (problem.errors?.length) {
    return problem.errors.map((e) => e.message).join(" ");
  }
  return problem.detail ?? problem.title;
}
