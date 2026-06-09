import { apiFetchBlob, apiFetchEnvelope } from "@/lib/api/client";
import type {
  ExamineeQuestionAtPosition,
  ExamineeSessionResource,
  ReviewResult,
  SaveResponseResult,
  SubmitSessionResult,
} from "@/lib/types";

export async function fetchCurrentSession(): Promise<ExamineeSessionResource> {
  const res = await apiFetchEnvelope<ExamineeSessionResource>(
    "/examinee/sessions/current",
  );
  return res.data;
}

export async function fetchQuestionAtPosition(
  sessionId: string,
  position: number,
): Promise<ExamineeQuestionAtPosition> {
  const res = await apiFetchEnvelope<ExamineeQuestionAtPosition>(
    `/examinee/sessions/${sessionId}/questions/${position}`,
  );
  return res.data;
}

export async function saveResponse(
  sessionId: string,
  questionId: string,
  csrfToken: string,
  selectedOption: string | null,
  ifUnmodifiedSince?: string,
): Promise<SaveResponseResult> {
  const res = await apiFetchEnvelope<SaveResponseResult>(
    `/examinee/sessions/${sessionId}/responses/${questionId}`,
    {
      method: "PUT",
      csrfToken,
      ifUnmodifiedSince,
      body: JSON.stringify({ selected_option: selectedOption }),
    },
  );
  return res.data;
}

export async function submitSession(
  sessionId: string,
  csrfToken: string,
  idempotencyKey: string,
): Promise<SubmitSessionResult> {
  const res = await apiFetchEnvelope<SubmitSessionResult>(
    `/examinee/sessions/${sessionId}/submit`,
    {
      method: "POST",
      csrfToken,
      idempotencyKey,
      body: JSON.stringify({ confirm: true }),
    },
  );
  return res.data;
}

export async function fetchReview(sessionId: string): Promise<ReviewResult> {
  const res = await apiFetchEnvelope<ReviewResult>(
    `/examinee/sessions/${sessionId}/review`,
  );
  return res.data;
}

export async function exportMyData(): Promise<Blob> {
  return apiFetchBlob("/examinee/me/data-export");
}
