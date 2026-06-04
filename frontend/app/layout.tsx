import type { Metadata } from "next";
import Link from "next/link";
import "./globals.css";

export const metadata: Metadata = {
  title: "MCQ Test Platform",
  description: "Role-Based Examination System with Examiner & Examinee Portals",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body>
        <a
          href="#main-content"
          className="sr-only focus:not-sr-only focus:absolute focus:left-4 focus:top-4 focus:z-50 focus:rounded focus:bg-primary focus:px-4 focus:py-2 focus:text-primary-foreground"
        >
          Skip to main content
        </a>
        <header className="border-b border-border bg-white">
          <nav
            className="mx-auto flex max-w-4xl items-center gap-4 px-4 py-3 text-sm"
            aria-label="Main"
          >
            <Link href="/" className="font-semibold text-primary">
              MCQ Platform
            </Link>
            <Link href="/exam/test" className="text-muted-foreground hover:text-foreground">
              Test
            </Link>
            <Link href="/exam/results" className="text-muted-foreground hover:text-foreground">
              Results
            </Link>
            <Link
              href="/examiner/dashboard"
              className="text-muted-foreground hover:text-foreground"
            >
              Examiner
            </Link>
          </nav>
        </header>
        <main id="main-content">{children}</main>
      </body>
    </html>
  );
}
