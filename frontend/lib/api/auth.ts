import { apiFetch, apiFetchEnvelope } from "@/lib/api/client";
import type {
  CsrfTokenData,
  CurrentUserData,
  ExamineeSessionResource,
  ExaminerLoginData,
  SuccessEnvelope,
} from "@/lib/types";

export async function fetchCsrfToken(): Promise<string> {
  const res = await apiFetchEnvelope<CsrfTokenData>("/auth/csrf");
  return res.data.csrf_token;
}

export async function loginExaminer(
  username: string,
  password: string,
): Promise<ExaminerLoginData> {
  const res = await apiFetchEnvelope<ExaminerLoginData>("/auth/examiner/login", {
    method: "POST",
    body: JSON.stringify({ username, password }),
  });
  return res.data;
}

export async function enterExaminee(
  csrfToken: string,
  payload: { prn: string; name: string; privacy_acknowledged: boolean },
): Promise<SuccessEnvelope<ExamineeSessionResource>> {
  return apiFetchEnvelope<ExamineeSessionResource>("/auth/examinee/entry", {
    method: "POST",
    csrfToken,
    body: JSON.stringify(payload),
  });
}

export async function logout(csrfToken: string): Promise<void> {
  await apiFetch<void>("/auth/logout", {
    method: "POST",
    csrfToken,
  });
}

export async function fetchCurrentUser(): Promise<CurrentUserData | null> {
  try {
    const res = await apiFetchEnvelope<CurrentUserData>("/auth/me");
    return res.data;
  } catch {
    return null;
  }
}
