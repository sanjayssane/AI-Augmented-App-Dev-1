"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import {
  Shield,
  Plus,
  Pencil,
  Trash2,
  Download,
  LogOut,
  Eye,
  AlertTriangle,
  Settings,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
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
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { downloadBlob } from "@/lib/api/client";
import {
  createQuestion,
  deleteQuestion,
  exportSessionsCsv,
  listQuestions,
  listSessions,
  patchQuestion,
} from "@/lib/api/examiner";
import { useAuth } from "@/lib/auth";
import { formatErrorMessage } from "@/lib/errors/problem";
import { usePageTitle } from "@/lib/hooks/use-page-title";
import type { CorrectOption, QuestionOut, SessionSummaryOut } from "@/lib/types";

const emptyQuestionForm = {
  question_text: "",
  option_a: "",
  option_b: "",
  option_c: "",
  option_d: "",
  correct_option: "A" as CorrectOption,
};

export default function ExaminerDashboardPage() {
  usePageTitle("Examiner Dashboard");
  const router = useRouter();
  const { user, csrfToken, logout } = useAuth();

  const [questions, setQuestions] = useState<QuestionOut[]>([]);
  const [activeCount, setActiveCount] = useState(0);
  const [questionsCursor, setQuestionsCursor] = useState<string | null>(null);
  const [sessions, setSessions] = useState<SessionSummaryOut[]>([]);
  const [sessionsCursor, setSessionsCursor] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const [dialogOpen, setDialogOpen] = useState(false);
  const [editingQuestion, setEditingQuestion] = useState<QuestionOut | null>(null);
  const [form, setForm] = useState(emptyQuestionForm);
  const [saving, setSaving] = useState(false);

  const loadQuestions = useCallback(async (cursor?: string) => {
    const data = await listQuestions({ cursor, limit: 50 });
    setQuestions((prev) => (cursor ? [...prev, ...data.items] : data.items));
    setQuestionsCursor(data.next_cursor);
    setActiveCount(data.active_count);
  }, []);

  const loadSessions = useCallback(async (cursor?: string) => {
    const data = await listSessions({ cursor, limit: 50 });
    setSessions((prev) => (cursor ? [...prev, ...data.items] : data.items));
    setSessionsCursor(data.next_cursor);
  }, []);

  useEffect(() => {
    Promise.all([loadQuestions(), loadSessions()])
      .catch((err) => {
        setError(formatErrorMessage(err, "Failed to load dashboard data."));
      })
      .finally(() => setLoading(false));
  }, [loadQuestions, loadSessions]);

  const openAddDialog = () => {
    setEditingQuestion(null);
    setForm(emptyQuestionForm);
    setDialogOpen(true);
  };

  const openEditDialog = (q: QuestionOut) => {
    setEditingQuestion(q);
    setForm({
      question_text: q.question_text,
      option_a: q.option_a,
      option_b: q.option_b,
      option_c: q.option_c,
      option_d: q.option_d,
      correct_option: q.correct_option,
    });
    setDialogOpen(true);
  };

  const handleSaveQuestion = async () => {
    if (!csrfToken) return;
    setSaving(true);
    setError("");
    try {
      if (editingQuestion) {
        await patchQuestion(editingQuestion.question_id, csrfToken, form);
      } else {
        await createQuestion(csrfToken, form);
      }
      setDialogOpen(false);
      await loadQuestions();
    } catch (err) {
      setError(formatErrorMessage(err, "Failed to save the question."));
    } finally {
      setSaving(false);
    }
  };

  const handleDeleteQuestion = async (questionId: string) => {
    if (!csrfToken) return;
    setError("");
    try {
      await deleteQuestion(questionId, csrfToken);
      await loadQuestions();
    } catch (err) {
      setError(formatErrorMessage(err, "Failed to delete the question."));
    }
  };

  const handleExport = async () => {
    setError("");
    try {
      const blob = await exportSessionsCsv(false);
      downloadBlob(blob, "sessions-export.csv");
    } catch (err) {
      setError(formatErrorMessage(err, "Failed to export sessions."));
    }
  };

  const handleLogout = async () => {
    await logout();
    router.push("/");
  };

  if (loading) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <p className="text-muted-foreground">Loading dashboard…</p>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background">
      <header className="border-b border-border bg-card">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-4 py-4 sm:px-6 lg:px-8">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary">
              <Shield className="h-6 w-6 text-primary-foreground" />
            </div>
            <div>
              <h1 className="text-lg font-semibold text-foreground">
                Examiner Dashboard
              </h1>
              <p className="text-xs text-muted-foreground">
                Welcome, {user?.username ?? "Examiner"}
              </p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            {user?.is_admin && (
              <Button variant="outline" size="sm" asChild>
                <Link href="/examiner/settings">
                  <Settings className="mr-2 h-4 w-4" />
                  Settings
                </Link>
              </Button>
            )}
            <Button variant="outline" size="sm" onClick={() => void handleLogout()}>
              <LogOut className="mr-2 h-4 w-4" />
              Logout
            </Button>
          </div>
        </div>
      </header>

      <div className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
        {error && (
          <Alert variant="destructive" className="mb-6">
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        )}

        {activeCount < 55 && activeCount >= 50 && (
          <Alert className="mb-6">
            <AlertTriangle className="h-4 w-4" />
            <AlertDescription>
              Active question bank: {activeCount}. Minimum 50 required for new
              sessions. Consider adding more questions.
            </AlertDescription>
          </Alert>
        )}

        <Tabs defaultValue="questions">
          <TabsList>
            <TabsTrigger value="questions">Question Bank</TabsTrigger>
            <TabsTrigger value="results">Results</TabsTrigger>
          </TabsList>

          <TabsContent value="questions" className="mt-6">
            <Card>
              <CardHeader className="flex flex-row items-center justify-between">
                <div>
                  <CardTitle>Questions</CardTitle>
                  <CardDescription>
                    {activeCount} active questions in the bank
                  </CardDescription>
                </div>
                <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
                  <DialogTrigger asChild>
                    <Button onClick={openAddDialog}>
                      <Plus className="mr-2 h-4 w-4" />
                      Add Question
                    </Button>
                  </DialogTrigger>
                  <DialogContent className="max-h-[90vh] overflow-y-auto sm:max-w-lg">
                    <DialogHeader>
                      <DialogTitle>
                        {editingQuestion ? "Edit Question" : "Add Question"}
                      </DialogTitle>
                      <DialogDescription>
                        All fields are required. Maximum 2000 characters for
                        question text.
                      </DialogDescription>
                    </DialogHeader>
                    <div className="space-y-4 py-4">
                      <div className="space-y-2">
                        <Label htmlFor="question_text">Question Text</Label>
                        <Textarea
                          id="question_text"
                          value={form.question_text}
                          onChange={(e) =>
                            setForm({ ...form, question_text: e.target.value })
                          }
                          maxLength={2000}
                          rows={3}
                        />
                      </div>
                      {(["a", "b", "c", "d"] as const).map((key) => (
                        <div key={key} className="space-y-2">
                          <Label htmlFor={`option_${key}`}>Option {key.toUpperCase()}</Label>
                          <Input
                            id={`option_${key}`}
                            value={form[`option_${key}`]}
                            onChange={(e) =>
                              setForm({
                                ...form,
                                [`option_${key}`]: e.target.value,
                              })
                            }
                            maxLength={500}
                          />
                        </div>
                      ))}
                      <div className="space-y-2">
                        <Label>Correct Answer</Label>
                        <Select
                          value={form.correct_option}
                          onValueChange={(v) =>
                            setForm({ ...form, correct_option: v as CorrectOption })
                          }
                        >
                          <SelectTrigger>
                            <SelectValue />
                          </SelectTrigger>
                          <SelectContent>
                            {(["A", "B", "C", "D"] as const).map((opt) => (
                              <SelectItem key={opt} value={opt}>
                                {opt}
                              </SelectItem>
                            ))}
                          </SelectContent>
                        </Select>
                      </div>
                    </div>
                    <DialogFooter>
                      <Button
                        onClick={() => void handleSaveQuestion()}
                        disabled={saving}
                      >
                        {saving ? "Saving…" : "Save"}
                      </Button>
                    </DialogFooter>
                  </DialogContent>
                </Dialog>
              </CardHeader>
              <CardContent>
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Question</TableHead>
                      <TableHead>Answer</TableHead>
                      <TableHead>Version</TableHead>
                      <TableHead className="text-right">Actions</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {questions.map((q) => (
                      <TableRow key={q.question_id}>
                        <TableCell className="max-w-md truncate">
                          {q.question_text}
                        </TableCell>
                        <TableCell>
                          <Badge>{q.correct_option}</Badge>
                        </TableCell>
                        <TableCell>v{q.question_version}</TableCell>
                        <TableCell className="text-right">
                          <div className="flex justify-end gap-2">
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => openEditDialog(q)}
                              aria-label="Edit question"
                            >
                              <Pencil className="h-4 w-4" />
                            </Button>
                            <AlertDialog>
                              <AlertDialogTrigger asChild>
                                <Button
                                  variant="ghost"
                                  size="sm"
                                  aria-label="Delete question"
                                >
                                  <Trash2 className="h-4 w-4 text-destructive" />
                                </Button>
                              </AlertDialogTrigger>
                              <AlertDialogContent>
                                <AlertDialogHeader>
                                  <AlertDialogTitle>Delete Question?</AlertDialogTitle>
                                  <AlertDialogDescription>
                                    This will soft-delete the question. It will not
                                    appear in new test sessions.
                                    {activeCount <= 50 && (
                                      <span className="mt-2 block text-warning">
                                        Warning: deleting may bring the bank below
                                        the minimum of 50 active questions.
                                      </span>
                                    )}
                                  </AlertDialogDescription>
                                </AlertDialogHeader>
                                <AlertDialogFooter>
                                  <AlertDialogCancel>Cancel</AlertDialogCancel>
                                  <AlertDialogAction
                                    onClick={() =>
                                      void handleDeleteQuestion(q.question_id)
                                    }
                                  >
                                    Delete
                                  </AlertDialogAction>
                                </AlertDialogFooter>
                              </AlertDialogContent>
                            </AlertDialog>
                          </div>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
                {questionsCursor && (
                  <div className="mt-4 text-center">
                    <Button
                      variant="outline"
                      onClick={() => void loadQuestions(questionsCursor)}
                    >
                      Load more
                    </Button>
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="results" className="mt-6">
            <Card>
              <CardHeader className="flex flex-row items-center justify-between">
                <div>
                  <CardTitle>Test Results</CardTitle>
                  <CardDescription>
                    View completed examinee sessions
                  </CardDescription>
                </div>
                <Button variant="outline" onClick={() => void handleExport()}>
                  <Download className="mr-2 h-4 w-4" />
                  Export CSV
                </Button>
              </CardHeader>
              <CardContent>
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>PRN</TableHead>
                      <TableHead>Name</TableHead>
                      <TableHead>Score</TableHead>
                      <TableHead>Submitted</TableHead>
                      <TableHead>Status</TableHead>
                      <TableHead className="text-right">Actions</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {sessions.map((s) => (
                      <TableRow key={s.session_id}>
                        <TableCell>{s.prn ?? "—"}</TableCell>
                        <TableCell>{s.name ?? "—"}</TableCell>
                        <TableCell>
                          {s.score !== null ? `${s.score} / 50` : "—"}
                        </TableCell>
                        <TableCell>
                          {s.submitted_at
                            ? new Date(s.submitted_at).toLocaleString()
                            : "—"}
                        </TableCell>
                        <TableCell>
                          <Badge variant="secondary">{s.status}</Badge>
                        </TableCell>
                        <TableCell className="text-right">
                          <Button variant="ghost" size="sm" asChild>
                            <Link href={`/examiner/sessions/${s.session_id}`}>
                              <Eye className="mr-1 h-4 w-4" />
                              Details
                            </Link>
                          </Button>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
                {sessionsCursor && (
                  <div className="mt-4 text-center">
                    <Button
                      variant="outline"
                      onClick={() => void loadSessions(sessionsCursor)}
                    >
                      Load more
                    </Button>
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
}
