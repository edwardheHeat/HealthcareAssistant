import { NextRequest, NextResponse } from "next/server";

const PUBLIC_ROUTES = ["/login", "/signup"];
const PROTECTED_ROUTES = ["/dashboard", "/questionnaire", "/chat", "/settings"];

export function proxy(request: NextRequest) {
  const { pathname } = request.nextUrl;
  const userId = request.cookies.get("ha_user_id")?.value;
  const onboardingComplete =
    request.cookies.get("ha_onboarding_complete")?.value === "true";

  const isPublic = PUBLIC_ROUTES.some((route) => pathname.startsWith(route));
  const isProtected = PROTECTED_ROUTES.some((route) =>
    pathname.startsWith(route),
  );
  const isRoot = pathname === "/";
  const isOnboarding = pathname.startsWith("/onboarding");

  if (!userId) {
    if (isProtected || isRoot || isOnboarding) {
      return NextResponse.redirect(new URL("/login", request.url));
    }
    return NextResponse.next();
  }

  if (isPublic || isRoot) {
    const target = onboardingComplete ? "/dashboard" : "/onboarding";
    return NextResponse.redirect(new URL(target, request.url));
  }

  if (!onboardingComplete && (isProtected || !isOnboarding)) {
    return NextResponse.redirect(new URL("/onboarding", request.url));
  }

  if (onboardingComplete && isOnboarding) {
    return NextResponse.redirect(new URL("/dashboard", request.url));
  }

  return NextResponse.next();
}

export const config = {
  matcher: [
    "/",
    "/login",
    "/signup",
    "/onboarding",
    "/dashboard/:path*",
    "/questionnaire/:path*",
    "/chat/:path*",
    "/settings/:path*",
  ],
};
