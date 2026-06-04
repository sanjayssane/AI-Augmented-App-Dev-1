import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";

export default function HomePage() {
  return (
    <div className="mx-auto max-w-4xl px-4 py-12">
      <h1 className="text-3xl font-bold tracking-tight">MCQ Online Test Platform</h1>
      <p className="mt-2 text-muted-foreground">
        Phase 0 scaffold — production UI will be implemented here. See{" "}
        <code className="rounded bg-muted px-1 text-sm">SampleUI/</code> for UX reference.
      </p>

      <div className="mt-10 grid gap-6 sm:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Examinee</CardTitle>
            <CardDescription>Take the 50-question MCQ test</CardDescription>
          </CardHeader>
          <CardContent>
            <Button asChild>
              <Link href="/exam/test">Go to test (stub)</Link>
            </Button>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Examiner</CardTitle>
            <CardDescription>Manage questions and view results</CardDescription>
          </CardHeader>
          <CardContent>
            <Button asChild variant="outline">
              <Link href="/examiner/dashboard">Go to dashboard (stub)</Link>
            </Button>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
