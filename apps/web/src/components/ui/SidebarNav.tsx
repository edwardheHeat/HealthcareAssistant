"use client";

import Link from "next/link";
<<<<<<< HEAD
import { usePathname, useRouter } from "next/navigation";
import { getSession, clearSession } from "@/lib/auth";
import { useEffect, useState } from "react";
=======
import { usePathname } from "next/navigation";
>>>>>>> 32e7e8429f7cd41eff9a8ad873be60f1e5e19156

const NAV_ITEMS = [
  { href: "/dashboard", icon: "📊", label: "Dashboard" },
  { href: "/questionnaire", icon: "📋", label: "Log Health" },
  { href: "/chat", icon: "💬", label: "AI Chat" },
];

export default function SidebarNav() {
  const pathname = usePathname();
<<<<<<< HEAD
  const router = useRouter();
  const [userName, setUserName] = useState<string | null>(null);

  useEffect(() => {
    const session = getSession();
    setUserName(session?.name ?? null);
  }, []);

  const handleLogout = () => {
    clearSession();
    router.push("/login");
  };
=======
>>>>>>> 32e7e8429f7cd41eff9a8ad873be60f1e5e19156

  return (
    <nav className="sidebar">
      <div className="sidebar-logo">
        <div className="sidebar-logo-icon">🫀</div>
        <div className="sidebar-logo-text">
          Health<span>AI</span>
        </div>
      </div>

      {NAV_ITEMS.map((item) => (
        <Link
          key={item.href}
          href={item.href}
          className={`nav-link ${pathname.startsWith(item.href) ? "active" : ""}`}
        >
          <span className="nav-icon">{item.icon}</span>
          {item.label}
        </Link>
      ))}
<<<<<<< HEAD

      <div style={{ marginTop: "auto", padding: "16px 12px", borderTop: "1px solid var(--border)" }}>
        {userName && (
          <div style={{ fontSize: "0.8rem", color: "var(--text-muted)", marginBottom: 10, paddingLeft: 4 }}>
            👤 {userName}
          </div>
        )}
        <button
          onClick={handleLogout}
          className="nav-link"
          style={{ width: "100%", background: "none", border: "none", cursor: "pointer", color: "var(--text-secondary)", textAlign: "left" }}
        >
          <span className="nav-icon">🚪</span>
          Log out
        </button>
      </div>
=======
>>>>>>> 32e7e8429f7cd41eff9a8ad873be60f1e5e19156
    </nav>
  );
}
