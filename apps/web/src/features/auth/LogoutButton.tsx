import { Button } from "@/components/ui/button";
import { auth } from "@/content/es";

import { signOutAction } from "./actions";

export function LogoutButton() {
  return (
    <form action={signOutAction}>
      <Button type="submit" variant="outline" size="sm">
        {auth.logout}
      </Button>
    </form>
  );
}
