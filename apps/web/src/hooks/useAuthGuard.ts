"use client";

import { useEffect, useState } from "react";
import { useRouter, usePathname } from "next/navigation";
import { getSession } from "@/lib/auth";

const PUBLIC_ROUTES = ["/login", "/signup"];

export function useAuthGuard() {
  const router = useRouter();
  const pathname = usePathname();
  const [isAllowed, setIsAllowed] = useState(false);
  const [isChecking, setIsChecking] = useState(true);

  useEffect(() => {
    const session = getSession();
    const isPublic = PUBLIC_ROUTES.some((r) => pathname.startsWith(r));

    if (!session && !isPublic) {
      setIsAllowed(false);
      setIsChecking(false);
      router.replace("/login");
      return;
    }

    if (session && !session.onboarding_complete && pathname !== "/onboarding") {
      setIsAllowed(false);
      setIsChecking(false);
      router.replace("/onboarding");
      return;
    }

    if (session && isPublic) {
      setIsAllowed(false);
      setIsChecking(false);
      router.replace(session.onboarding_complete ? "/dashboard" : "/onboarding");
      return;
    }

    setIsAllowed(true);
    setIsChecking(false);
  }, [pathname, router]);

  return { isAllowed, isChecking };
}
