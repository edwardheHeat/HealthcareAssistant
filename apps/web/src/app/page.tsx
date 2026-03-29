"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";

import { getSession } from "@/lib/auth";

export default function Home() {
  const router = useRouter();

  useEffect(() => {
    const session = getSession();

    if (!session) {
      router.replace("/login");
      return;
    }

    if (!session.onboarding_complete) {
      router.replace("/onboarding");
      return;
    }

    router.replace("/dashboard");
  }, [router]);

  return (
    <div style={{ display: "flex", justifyContent: "center", paddingTop: 80 }}>
      <div className="spinner" />
    </div>
  );
}
