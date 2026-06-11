"use client";

import { useEffect, useState, type ReactNode } from "react";
import Link from "next/link";
import {
  GraduationCap,
  CheckCircle2,
  XCircle,
  MinusCircle,
  Trophy,
  BarChart3,
  FileText,
  Home,
  Download,
  ChevronDown,
  ChevronUp,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { RouteGuard } from "@/components/route-guard";
import { downloadBlob } from "@/lib/api/client";
import { exportMyData, fetchReview } from "@/lib/api/examinee";
import { formatErrorMessage } from "@/lib/errors/problem";
import { useAuth } from "@/lib/auth";
import { usePageTitle } from "@/lib/hooks/use-page-title";
import { useStatusAnnouncer } from "@/components/status-announcer";
import type { ReviewItem } from "@/lib/types";

function ResultsContent() {
  usePageTitle("Results");
  const { examineeSession, lastSubmitResult } = useAuth();
  const { announceAssertive } = useStatusAnnouncer();
  const [reviewItems, setReviewItems] = useState<ReviewItem[]>([]);
  const [loadingReview, setLoadingReview] = useState(false);
  const [reviewError, setReviewError] = useState("");
  const [exportError, setExportError] = useState("");
  const [expandedQuestions, setExpandedQuestions] = useState<Set<number>>(new Set());

  const computedFromReview =
    reviewItems.length > 0
      ? {
          correct_count: reviewItems.filter((i) => i.is_correct === true).length,
          incorrect_count: reviewItems.filter((i) => i.is_correct === false).length,
          unattempted_count: reviewItems.filter((i) => i.is_correct === null).length,
        }
      : null;

  const sessionId =
    examineeSession?.session_id ?? lastSubmitResult?.session_id;

  useEffect(() => {
    if (!sessionId) return;
    setLoadingReview(true);
    setReviewError("");
    fetchReview(sessionId)
      .then((data) => setReviewItems(data.items))
      .catch((err) => {
        setReviewItems([]);
        setReviewError(formatErrorMessage(err, "Failed to load the answer review."));
      })
      .finally(() => setLoadingReview(false));
  }, [sessionId]);

  useEffect(() => {
    if (lastSubmitResult) {
      announceAssertive(
        `Your score is ${lastSubmitResult.score} out of ${lastSubmitResult.max_score}.`,
      );
    }
  }, [lastSubmitResult, announceAssertive]);

  const score = lastSubmitResult?.score ?? computedFromReview?.correct_count ?? 0;
  const maxScore = lastSubmitResult?.max_score ?? 50;
  const correctCount =
    lastSubmitResult?.correct_count ?? computedFromReview?.correct_count ?? 0;
  const incorrectCount =
    lastSubmitResult?.incorrect_count ?? computedFromReview?.incorrect_count ?? 0;
  const unattemptedCount =
    lastSubmitResult?.unattempted_count ?? computedFromReview?.unattempted_count ?? 0;
  const submittedAt = lastSubmitResult?.submitted_at;
  const scorePercentage = (score / maxScore) * 100;

  const getPerformanceLevel = () => {
    if (scorePercentage >= 90) return { label: "Excellent", color: "text-accent" };
    if (scorePercentage >= 75) return { label: "Good", color: "text-primary" };
    if (scorePercentage >= 50) return { label: "Satisfactory", color: "text-warning" };
    return { label: "Needs Improvement", color: "text-destructive" };
  };

  const performance = getPerformanceLevel();

  const toggleQuestion = (position: number) => {
    setExpandedQuestions((prev) => {
      const next = new Set(prev);
      if (next.has(position)) next.delete(position);
      else next.add(position);
      return next;
    });
  };

  const handleExportData = async () => {
    setExportError("");
    try {
      const blob = await exportMyData();
      downloadBlob(blob, "my-data-export.json");
    } catch (err) {
      setExportError(formatErrorMessage(err, "Failed to export your data."));
    }
  };

  return (
    <div className="min-h-screen bg-background">
      <header className="border-b border-border bg-card">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-4 py-4 sm:px-6 lg:px-8">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary">
              <GraduationCap className="h-6 w-6 text-primary-foreground" />
            </div>
            <div>
              <h1 className="text-lg font-semibold text-foreground">Test Results</h1>
              <p className="text-xs text-muted-foreground">MCQ Examination Complete</p>
            </div>
          </div>
          <Button variant="outline" size="sm" asChild>
            <Link href="/">
              <Home className="mr-2 h-4 w-4" />
              Home
            </Link>
          </Button>
        </div>
      </header>

      <div className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
        <Tabs defaultValue="summary">
          <TabsList className="mb-6">
            <TabsTrigger value="summary">
              <Trophy className="mr-2 h-4 w-4" />
              Summary
            </TabsTrigger>
            <TabsTrigger value="review">
              <FileText className="mr-2 h-4 w-4" />
              Review Answers
            </TabsTrigger>
          </TabsList>

          <TabsContent value="summary">
            <div className="grid gap-6 lg:grid-cols-3">
              <Card className="lg:col-span-2">
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Trophy className="h-6 w-6 text-primary" />
                    Your Score
                  </CardTitle>
                  <CardDescription>
                    {submittedAt &&
                      `Submitted on ${new Date(submittedAt).toLocaleString()}`}
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="flex flex-col items-center gap-6 sm:flex-row">
                    <div className="text-center sm:text-left">
                      <p className="text-5xl font-bold text-foreground">
                        {score}
                        <span className="text-2xl text-muted-foreground">
                          {" "}/ {maxScore}
                        </span>
                      </p>
                      <p className={`mt-2 text-lg font-medium ${performance.color}`}>
                        {performance.label}
                      </p>
                    </div>
                    <div className="flex-1 w-full">
                      <Progress value={scorePercentage} className="h-4" />
                      <p className="mt-2 text-sm text-muted-foreground text-center sm:text-right">
                        {Math.round(scorePercentage)}% correct
                      </p>
                    </div>
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2 text-base">
                    <BarChart3 className="h-5 w-5" />
                    Breakdown
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="flex items-center justify-between">
                    <span className="flex items-center gap-2 text-sm">
                      <CheckCircle2 className="h-4 w-4 text-accent" />
                      Correct
                    </span>
                    <Badge variant="secondary">{correctCount}</Badge>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="flex items-center gap-2 text-sm">
                      <XCircle className="h-4 w-4 text-destructive" />
                      Incorrect
                    </span>
                    <Badge variant="secondary">{incorrectCount}</Badge>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="flex items-center gap-2 text-sm">
                      <MinusCircle className="h-4 w-4 text-muted-foreground" />
                      Unattempted
                    </span>
                    <Badge variant="secondary">{unattemptedCount}</Badge>
                  </div>
                </CardContent>
              </Card>
            </div>

            <div className="mt-6">
              <Button variant="outline" onClick={() => void handleExportData()}>
                <Download className="mr-2 h-4 w-4" />
                Download My Data (GDPR)
              </Button>
              {exportError && (
                <Alert variant="destructive" className="mt-4">
                  <AlertDescription>{exportError}</AlertDescription>
                </Alert>
              )}
            </div>
          </TabsContent>

          <TabsContent value="review">
            <Card>
              <CardHeader>
                <CardTitle>Answer Review</CardTitle>
                <CardDescription>
                  Review your submitted answers and the correct responses
                </CardDescription>
              </CardHeader>
              <CardContent>
                {loadingReview ? (
                  <p className="text-muted-foreground">Loading review…</p>
                ) : reviewError ? (
                  <Alert variant="destructive">
                    <AlertDescription>{reviewError}</AlertDescription>
                  </Alert>
                ) : (
                  <ScrollArea className="h-[600px] pr-4">
                    <div className="space-y-3">
                      {reviewItems.map((item) => {
                        const isExpanded = expandedQuestions.has(item.position);
                        const statusIcon =
                          item.is_correct === true ? (
                            <CheckCircle2 className="h-5 w-5 text-accent" aria-label="Correct" />
                          ) : item.is_correct === false ? (
                            <XCircle className="h-5 w-5 text-destructive" aria-label="Incorrect" />
                          ) : (
                            <MinusCircle className="h-5 w-5 text-muted-foreground" aria-label="Unattempted" />
                          );
                        return (
                          <div
                            key={item.position}
                            className="rounded-lg border border-border"
                          >
                            <button
                              type="button"
                              className="flex w-full items-center justify-between p-4 text-left hover:bg-muted/50"
                              onClick={() => toggleQuestion(item.position)}
                              aria-expanded={isExpanded}
                            >
                              <div className="flex items-center gap-3">
                                {statusIcon}
                                <span className="font-medium">
                                  Q{item.position}: {item.question_text.slice(0, 80)}
                                  {item.question_text.length > 80 ? "…" : ""}
                                </span>
                              </div>
                              {isExpanded ? (
                                <ChevronUp className="h-4 w-4" />
                              ) : (
                                <ChevronDown className="h-4 w-4" />
                              )}
                            </button>
                            {isExpanded && (
                              <div className="border-t border-border px-4 pb-4 pt-2">
                                <p className="mb-2 text-sm text-foreground">
                                  {item.question_text}
                                </p>
                                <ul className="space-y-1 text-sm">
                                  {item.options.map((opt) => (
                                    <li
                                      key={opt.key}
                                      className={
                                        opt.key === item.correct_option
                                          ? "font-medium text-accent"
                                          : opt.key === item.selected_option
                                            ? "text-foreground"
                                            : "text-muted-foreground"
                                      }
                                    >
                                      {opt.key}: {opt.text}
                                      {opt.key === item.selected_option && " (your answer)"}
                                      {opt.key === item.correct_option && " (correct)"}
                                    </li>
                                  ))}
                                </ul>
                              </div>
                            )}
                          </div>
                        );
                      })}
                    </div>
                  </ScrollArea>
                )}
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
}

function ResultsPageGuard({ children }: { children: ReactNode }) {
  const { user, isLoading, examineeSession, lastSubmitResult } = useAuth();

  if (isLoading) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <p className="text-muted-foreground">Loading…</p>
      </div>
    );
  }

  if (!user || user.role !== "EXAMINEE") return null;
  if (
    examineeSession?.status !== "COMPLETED" &&
    !lastSubmitResult
  ) {
    return null;
  }

  return <>{children}</>;
}

export default function ResultsPage() {
  return (
    <RouteGuard role="EXAMINEE" redirectTo="/">
      <ResultsPageGuard>
        <ResultsContent />
      </ResultsPageGuard>
    </RouteGuard>
  );
}
