import { screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { http, HttpResponse } from "msw";
import { describe, expect, it, vi } from "vitest";

import { documentsCopy } from "@/content/es";
import { server } from "@/test/msw";
import { renderWithQuery } from "@/test/render";

import { UploadZone } from "./UploadZone";
import { preCheck } from "./validation";

const refresh = vi.fn();
vi.mock("next/navigation", () => ({ useRouter: () => ({ refresh }) }));

const TICKET_URL = `${window.location.origin}/api/backend/api/v1/evaluations/:id/documents/upload-ticket`;
// PDFs go straight to the API (hosting limits function bodies), authorized by the ticket.
const UPLOAD_URL = "http://api.test/api/v1/evaluations/:id/documents";

function ticketHandler() {
  return http.post(TICKET_URL, () => HttpResponse.json({ ticket: "ticket-123", expires_in: 300 }));
}

function pdfFile(name = "politica.pdf", bytes = 2048): File {
  return new File([new Uint8Array(bytes)], name, { type: "application/pdf" });
}

describe("preCheck", () => {
  it("accepts PDFs up to 20 MB and rejects the rest", () => {
    expect(preCheck(pdfFile())).toBeNull();
    expect(preCheck(new File(["x"], "nota.txt", { type: "text/plain" }))).toBe(
      documentsCopy.clientErrors.type,
    );
    expect(preCheck(pdfFile("vacio.pdf", 0))).toBe(documentsCopy.clientErrors.empty);
    const huge = pdfFile();
    Object.defineProperty(huge, "size", { value: 21 * 1024 * 1024 });
    expect(preCheck(huge)).toBe(documentsCopy.clientErrors.size);
  });
});

describe("UploadZone", () => {
  it("uploads directly to the API with a ticket and confirms the validation results", async () => {
    let contentType: string | null = null;
    let ticket: string | null = null;
    server.use(
      ticketHandler(),
      http.post(UPLOAD_URL, ({ request }) => {
        ticket = request.headers.get("x-upload-ticket");
        // jsdom's FormData cannot be re-parsed by Node's fetch here; the header proves multipart.
        contentType = request.headers.get("content-type");
        return HttpResponse.json(
          {
            id: "6f9619ff-8b86-d011-b42d-00cf4fc964ff",
            original_name: "politica.pdf",
            size_bytes: 2048,
            page_count: 5,
            has_text: true,
            status: "STORED",
            created_at: "2026-10-07T12:00:00Z",
          },
          { status: 201 },
        );
      }),
    );
    renderWithQuery(<UploadZone evaluationId="e1" />);

    await userEvent.upload(screen.getByLabelText(documentsCopy.choose), pdfFile());

    expect(await screen.findByText(documentsCopy.validPdf)).toBeInTheDocument();
    expect(screen.getByText("5 páginas")).toBeInTheDocument();
    expect(screen.getByText(documentsCopy.textDetected)).toBeInTheDocument();
    expect(contentType).toMatch(/^multipart\/form-data; boundary=/);
    expect(ticket).toBe("ticket-123");
    expect(refresh).toHaveBeenCalled();
  });

  it("shows the API's Spanish message when the server rejects the file", async () => {
    server.use(
      ticketHandler(),
      http.post(UPLOAD_URL, () =>
        HttpResponse.json(
          {
            code: "INVALID_FILE",
            message: "El PDF no tiene texto seleccionable; parece un documento escaneado.",
            request_id: "r1",
          },
          { status: 422 },
        ),
      ),
    );
    renderWithQuery(<UploadZone evaluationId="e1" />);
    await userEvent.upload(screen.getByLabelText(documentsCopy.choose), pdfFile("escaneado.pdf"));
    expect(await screen.findByRole("alert")).toHaveTextContent("parece un documento escaneado");
  });

  it("explains when no upload ticket can be obtained", async () => {
    server.use(
      http.post(TICKET_URL, () =>
        HttpResponse.json(
          {
            code: "FORBIDDEN",
            message: "No tienes permiso para realizar esta acción.",
            request_id: "r",
          },
          { status: 403 },
        ),
      ),
    );
    renderWithQuery(<UploadZone evaluationId="e1" />);
    await userEvent.upload(screen.getByLabelText(documentsCopy.choose), pdfFile());
    expect(await screen.findByRole("alert")).toHaveTextContent("No tienes permiso");
  });

  it("never calls the API for files that fail the client pre-check", async () => {
    renderWithQuery(<UploadZone evaluationId="e1" />);
    await userEvent.upload(
      screen.getByLabelText(documentsCopy.choose),
      new File(["x"], "nota.txt", { type: "text/plain" }),
      { applyAccept: false },
    );
    expect(await screen.findByRole("alert")).toHaveTextContent(documentsCopy.clientErrors.type);
  });
});
