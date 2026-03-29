import type { Metadata } from "next";
import "./globals.css";
<<<<<<< HEAD
import AppShell from "@/components/ui/AppShell";
=======
import SidebarNav from "@/components/ui/SidebarNav";
>>>>>>> 32e7e8429f7cd41eff9a8ad873be60f1e5e19156

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
<<<<<<< HEAD
        <AppShell>{children}</AppShell>
=======
        <div className="app-shell">
          <SidebarNav />
          <main className="main-content">{children}</main>
        </div>
>>>>>>> 32e7e8429f7cd41eff9a8ad873be60f1e5e19156
      </body>
    </html>
  );
}
