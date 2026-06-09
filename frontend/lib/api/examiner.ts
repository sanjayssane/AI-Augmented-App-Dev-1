import { apiFetch, apiFetchBlob, apiFetchEnvelope } from "@/lib/api/client";
import type {
  CorrectOption,
  EraseExamineeData,
  ExaminerUserOut,
  PlatformSettingsOut,
  QuestionListData,
  QuestionOut,
  SessionDetailOut,
  SessionListData,
  SelectionMode,
} from "@/lib/types";

export async function listQuestions(params?: {
  cursor?: string;
  limit?: number;
  include_deleted?: boolean;
}): Promise<QuestionListData> {
  const search = new URLSearchParams();
  if (params?.cursor) search.set("cursor", params.cursor);
  if (params?.limit) search.set("limit", String(params.limit));
  if (params?.include_deleted) search.set("include_deleted", "true");
  const qs = search.toString();
  const res = await apiFetchEnvelope<QuestionListData>(
    `/examiner/questions${qs ? `?${qs}` : ""}`,
  );
  return res.data;
}

export async function createQuestion(
  csrfToken: string,
  body: {
    question_text: string;
    option_a: string;
    option_b: string;
    option_c: string;
    option_d: string;
    correct_option: CorrectOption;
  },
): Promise<QuestionOut> {
  const res = await apiFetchEnvelope<QuestionOut>("/examiner/questions", {
    method: "POST",
    csrfToken,
    body: JSON.stringify(body),
  });
  return res.data;
}

export async function patchQuestion(
  questionId: string,
  csrfToken: string,
  body: Partial<{
    question_text: string;
    option_a: string;
    option_b: string;
    option_c: string;
    option_d: string;
    correct_option: CorrectOption;
  }>,
): Promise<QuestionOut> {
  const res = await apiFetchEnvelope<QuestionOut>(
    `/examiner/questions/${questionId}`,
    {
      method: "PATCH",
      csrfToken,
      body: JSON.stringify(body),
    },
  );
  return res.data;
}

export async function deleteQuestion(
  questionId: string,
  csrfToken: string,
): Promise<void> {
  await apiFetch<void>(`/examiner/questions/${questionId}`, {
    method: "DELETE",
    csrfToken,
  });
}

export async function listSessions(params?: {
  cursor?: string;
  limit?: number;
}): Promise<SessionListData> {
  const search = new URLSearchParams();
  if (params?.cursor) search.set("cursor", params.cursor);
  if (params?.limit) search.set("limit", String(params.limit));
  const qs = search.toString();
  const res = await apiFetchEnvelope<SessionListData>(
    `/examiner/sessions${qs ? `?${qs}` : ""}`,
  );
  return res.data;
}

export async function getSessionDetail(
  sessionId: string,
): Promise<SessionDetailOut> {
  const res = await apiFetchEnvelope<SessionDetailOut>(
    `/examiner/sessions/${sessionId}`,
  );
  return res.data;
}

export async function exportSessionsCsv(
  anonymised = false,
): Promise<Blob> {
  return apiFetchBlob(
    `/examiner/sessions/export?format=csv&anonymised=${anonymised}`,
  );
}

export async function getSettings(): Promise<PlatformSettingsOut> {
  const res = await apiFetchEnvelope<PlatformSettingsOut>("/examiner/settings");
  return res.data;
}

export async function patchSettings(
  csrfToken: string,
  body: Partial<{
    retention_days_completed: number;
    allow_examinee_retake: boolean;
    question_selection_mode: SelectionMode;
  }>,
): Promise<PlatformSettingsOut> {
  const res = await apiFetchEnvelope<PlatformSettingsOut>("/examiner/settings", {
    method: "PATCH",
    csrfToken,
    body: JSON.stringify(body),
  });
  return res.data;
}

export async function createExaminer(
  csrfToken: string,
  body: {
    username: string;
    password: string;
    force_password_change: boolean;
  },
): Promise<ExaminerUserOut> {
  const res = await apiFetchEnvelope<ExaminerUserOut>(
    "/examiner/users/examiners",
    {
      method: "POST",
      csrfToken,
      body: JSON.stringify(body),
    },
  );
  return res.data;
}

export async function eraseExaminee(
  userId: string,
  csrfToken: string,
): Promise<EraseExamineeData> {
  const res = await apiFetchEnvelope<EraseExamineeData>(
    `/examiner/users/examinees/${userId}/erase`,
    {
      method: "POST",
      csrfToken,
    },
  );
  return res.data;
}
