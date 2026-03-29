import { cookies } from "next/headers";
import { redirect } from "next/navigation";

export default async function Home() {
  const cookieStore = await cookies();
  const userId = cookieStore.get("ha_user_id")?.value;
  const onboardingComplete =
    cookieStore.get("ha_onboarding_complete")?.value === "true";

  if (!userId) {
    redirect("/login");
  }

  if (!onboardingComplete) {
    redirect("/onboarding");
  }

  redirect("/dashboard");
}
