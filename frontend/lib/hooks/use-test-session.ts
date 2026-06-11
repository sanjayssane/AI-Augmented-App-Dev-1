"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import {
  fetchQuestionAtPosition,
  saveResponse,
  submitSession,
} from "@/lib/api/examinee";
import { useAuth } from "@/lib/auth";
import { ApiError, formatErrorMessage } from "@/lib/errors/problem";
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
    refreshMe,
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
  const [loadError, setLoadError] = useState<string | null>(null);
  const [saveState, setSaveState] = useState<SaveState>("idle");
  const [saveError, setSaveError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);

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
      setLoadError(null);
      try {
        const data = await fetchQuestionAtPosition(session.session_id, pos);
        setQuestionData(data);
        setSession((prev) =>
          prev
            ? { ...prev, answered_count: data.answered_count }
            : prev,
        );
      } catch (err) {
        setLoadError(formatErrorMessage(err, "Failed to load the question."));
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
          if (err instanceof ApiError && err.status === 403) {
            const profile = await refreshMe();
            if (!profile?.csrf_token) throw err;
            token = profile.csrf_token;
            result = await attemptSave(token);
          } else if (err instanceof ApiError && err.status === 409) {
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
        setSaveError(formatErrorMessage(err, "Failed to save your answer."));
        announcePolite("Save failed. Please retry.");
      }
    },
    [session, questionData, csrfToken, position, announcePolite, refreshMe],
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
    setSubmitError(null);
    try {
      let token = csrfToken;
      if (!idempotencyKeyRef.current) {
        idempotencyKeyRef.current = crypto.randomUUID();
      }

      const attemptSubmit = async (csrf: string) =>
        submitSession(session.session_id, csrf, idempotencyKeyRef.current!);

      let result;
      try {
        result = await attemptSubmit(token);
      } catch (err) {
        if (err instanceof ApiError && err.status === 403) {
          const profile = await refreshMe();
          if (!profile?.csrf_token) throw err;
          token = profile.csrf_token;
          result = await attemptSubmit(token);
        } else {
          throw err;
        }
      }

      setLastSubmitResult(result);
      const updated = await refreshExamineeSession();
      if (!updated) {
        setSession((prev) =>
          prev ? { ...prev, status: "COMPLETED" as const } : prev,
        );
      }
      return result;
    } catch (err) {
      setSubmitError(formatErrorMessage(err, "Failed to submit the test."));
      return null;
    } finally {
      setIsSubmitting(false);
    }
  }, [session, csrfToken, setLastSubmitResult, refreshExamineeSession, refreshMe]);

  return {
    session,
    position,
    questionData,
    loading,
    loadError,
    saveState,
    saveError,
    isSubmitting,
    submitError,
    setPosition: goToPosition,
    saveAnswer,
    retrySave,
    retryLoad: loadQuestion,
    submitTest,
  };
}
