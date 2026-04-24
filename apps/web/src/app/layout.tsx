import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "HealthcareAssistant",
  description: "Your personal AI-powered health tracker",
};

export const viewport = {
  width: "device-width",
  initialScale: 1,
  maximumScale: 1,
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
