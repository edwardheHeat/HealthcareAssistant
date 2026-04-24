import SidebarNav from "@/components/ui/SidebarNav";

export default function AppLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="app-shell">
      <SidebarNav />
      <main className="main-content">{children}</main>
    </div>
  );
}
