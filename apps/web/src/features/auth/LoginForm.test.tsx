import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { auth } from "@/content/es";

import { LoginForm } from "./LoginForm";

const signInAction = vi.fn();

vi.mock("./actions", () => ({
  signInAction: (input: unknown) => signInAction(input),
}));

describe("LoginForm", () => {
  beforeEach(() => signInAction.mockReset());

  it("validates input in Spanish before calling the server", async () => {
    render(<LoginForm />);
    await userEvent.click(screen.getByRole("button", { name: auth.login.submit }));

    expect(await screen.findAllByText(auth.validation.required)).toHaveLength(2);
    expect(signInAction).not.toHaveBeenCalled();
    expect(screen.getByLabelText(auth.login.email)).toHaveAttribute("aria-invalid", "true");
  });

  it("submits credentials and shows a generic error", async () => {
    signInAction.mockResolvedValue({ ok: false, message: auth.login.invalidCredentials });
    render(<LoginForm />);

    await userEvent.type(screen.getByLabelText(auth.login.email), "persona@example.test");
    await userEvent.type(screen.getByLabelText(auth.login.password), "una-clave");
    await userEvent.click(screen.getByRole("button", { name: auth.login.submit }));

    await waitFor(() =>
      expect(signInAction).toHaveBeenCalledWith({
        email: "persona@example.test",
        password: "una-clave",
      }),
    );
    expect(await screen.findByRole("alert")).toHaveTextContent(auth.login.invalidCredentials);
  });

  it("never shows demo credentials", () => {
    const { container } = render(<LoginForm />);
    const text = container.textContent ?? "";
    expect(text).not.toMatch(/demo|contraseña_demo|correo_demo/i);
    expect(screen.getByLabelText(auth.login.email)).toHaveValue("");
    expect(screen.getByLabelText(auth.login.password)).toHaveValue("");
  });
});
