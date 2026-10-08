import { describe, expect, it } from "vitest";

import { navigationFor } from "./navigation";

describe("navigationFor", () => {
  it("shows administration only to administrators", () => {
    const adminLinks = navigationFor("ADMIN").map((item) => item.href);
    expect(adminLinks).toContain("/app/admin/usuarios");
    for (const role of ["SME", "REVIEWER", "MENTOR"] as const) {
      expect(navigationFor(role).some((item) => item.href.startsWith("/app/admin"))).toBe(false);
    }
  });

  it("gives the mentor only the metrics screen", () => {
    expect(navigationFor("MENTOR").map((item) => item.href)).toEqual(["/app/metricas"]);
  });

  it("lets SMEs create evaluations but not review them", () => {
    const links = navigationFor("SME").map((item) => item.href);
    expect(links).toContain("/app/evaluaciones/nueva");
    expect(links).not.toContain("/app/revision");
  });
});
