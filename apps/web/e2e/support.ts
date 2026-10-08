import { expect, type Page } from "@playwright/test";

export type SeedRole = "ADMIN" | "REVIEWER" | "SME" | "SME_B" | "MENTOR";

export function credentials(role: SeedRole): { email: string; password: string } {
  const email = process.env[`SEED_${role}_EMAIL`];
  const password = process.env[`SEED_${role}_PASSWORD`];
  if (!email || !password) {
    throw new Error(`SEED_${role}_EMAIL/PASSWORD missing: run "make env" and "make seed".`);
  }
  return { email, password };
}

export async function login(page: Page, role: SeedRole, landing = /\/app$/): Promise<void> {
  const { email, password } = credentials(role);
  await page.goto("/login");
  await page.getByLabel("Correo electrónico").fill(email);
  await page.getByLabel("Contraseña").fill(password);
  await page.getByRole("button", { name: "Ingresar" }).click();
  await expect(page).toHaveURL(landing);
}

export async function logout(page: Page): Promise<void> {
  await page.getByRole("button", { name: "Cerrar sesión" }).click();
  await expect(page).toHaveURL(/\/login$/);
}
