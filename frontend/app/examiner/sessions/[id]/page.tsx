"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { ArrowLeft, CheckCircle2, XCircle, MinusCircle } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { getSessionDetail } from "@/lib/api/examiner";
import { usePageTitle } from "@/lib/hooks/use-page-title";
import type { SessionDetailOut } from "@/lib/types";

export default function SessionDetailPage() {
  const params = useParams();
  const sessionId = params.id as string;
  const [detail, setDetail] = useState<SessionDetailOut | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  usePageTitle(detail ? `Session ${detail.prn ?? sessionId}` : "Session Detail");

  useEffect(() => {
    getSessionDetail(sessionId)
      .then(setDetail)
      .catch((err) =>
        setError(err instanceof Error ? err.message : "Failed to load session"),
      )
      .finally(() => setLoading(false));
  }, [sessionId]);

  if (loading) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <p className="text-muted-foreground">Loading session…</p>
      </div>
    );
  }

  if (error || !detail) {
    return (
      <div className="mx-auto max-w-7xl px-4 py-12">
        <p className="text-destructive">{error || "Session not found"}</p>
        <Button variant="outline" className="mt-4" asChild>
          <Link href="/examiner/dashboard">Back to dashboard</Link>
        </Button>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background">
      <div className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
        <Button variant="ghost" className="mb-6" asChild>
          <Link href="/examiner/dashboard">
            <ArrowLeft className="mr-2 h-4 w-4" />
            Back to Dashboard
          </Link>
        </Button>

        <Card className="mb-6">
          <CardHeader>
            <CardTitle>Session Details</CardTitle>
            <CardDescription>
              {detail.prn} — {detail.name}
            </CardDescription>
          </CardHeader>
          <CardContent>
            <dl className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
              <div>
                <dt className="text-sm text-muted-foreground">Score</dt>
                <dd className="text-lg font-semibold">
                  {detail.score !== null ? `${detail.score} / 50` : "—"}
                </dd>
              </div>
              <div>
                <dt className="text-sm text-muted-foreground">Status</dt>
                <dd>
                  <Badge>{detail.status}</Badge>
                </dd>
              </div>
              <div>
                <dt className="text-sm text-muted-foreground">Started</dt>
                <dd>{new Date(detail.started_at).toLocaleString()}</dd>
              </div>
              <div>
                <dt className="text-sm text-muted-foreground">Submitted</dt>
                <dd>
                  {detail.submitted_at
                    ? new Date(detail.submitted_at).toLocaleString()
                    : "—"}
                </dd>
              </div>
              <div className="sm:col-span-2">
                <dt className="text-sm text-muted-foreground">Examinee User ID</dt>
                <dd className="font-mono text-sm">{detail.user_id}</dd>
              </div>
            </dl>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Responses</CardTitle>
          </CardHeader>
          <CardContent>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>#</TableHead>
                  <TableHead>Question</TableHead>
                  <TableHead>Selected</TableHead>
                  <TableHead>Correct</TableHead>
                  <TableHead>Result</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {detail.responses.map((r) => (
                  <TableRow key={r.question_id}>
                    <TableCell>{r.position}</TableCell>
                    <TableCell className="max-w-md truncate">
                      {r.question_text}
                    </TableCell>
                    <TableCell>{r.selected_option ?? "—"}</TableCell>
                    <TableCell>{r.correct_option}</TableCell>
                    <TableCell>
                      {r.is_correct === true && (
                        <CheckCircle2 className="h-5 w-5 text-accent" aria-label="Correct" />
                      )}
                      {r.is_correct === false && (
                        <XCircle className="h-5 w-5 text-destructive" aria-label="Incorrect" />
                      )}
                      {r.is_correct === null && (
                        <MinusCircle
                          className="h-5 w-5 text-muted-foreground"
                          aria-label="Unattempted"
                        />
                      )}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
