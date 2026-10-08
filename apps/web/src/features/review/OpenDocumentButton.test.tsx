import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { http, HttpResponse } from "msw";
import { afterEach, describe, expect, it, vi } from "vitest";

import { reviewCopy } from "@/content/es";
import { server } from "@/test/msw";

import { OpenDocumentButton } from "./OpenDocumentButton";

const LINK_URL = `${window.location.origin}/api/backend/api/v1/evaluations/:evaluation/documents/:document/link`;

function fakeTab() {
  return { opener: {} as unknown, location: { href: "about:blank" }, close: vi.fn() };
}

describe("OpenDocumentButton", () => {
  afterEach(() => vi.restoreAllMocks());

  it("opens the original PDF at the cited page in a new tab", async () => {
    const tab = fakeTab();
    vi.spyOn(window, "open").mockReturnValue(tab as unknown as Window);
    server.use(
      http.get(LINK_URL, () =>
        HttpResponse.json({ url: "https://storage.test/doc.pdf?token=t", expires_in: 120 }),
      ),
    );
    render(
      <OpenDocumentButton
        evaluationId="e1"
        documentId="d1"
        page={3}
        label={reviewCopy.documents.atPage(3)}
      />,
    );
    await userEvent.click(screen.getByRole("button", { name: reviewCopy.documents.atPage(3) }));

    await waitFor(() =>
      expect(tab.location.href).toBe("https://storage.test/doc.pdf?token=t#page=3"),
    );
    expect(tab.opener).toBeNull();
  });

  it("closes the tab and explains why when the PDF is no longer available", async () => {
    const tab = fakeTab();
    vi.spyOn(window, "open").mockReturnValue(tab as unknown as Window);
    server.use(
      http.get(LINK_URL, () =>
        HttpResponse.json(
          {
            code: "CONFLICT",
            message:
              "El PDF original ya no está disponible: se eliminó según la política de retención.",
            request_id: "r",
          },
          { status: 409 },
        ),
      ),
    );
    render(
      <OpenDocumentButton evaluationId="e1" documentId="d1" label={reviewCopy.documents.open} />,
    );
    await userEvent.click(screen.getByRole("button", { name: reviewCopy.documents.open }));

    expect(await screen.findByRole("alert")).toHaveTextContent("política de retención");
    expect(tab.close).toHaveBeenCalled();
  });
});
