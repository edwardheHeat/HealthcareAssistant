"use client";

import { usePathname } from "next/navigation";
import SidebarNav from "./SidebarNav";
import { useAuthGuard } from "@/hooks/useAuthGuard";

const NO_SHELL_ROUTES = ["/login", "/signup", "/onboarding"];

export default function AppShell({ children }: { children: React.ReactNode }) {
  useAuthGuard();
  const pathname = usePathname();
  const showShell = !NO_SHELL_ROUTES.some((r) => pathname.startsWith(r));

  if (!showShell) {
    return <>{children}</>;
  }

  return (
    <div className="app-shell">
      <SidebarNav />
      <main className="main-content">{children}</main>
    </div>
  );
}
