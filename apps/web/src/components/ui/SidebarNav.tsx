"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useState } from "react";
import { useAlerts } from "@/hooks/useAlerts";
import NotificationPanel from "@/components/notifications/NotificationPanel";

const NAV_ITEMS = [
  { href: "/dashboard", icon: "📊", label: "Dashboard" },
  { href: "/questionnaire", icon: "📋", label: "Log Health" },
  { href: "/chat", icon: "💬", label: "AI Chat" },
];

export default function SidebarNav() {
  const pathname = usePathname();
  const {
    alerts,
    unreadCount,
    isOpen,
    openPanel,
    closePanel,
    dismissAlert,
    deleteAlert,
    deleteDay,
    deleteAll,
  } = useAlerts();

  return (
    <>
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

        {/* Spacer */}
        <div style={{ flex: 1 }} />

        {/* Notification inbox */}
        <button
          onClick={openPanel}
          className="inbox-btn"
          title="Inbox / Alerts"
        >
          <svg
            xmlns="http://www.w3.org/2000/svg"
            width="22"
            height="22"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
          >
            <polyline points="22 12 16 12 14 15 10 15 8 12 2 12"></polyline>
            <path d="M5.45 5.11L2 12v6a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2v-6l-3.45-6.89A2 2 0 0 0 16.76 4H7.24a2 2 0 0 0-1.79 1.11z"></path>
          </svg>
          {unreadCount > 0 && (
            <span className="inbox-badge">
              {unreadCount > 99 ? "99+" : unreadCount}
            </span>
          )}
        </button>
      </nav>

      {isOpen && (
        <NotificationPanel
          alerts={alerts}
          onClose={closePanel}
          onDelete={deleteAlert}
          onDismiss={dismissAlert}
          onDeleteDay={deleteDay}
          onDeleteAll={deleteAll}
        />
      )}
    </>
  );
}
