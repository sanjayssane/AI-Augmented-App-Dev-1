"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import {
  GraduationCap,
  ChevronLeft,
  ChevronRight,
  Flag,
  LogOut,
  CheckCircle2,
  Circle,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { Label } from "@/components/ui/label";
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from "@/components/ui/alert-dialog";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { RouteGuard } from "@/components/route-guard";
import { useAuth } from "@/lib/auth";
import { usePageTitle } from "@/lib/hooks/use-page-title";
import { useTestSession } from "@/lib/hooks/use-test-session";
import type { SelectedOption } from "@/lib/types";

function TestPageContent() {
  const router = useRouter();
  const { logout } = useAuth();
  const questionHeadingRef = useRef<HTMLHeadingElement>(null);
  const [showNavigator, setShowNavigator] = useState(true);
  const [answeredMap, setAnsweredMap] = useState<Set<number>>(new Set());
  const [isLoggingOut, setIsLoggingOut] = useState(false);

  const {
    session,
    position,
    questionData,
    loading,
    loadError,
    saveState,
    saveError,
    isSubmitting,
    submitError,
    setPosition,
    saveAnswer,
    retrySave,
    retryLoad,
    submitTest,
  } = useTestSession();

  usePageTitle(`Question ${position} of 50`);

  useEffect(() => {
    questionHeadingRef.current?.focus();
  }, [position, questionData?.question.question_id]);

  useEffect(() => {
    if (questionData?.selected_option) {
      setAnsweredMap((prev) => new Set(prev).add(position));
    }
  }, [questionData?.selected_option, position]);

  const answeredCount = session?.answered_count ?? 0;
  const totalQuestions = session?.total_questions ?? 50;

  const handleNavigation = useCallback(
    (direction: "prev" | "next") => {
      if (saveState === "error") return;
      if (direction === "prev" && position > 1) setPosition(position - 1);
      if (direction === "next" && position < totalQuestions)
        setPosition(position + 1);
    },
    [position, totalQuestions, setPosition, saveState],
  );

  const handleSubmit = async () => {
    const result = await submitTest();
    if (result) router.push("/exam/results");
  };

  const handleLogout = async () => {
    setIsLoggingOut(true);
    try {
      await logout();
      router.push("/");
    } finally {
      setIsLoggingOut(false);
    }
  };

  const formatExpires = (iso: string | undefined) => {
    if (!iso) return null;
    return new Date(iso).toLocaleString();
  };

  if (!session) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <p className="text-muted-foreground">Loading session…</p>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background">
      {saveState === "error" && saveError && (
        <Alert variant="destructive" className="rounded-none border-x-0 border-t-0">
          <AlertDescription className="flex flex-wrap items-center justify-between gap-2">
            <span>{saveError}</span>
            <Button size="sm" variant="outline" onClick={() => void retrySave()}>
              Retry save
            </Button>
          </AlertDescription>
        </Alert>
      )}

      {submitError && (
        <Alert variant="destructive" className="rounded-none border-x-0 border-t-0">
          <AlertDescription>{submitError}</AlertDescription>
        </Alert>
      )}

      <header className="sticky top-0 z-10 border-b border-border bg-card shadow-sm">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-4 py-3 sm:px-6 lg:px-8">
          <div className="flex items-center gap-3">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary">
              <GraduationCap className="h-5 w-5 text-primary-foreground" />
            </div>
            <span className="font-semibold text-foreground">MCQ Test</span>
          </div>

          <div className="flex items-center gap-4">
            {session.expires_at && (
              <span className="hidden text-sm text-muted-foreground sm:inline">
                Session expires: {formatExpires(session.expires_at)}
              </span>
            )}
            <div
              className="flex items-center gap-2 rounded-full bg-secondary px-3 py-1"
              role="progressbar"
              aria-valuenow={answeredCount}
              aria-valuemin={0}
              aria-valuemax={totalQuestions}
              aria-label={`${answeredCount} of ${totalQuestions} questions answered`}
            >
              <CheckCircle2 className="h-4 w-4 text-primary" aria-hidden="true" />
              <span className="text-sm font-medium text-foreground">
                {answeredCount} / {totalQuestions}
                <span className="sr-only"> questions answered</span>
              </span>
            </div>

            <AlertDialog>
              <AlertDialogTrigger asChild>
                <Button variant="outline" size="sm">
                  <LogOut className="mr-2 h-4 w-4" />
                  Logout
                </Button>
              </AlertDialogTrigger>
              <AlertDialogContent>
                <AlertDialogHeader>
                  <AlertDialogTitle>Log out?</AlertDialogTitle>
                  <AlertDialogDescription>
                    Your saved answers will be kept. You can resume this test later
                    by entering your PRN again.
                  </AlertDialogDescription>
                </AlertDialogHeader>
                <AlertDialogFooter>
                  <AlertDialogCancel>Stay in test</AlertDialogCancel>
                  <AlertDialogAction
                    onClick={() => void handleLogout()}
                    disabled={isLoggingOut}
                  >
                    {isLoggingOut ? "Logging out…" : "Log out"}
                  </AlertDialogAction>
                </AlertDialogFooter>
              </AlertDialogContent>
            </AlertDialog>

            <AlertDialog>
              <AlertDialogTrigger asChild>
                <Button variant="destructive" size="sm">
                  <Flag className="mr-2 h-4 w-4" />
                  End Test
                </Button>
              </AlertDialogTrigger>
              <AlertDialogContent>
                <AlertDialogHeader>
                  <AlertDialogTitle>End Test?</AlertDialogTitle>
                  <AlertDialogDescription>
                    You have answered <strong>{answeredCount} of {totalQuestions}</strong>{" "}
                    questions.
                    {answeredCount < totalQuestions && (
                      <span className="mt-2 block text-warning">
                        You still have {totalQuestions - answeredCount} unanswered
                        questions.
                      </span>
                    )}
                    <span className="mt-2 block">
                      Are you sure you want to submit your test? This action cannot be
                      undone.
                    </span>
                  </AlertDialogDescription>
                </AlertDialogHeader>
                <AlertDialogFooter>
                  <AlertDialogCancel>Continue Test</AlertDialogCancel>
                  <AlertDialogAction
                    onClick={() => void handleSubmit()}
                    disabled={isSubmitting || saveState === "error"}
                    className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
                  >
                    {isSubmitting ? "Submitting…" : "Submit Test"}
                  </AlertDialogAction>
                </AlertDialogFooter>
              </AlertDialogContent>
            </AlertDialog>
          </div>
        </div>

        <div className="mx-auto max-w-7xl px-4 pb-3 sm:px-6 lg:px-8">
          <div className="flex items-center gap-3">
            <Progress
              value={(answeredCount / totalQuestions) * 100}
              className="h-2 flex-1"
            />
            <span className="whitespace-nowrap text-xs text-muted-foreground">
              {Math.round((answeredCount / totalQuestions) * 100)}% Complete
            </span>
          </div>
        </div>
      </header>

      <div className="mx-auto max-w-7xl px-4 py-6 sm:px-6 lg:px-8">
        <div className="flex flex-col gap-6 lg:flex-row">
          <aside
            className={`${showNavigator ? "block" : "hidden"} shrink-0 lg:block lg:w-64`}
          >
            <Card>
              <CardContent className="p-4">
                <div className="mb-4 flex items-center justify-between">
                  <h2 className="font-semibold text-foreground">Questions</h2>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => setShowNavigator(false)}
                    className="lg:hidden"
                    aria-label="Hide question navigator"
                  >
                    Hide
                  </Button>
                </div>

                <div
                  className="grid grid-cols-5 gap-2"
                  role="navigation"
                  aria-label="Question navigator"
                >
                  {Array.from({ length: totalQuestions }, (_, i) => i + 1).map(
                    (pos) => {
                      const isAnswered =
                        answeredMap.has(pos) ||
                        (pos === position && !!questionData?.selected_option);
                      const isCurrent = pos === position;
                      return (
                        <button
                          key={pos}
                          type="button"
                          onClick={() => setPosition(pos)}
                          disabled={saveState === "error"}
                          className={`relative flex h-9 w-9 items-center justify-center rounded-md text-sm font-medium transition-colors focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-ring ${
                            isCurrent
                              ? "bg-primary text-primary-foreground"
                              : isAnswered
                                ? "border border-accent bg-accent/20 text-accent-foreground"
                                : "bg-secondary text-secondary-foreground hover:bg-secondary/80"
                          }`}
                          aria-label={`Question ${pos}${isAnswered ? ", answered" : ", not answered"}${isCurrent ? ", current" : ""}`}
                          aria-current={isCurrent ? "true" : undefined}
                        >
                          {pos}
                          {isAnswered && !isCurrent && (
                            <CheckCircle2
                              className="absolute -right-1 -top-1 h-3 w-3 text-accent"
                              aria-hidden="true"
                            />
                          )}
                        </button>
                      );
                    },
                  )}
                </div>

                <div className="mt-4 space-y-2 border-t border-border pt-4">
                  <div className="flex items-center gap-2 text-xs text-muted-foreground">
                    <div className="flex h-4 w-4 items-center justify-center rounded bg-primary">
                      <span className="text-[10px] text-primary-foreground">1</span>
                    </div>
                    <span>Current</span>
                  </div>
                  <div className="flex items-center gap-2 text-xs text-muted-foreground">
                    <div className="flex h-4 w-4 items-center justify-center rounded border border-accent bg-accent/20">
                      <CheckCircle2 className="h-2.5 w-2.5 text-accent" />
                    </div>
                    <span>Answered</span>
                  </div>
                  <div className="flex items-center gap-2 text-xs text-muted-foreground">
                    <div className="flex h-4 w-4 items-center justify-center rounded bg-secondary">
                      <Circle className="h-2 w-2 text-muted-foreground" />
                    </div>
                    <span>Not answered</span>
                  </div>
                </div>
              </CardContent>
            </Card>
          </aside>

          <div className="flex-1">
            <Card>
              <CardContent className="p-6 sm:p-8">
                {loadError ? (
                  <Alert variant="destructive">
                    <AlertDescription className="flex flex-wrap items-center justify-between gap-2">
                      <span>{loadError}</span>
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => void retryLoad(position)}
                      >
                        Retry
                      </Button>
                    </AlertDescription>
                  </Alert>
                ) : loading || !questionData ? (
                  <p className="text-muted-foreground">Loading question…</p>
                ) : (
                  <>
                    <div className="mb-6">
                      <span className="text-sm font-medium text-primary">
                        Question {position} of {totalQuestions}
                      </span>
                      <h1
                        ref={questionHeadingRef}
                        tabIndex={-1}
                        className="mt-2 text-xl font-semibold text-foreground outline-none sm:text-2xl"
                      >
                        {questionData.question.question_text}
                      </h1>
                    </div>

                    <fieldset className="space-y-4">
                      <legend className="sr-only">
                        Select your answer for question {position}
                      </legend>
                      <RadioGroup
                        value={questionData.selected_option ?? ""}
                        onValueChange={(value) =>
                          void saveAnswer(value as SelectedOption)
                        }
                        className="space-y-3"
                      >
                        {questionData.question.options.map((option) => (
                          <div key={option.key}>
                            <Label
                              htmlFor={`option-${option.key}`}
                              className={`flex cursor-pointer items-start gap-4 rounded-lg border-2 p-4 transition-colors hover:bg-secondary/50 ${
                                questionData.selected_option === option.key
                                  ? "border-primary bg-primary/5"
                                  : "border-border"
                              }`}
                            >
                              <RadioGroupItem
                                value={option.key}
                                id={`option-${option.key}`}
                                className="mt-0.5"
                              />
                              <div className="flex-1">
                                <span className="mr-2 inline-flex h-6 w-6 items-center justify-center rounded-full bg-secondary text-xs font-semibold text-secondary-foreground">
                                  {option.key}
                                </span>
                                <span className="text-foreground">{option.text}</span>
                              </div>
                            </Label>
                          </div>
                        ))}
                      </RadioGroup>
                    </fieldset>

                    <div className="mt-8 flex items-center justify-between">
                      <Button
                        type="button"
                        variant="outline"
                        onClick={() => handleNavigation("prev")}
                        aria-disabled={position === 1}
                        className={position === 1 ? "opacity-50" : ""}
                      >
                        <ChevronLeft className="mr-2 h-4 w-4" />
                        Previous
                      </Button>

                      <Button
                        type="button"
                        variant="ghost"
                        size="sm"
                        onClick={() => setShowNavigator(!showNavigator)}
                        className="lg:hidden"
                      >
                        {showNavigator ? "Hide" : "Show"} Navigator
                      </Button>

                      <Button
                        type="button"
                        onClick={() => handleNavigation("next")}
                        aria-disabled={position === totalQuestions}
                        className={position === totalQuestions ? "opacity-50" : ""}
                      >
                        Next
                        <ChevronRight className="ml-2 h-4 w-4" />
                      </Button>
                    </div>
                  </>
                )}
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </div>
  );
}

export default function TestPage() {
  return (
    <RouteGuard role="EXAMINEE" sessionStatus="ACTIVE" redirectTo="/">
      <TestPageContent />
    </RouteGuard>
  );
}
