"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { ArrowLeft, Shield } from "lucide-react";
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
import { Checkbox } from "@/components/ui/checkbox";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
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
import { Separator } from "@/components/ui/separator";
import {
  createExaminer,
  eraseExaminee,
  getSettings,
  patchSettings,
} from "@/lib/api/examiner";
import { useAuth } from "@/lib/auth";
import { formatErrorMessage } from "@/lib/errors/problem";
import { usePageTitle } from "@/lib/hooks/use-page-title";
import type { PlatformSettingsOut, SelectionMode } from "@/lib/types";

export default function SettingsPage() {
  usePageTitle("Settings");
  const { user, csrfToken } = useAuth();
  const isAdmin = user?.is_admin ?? false;

  const [settings, setSettings] = useState<PlatformSettingsOut | null>(null);
  const [retentionDays, setRetentionDays] = useState(730);
  const [allowRetake, setAllowRetake] = useState(false);
  const [selectionMode, setSelectionMode] = useState<SelectionMode>("FIXED_ORDER");
  const [newUsername, setNewUsername] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [eraseUserId, setEraseUserId] = useState("");
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    getSettings()
      .then((data) => {
        setSettings(data);
        setRetentionDays(data.retention_days_completed);
        setAllowRetake(data.allow_examinee_retake);
        setSelectionMode(data.question_selection_mode);
      })
      .catch((err) =>
        setError(formatErrorMessage(err, "Failed to load settings.")),
      );
  }, []);

  const handleSaveSettings = async () => {
    if (!csrfToken || !isAdmin) return;
    setSaving(true);
    setError("");
    try {
      const updated = await patchSettings(csrfToken, {
        retention_days_completed: retentionDays,
        allow_examinee_retake: allowRetake,
        question_selection_mode: selectionMode,
      });
      setSettings(updated);
      setMessage("Settings saved successfully.");
    } catch (err) {
      setError(formatErrorMessage(err, "Failed to save settings."));
    } finally {
      setSaving(false);
    }
  };

  const handleCreateExaminer = async () => {
    if (!csrfToken || !isAdmin) return;
    setSaving(true);
    setError("");
    try {
      await createExaminer(csrfToken, {
        username: newUsername,
        password: newPassword,
        force_password_change: true,
      });
      setMessage(`Examiner "${newUsername}" created.`);
      setNewUsername("");
      setNewPassword("");
    } catch (err) {
      setError(formatErrorMessage(err, "Failed to create the examiner."));
    } finally {
      setSaving(false);
    }
  };

  const handleErase = async () => {
    if (!csrfToken || !isAdmin || !eraseUserId) return;
    setError("");
    try {
      const result = await eraseExaminee(eraseUserId, csrfToken);
      setMessage(`Erasure job accepted (job ${result.job_id}).`);
      setEraseUserId("");
    } catch (err) {
      setError(formatErrorMessage(err, "Failed to start the erasure job."));
    }
  };

  if (!isAdmin) {
    return (
      <div className="mx-auto max-w-3xl px-4 py-12">
        <Alert>
          <AlertDescription>
            Admin privileges are required to access settings.{" "}
            <Link href="/examiner/dashboard" className="underline">
              Return to dashboard
            </Link>
          </AlertDescription>
        </Alert>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background">
      <header className="border-b border-border bg-card">
        <div className="mx-auto flex max-w-3xl items-center gap-3 px-4 py-4">
          <Shield className="h-6 w-6 text-primary" />
          <h1 className="text-lg font-semibold">Platform Settings</h1>
        </div>
      </header>

      <div className="mx-auto max-w-3xl px-4 py-8">
        <Button variant="ghost" className="mb-6" asChild>
          <Link href="/examiner/dashboard">
            <ArrowLeft className="mr-2 h-4 w-4" />
            Back to Dashboard
          </Link>
        </Button>

        {message && (
          <Alert className="mb-6">
            <AlertDescription>{message}</AlertDescription>
          </Alert>
        )}
        {error && (
          <Alert variant="destructive" className="mb-6">
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        )}

        <Card className="mb-6">
          <CardHeader>
            <CardTitle>Institution Settings</CardTitle>
            <CardDescription>
              Configure retention, retake policy, and question selection
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="retention">Retention Days (completed tests)</Label>
              <Input
                id="retention"
                type="number"
                min={1}
                max={3650}
                value={retentionDays}
                onChange={(e) => setRetentionDays(Number(e.target.value))}
              />
            </div>
            <div className="flex items-center gap-2">
              <Checkbox
                id="retake"
                checked={allowRetake}
                onCheckedChange={(c) => setAllowRetake(c === true)}
              />
              <Label htmlFor="retake">Allow examinee retake</Label>
            </div>
            <div className="space-y-2">
              <Label>Question Selection Mode</Label>
              <Select
                value={selectionMode}
                onValueChange={(v) => setSelectionMode(v as SelectionMode)}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="FIXED_ORDER">Fixed Order</SelectItem>
                  <SelectItem value="RANDOM_SAMPLE">Random Sample</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <Button onClick={() => void handleSaveSettings()} disabled={saving}>
              {saving ? "Saving…" : "Save Settings"}
            </Button>
          </CardContent>
        </Card>

        <Separator className="my-8" />

        <Card className="mb-6">
          <CardHeader>
            <CardTitle>Create Examiner</CardTitle>
            <CardDescription>
              Password must be at least 12 characters with upper, lower, and digit
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="username">Username</Label>
              <Input
                id="username"
                value={newUsername}
                onChange={(e) => setNewUsername(e.target.value)}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="new-password">Password</Label>
              <Input
                id="new-password"
                type="password"
                value={newPassword}
                onChange={(e) => setNewPassword(e.target.value)}
              />
            </div>
            <Button
              onClick={() => void handleCreateExaminer()}
              disabled={saving || !newUsername || !newPassword}
            >
              Create Examiner
            </Button>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>GDPR Erasure</CardTitle>
            <CardDescription>
              Permanently anonymise an examinee&apos;s personal data. Enter the
              examinee user ID from a session detail page.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="erase-user-id">Examinee User ID</Label>
              <Input
                id="erase-user-id"
                value={eraseUserId}
                onChange={(e) => setEraseUserId(e.target.value)}
                placeholder="UUID from session detail"
              />
            </div>
            <AlertDialog>
              <AlertDialogTrigger asChild>
                <Button variant="destructive" disabled={!eraseUserId}>
                  Request Erasure
                </Button>
              </AlertDialogTrigger>
              <AlertDialogContent>
                <AlertDialogHeader>
                  <AlertDialogTitle>Confirm Data Erasure</AlertDialogTitle>
                  <AlertDialogDescription>
                    This will permanently anonymise all personal data for this
                    examinee. This action cannot be undone.
                  </AlertDialogDescription>
                </AlertDialogHeader>
                <AlertDialogFooter>
                  <AlertDialogCancel>Cancel</AlertDialogCancel>
                  <AlertDialogAction onClick={() => void handleErase()}>
                    Confirm Erasure
                  </AlertDialogAction>
                </AlertDialogFooter>
              </AlertDialogContent>
            </AlertDialog>
          </CardContent>
        </Card>

        {settings && (
          <p className="mt-6 text-xs text-muted-foreground">
            Current: retention {settings.retention_days_completed} days, retake{" "}
            {settings.allow_examinee_retake ? "enabled" : "disabled"},{" "}
            {settings.question_selection_mode}
          </p>
        )}
      </div>
    </div>
  );
}
