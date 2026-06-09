"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import {
  fetchQuestionAtPosition,
  saveResponse,
  submitSession,
} from "@/lib/api/examinee";
import { useAuth } from "@/lib/auth";
import { ApiError } from "@/lib/errors/problem";
import { useStatusAnnouncer } from "@/components/status-announcer";
import type {
  ExamineeQuestionAtPosition,
  ExamineeSessionResource,
  SelectedOption,
} from "@/lib/types";

type SaveState = "idle" | "saving" | "saved" | "error";

export function useTestSession() {
  const {
    examineeSession,
    csrfToken,
    refreshCsrf,
    refreshExamineeSession,
    setLastSubmitResult,
  } = useAuth();
  const { announcePolite } = useStatusAnnouncer();

  const [session, setSession] = useState<ExamineeSessionResource | null>(
    examineeSession,
  );
  const [position, setPosition] = useState(1);
  const [questionData, setQuestionData] =
    useState<ExamineeQuestionAtPosition | null>(null);
  const [loading, setLoading] = useState(true);
  const [saveState, setSaveState] = useState<SaveState>("idle");
  const [saveError, setSaveError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const updatedAtRef = useRef<Record<string, string>>({});
  const idempotencyKeyRef = useRef<string | null>(null);

  useEffect(() => {
    if (examineeSession) {
      setSession(examineeSession);
      setPosition(examineeSession.current_position || 1);
    }
  }, [examineeSession]);

  const loadQuestion = useCallback(
    async (pos: number) => {
      if (!session) return;
      setLoading(true);
      try {
        const data = await fetchQuestionAtPosition(session.session_id, pos);
        setQuestionData(data);
        setSession((prev) =>
          prev
            ? { ...prev, answered_count: data.answered_count }
            : prev,
        );
      } finally {
        setLoading(false);
      }
    },
    [session],
  );

  useEffect(() => {
    if (session) void loadQuestion(position);
  }, [session, position, loadQuestion]);

  const saveAnswer = useCallback(
    async (option: SelectedOption) => {
      if (!session || !questionData || !csrfToken) return;

      setSaveState("saving");
      setSaveError(null);

      const questionId = questionData.question.question_id;
      const ifUnmodifiedSince = updatedAtRef.current[questionId];

      const attemptSave = async (token: string) => {
        return saveResponse(
          session.session_id,
          questionId,
          token,
          option,
          ifUnmodifiedSince,
        );
      };

      try {
        let token = csrfToken;
        let result;
        try {
          result = await attemptSave(token);
        } catch (err) {
          if (err instanceof ApiError && err.status === 409) {
            const refreshed = await fetchQuestionAtPosition(
              session.session_id,
              position,
            );
            setQuestionData(refreshed);
            updatedAtRef.current[questionId] = refreshed.selected_option
              ? new Date().toISOString()
              : "";
            result = await attemptSave(token);
          } else {
            throw err;
          }
        }

        updatedAtRef.current[questionId] = result.updated_at;
        setQuestionData((prev) =>
          prev
            ? {
                ...prev,
                selected_option: result.selected_option,
                answered_count: result.answered_count,
              }
            : prev,
        );
        setSession((prev) =>
          prev ? { ...prev, answered_count: result.answered_count } : prev,
        );
        setSaveState("saved");
        announcePolite("Answer saved");
      } catch (err) {
        setSaveState("error");
        const message =
          err instanceof ApiError
            ? err.problem.detail ?? "Failed to save answer"
            : "Failed to save answer";
        setSaveError(message);
        announcePolite("Save failed. Please retry.");
      }
    },
    [session, questionData, csrfToken, position, announcePolite],
  );

  const retrySave = useCallback(async () => {
    if (!questionData?.selected_option) {
      setSaveError(null);
      setSaveState("idle");
      return;
    }
    await saveAnswer(questionData.selected_option);
  }, [questionData, saveAnswer]);

  const goToPosition = useCallback(
    (pos: number) => {
      if (saveState === "error") return;
      if (pos >= 1 && pos <= 50) setPosition(pos);
    },
    [saveState],
  );

  const submitTest = useCallback(async () => {
    if (!session || !csrfToken) return null;

    setIsSubmitting(true);
    try {
      let token = csrfToken;
      if (!idempotencyKeyRef.current) {
        idempotencyKeyRef.current = crypto.randomUUID();
      }
      const result = await submitSession(
        session.session_id,
        token,
        idempotencyKeyRef.current,
      );
      setLastSubmitResult(result);
      const updated = await refreshExamineeSession();
      if (!updated) {
        setSession((prev) =>
          prev ? { ...prev, status: "COMPLETED" as const } : prev,
        );
      }
      return result;
    } finally {
      setIsSubmitting(false);
    }
  }, [session, csrfToken, setLastSubmitResult, refreshExamineeSession]);

  return {
    session,
    position,
    questionData,
    loading,
    saveState,
    saveError,
    isSubmitting,
    setPosition: goToPosition,
    saveAnswer,
    retrySave,
    submitTest,
    refreshCsrf,
  };
}
