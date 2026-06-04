import Link from "next/link";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

type PlaceholderPageProps = {
  title: string;
  description: string;
  backHref: string;
  backLabel: string;
};

export function PlaceholderPage({
  title,
  description,
  backHref,
  backLabel,
}: PlaceholderPageProps) {
  return (
    <div className="mx-auto max-w-2xl px-4 py-12">
      <Card>
        <CardHeader>
          <CardTitle>{title}</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <p className="text-muted-foreground">{description}</p>
          <p className="rounded-md border border-dashed border-border bg-muted px-4 py-3 text-sm">
            Under construction — Phase 0 scaffold route only.
          </p>
          <Link href={backHref} className="text-sm font-medium text-primary hover:underline">
            ← {backLabel}
          </Link>
        </CardContent>
      </Card>
    </div>
  );
}
