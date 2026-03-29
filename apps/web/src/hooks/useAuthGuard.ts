"use client";

import { useEffect } from "react";
import { useRouter, usePathname } from "next/navigation";
import { getSession } from "@/lib/auth";

const PUBLIC_ROUTES = ["/login", "/signup"];

export function useAuthGuard() {
  const router = useRouter();
  const pathname = usePathname();

  useEffect(() => {
    const session = getSession();
    const isPublic = PUBLIC_ROUTES.some((r) => pathname.startsWith(r));

    if (!session && !isPublic) {
      router.replace("/login");
      return;
    }

    if (session && !session.onboarding_complete && pathname !== "/onboarding") {
      router.replace("/onboarding");
      return;
    }

    if (session && isPublic) {
      router.replace("/dashboard");
    }
  }, [pathname, router]);
}
