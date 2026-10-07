import { AppShell } from "@/components/shared/AppShell";
import { LogoutButton } from "@/features/auth";
import { navigationFor } from "@/lib/navigation";
import { requireProfile } from "@/lib/profile";

export default async function PrivateLayout({ children }: LayoutProps<"/app">) {
  const profile = await requireProfile();
  return (
    <AppShell
      userName={profile.full_name}
      role={profile.role}
      companyName={profile.company_name}
      items={navigationFor(profile.role)}
      actions={<LogoutButton />}
    >
      {children}
    </AppShell>
  );
}
