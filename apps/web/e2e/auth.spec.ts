import { expect, test } from "@playwright/test";

import { credentials, login, logout } from "./support";

test("protected routes redirect anonymous visitors to the login page", async ({ page }) => {
  await page.goto("/app");
  await expect(page).toHaveURL(/\/login$/);
  await expect(page.getByRole("heading", { name: "Iniciar sesión" })).toBeVisible();
});

test("wrong credentials show a generic error", async ({ page }) => {
  await page.goto("/login");
  await page.getByLabel("Correo electrónico").fill(credentials("SME").email);
  await page.getByLabel("Contraseña").fill("ContraseñaIncorrecta123");
  await page.getByRole("button", { name: "Ingresar" }).click();
  await expect(page.getByText("Correo o contraseña incorrectos.")).toBeVisible();
});

test("an SME signs in, sees its company and signs out", async ({ page, context }) => {
  await login(page, "SME");
  await expect(page.getByText("PYME", { exact: false }).first()).toBeVisible();
  await expect(page.getByText("Empresa de prueba A S.A.S.")).toBeVisible();
  await expect(
    page
      .getByRole("navigation", { name: "Navegación principal" })
      .getByRole("link", { name: "Nueva evaluación" }),
  ).toBeVisible();

  const cookies = await context.cookies();
  const authCookies = cookies.filter((cookie) => cookie.name.startsWith("sb-"));
  expect(authCookies.length).toBeGreaterThan(0);
  expect(authCookies.every((cookie) => cookie.httpOnly)).toBe(true);

  await logout(page);
  await page.goto("/app");
  await expect(page).toHaveURL(/\/login$/);
});

test("the mentor only sees the metrics entry", async ({ page }) => {
  await login(page, "MENTOR");
  const navigation = page.getByRole("navigation", { name: "Navegación principal" });
  await expect(navigation.getByRole("link")).toHaveCount(1);
  await expect(navigation.getByRole("link", { name: "Métricas" })).toBeVisible();
});

test("account recovery never reveals whether an email exists", async ({ page }) => {
  for (const email of [credentials("SME").email, "nadie@example.test"]) {
    await page.goto("/recuperar");
    await page.getByLabel("Correo electrónico").fill(email);
    await page.getByRole("button", { name: "Enviar instrucciones" }).click();
    await expect(page.getByRole("status")).toContainText("Si el correo está registrado");
  }
});
