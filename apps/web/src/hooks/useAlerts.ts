"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { getAlerts, markAlertRead, deleteAlert, deleteAlerts } from "@/lib/apiClient";
import type { Alert } from "@/types/stats";

const POLL_INTERVAL_MS = 30_000;

export function useAlerts() {
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [isOpen, setIsOpen] = useState(false);
  const prevUnreadRef = useRef(0);

  const fetchAlerts = useCallback(async () => {
    try {
      const data = await getAlerts();
      setAlerts(data);
      const newUnread = data.filter((a) => !a.is_read).length;
      // Auto-open panel when new unread alerts arrive
      if (newUnread > prevUnreadRef.current && prevUnreadRef.current >= 0) {
        setIsOpen(true);
      }
      prevUnreadRef.current = newUnread;
    } catch {
      // Silently ignore — backend may not be running
    }
  }, []);

  // Initial fetch + polling
  useEffect(() => {
    fetchAlerts();
    const interval = setInterval(fetchAlerts, POLL_INTERVAL_MS);
    return () => clearInterval(interval);
  }, [fetchAlerts]);

  // Refetch on page focus
  useEffect(() => {
    const onFocus = () => fetchAlerts();
    window.addEventListener("focus", onFocus);
    return () => window.removeEventListener("focus", onFocus);
  }, [fetchAlerts]);

  const openPanel = () => setIsOpen(true);
  const closePanel = () => setIsOpen(false);

  const dismissAlert = async (id: number) => {
    await markAlertRead(id);
    setAlerts((prev) =>
      prev.map((a) => (a.id === id ? { ...a, is_read: true } : a))
    );
  };

  const handleDeleteAlert = async (id: number) => {
    await deleteAlert(id);
    setAlerts((prev) => prev.filter((a) => a.id !== id));
  };

  const handleDeleteDay = async (dateKey: string) => {
    // dateKey is YYYY-MM-DD in local time — delete alerts for that calendar day (UTC)
    const afterDate = new Date(dateKey + "T00:00:00.000Z").toISOString();
    const beforeDate = new Date(
      new Date(dateKey + "T00:00:00.000Z").getTime() + 86_400_000
    ).toISOString();
    await deleteAlerts({ afterDate, beforeDate });
    setAlerts((prev) =>
      prev.filter((a) => {
        const d = a.created_at.slice(0, 10);
        return d !== dateKey;
      })
    );
  };

  const handleDeleteAll = async () => {
    await deleteAlerts({});
    setAlerts([]);
  };

  const unreadCount = alerts.filter((a) => !a.is_read).length;

  return {
    alerts,
    unreadCount,
    isOpen,
    openPanel,
    closePanel,
    dismissAlert,
    deleteAlert: handleDeleteAlert,
    deleteDay: handleDeleteDay,
    deleteAll: handleDeleteAll,
    refetch: fetchAlerts,
  };
}
