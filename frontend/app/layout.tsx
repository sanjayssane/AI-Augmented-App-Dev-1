import type { Metadata } from "next";
import { AuthProvider } from "@/lib/auth/auth-provider";
import { StatusAnnouncerProvider } from "@/components/status-announcer";
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
          className="sr-only focus:not-sr-only focus:absolute focus:left-4 focus:top-4 focus:z-50 focus:rounded-md focus:bg-primary focus:px-4 focus:py-2 focus:text-primary-foreground"
        >
          Skip to main content
        </a>
        <AuthProvider>
          <StatusAnnouncerProvider>
            <main id="main-content">{children}</main>
          </StatusAnnouncerProvider>
        </AuthProvider>
      </body>
    </html>
  );
}
