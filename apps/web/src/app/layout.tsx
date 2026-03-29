import type { Metadata } from "next";
import "./globals.css";
import AppShell from "@/components/ui/AppShell";

export const metadata: Metadata = {
  title: "HealthcareAssistant",
  description: "Your personal AI-powered health tracker",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>
        <AppShell>{children}</AppShell>
      </body>
    </html>
  );
}
