import type { Metadata } from "next";
import "./globals.css";
import SidebarNav from "@/components/ui/SidebarNav";

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
        <div className="app-shell">
          <SidebarNav />
          <main className="main-content">{children}</main>
        </div>
      </body>
    </html>
  );
}
