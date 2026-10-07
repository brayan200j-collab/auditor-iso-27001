"use client";

import { CheckCircle2, FileUp } from "lucide-react";
import { useRouter } from "next/navigation";
import { useEffect, useEffectEvent, useId, useRef, useState } from "react";

import { Alert } from "@/components/ui/alert";
import { buttonVariants } from "@/components/ui/button";
import { documentsCopy } from "@/content/es";
import { cn } from "@/lib/utils";

import { useDocumentUpload, type UploadedDocument } from "./useDocumentUpload";
import { preCheck } from "./validation";

export function UploadZone({ evaluationId }: { evaluationId: string }) {
  const router = useRouter();
  const inputId = useId();
  const inputRef = useRef<HTMLInputElement>(null);
  const [dragging, setDragging] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [uploaded, setUploaded] = useState<UploadedDocument | null>(null);
  const upload = useDocumentUpload(evaluationId);
  const zoneRef = useRef<HTMLDivElement>(null);

  const send = (file: File | undefined) => {
    if (!file) return;
    setError(null);
    setUploaded(null);
    const problem = preCheck(file);
    if (problem) {
      setError(problem);
      return;
    }
    upload.mutate(file, {
      onSuccess: (document) => {
        setUploaded(document);
        router.refresh();
      },
      onError: (failure) => setError(failure.message),
      onSettled: () => {
        if (inputRef.current) inputRef.current.value = "";
      },
    });
  };

  const onDroppedFile = useEffectEvent((file: File | undefined) => send(file));

  // Drag and drop is a pointer-only enhancement; the "Seleccionar PDF" button is the accessible
  // equivalent for keyboard and screen-reader users.
  useEffect(() => {
    const zone = zoneRef.current;
    if (!zone) return;
    const over = (event: DragEvent) => {
      event.preventDefault();
      setDragging(true);
    };
    const leave = () => setDragging(false);
    const drop = (event: DragEvent) => {
      event.preventDefault();
      setDragging(false);
      onDroppedFile(event.dataTransfer?.files[0]);
    };
    zone.addEventListener("dragover", over);
    zone.addEventListener("dragleave", leave);
    zone.addEventListener("drop", drop);
    return () => {
      zone.removeEventListener("dragover", over);
      zone.removeEventListener("dragleave", leave);
      zone.removeEventListener("drop", drop);
    };
  }, []);

  return (
    <div className="flex flex-col gap-3">
      <div
        ref={zoneRef}
        className={cn(
          "border-border bg-surface-muted flex flex-col items-center gap-3 rounded-md border-2 border-dashed p-8 text-center",
          dragging && "border-primary bg-info-soft",
        )}
      >
        <FileUp className="text-primary size-8" aria-hidden="true" />
        <p className="text-foreground font-medium">{documentsCopy.dropTitle}</p>
        <p className="text-muted-foreground text-sm">{documentsCopy.dropHint}</p>
        <input
          ref={inputRef}
          id={inputId}
          type="file"
          accept="application/pdf,.pdf"
          className="peer sr-only"
          onChange={(event) => send(event.target.files?.[0])}
          disabled={upload.isPending}
        />
        <label
          htmlFor={inputId}
          className={cn(
            buttonVariants({ variant: "outline" }),
            "peer-focus-visible:outline-ring cursor-pointer peer-focus-visible:outline-3 peer-focus-visible:outline-offset-2",
            upload.isPending && "pointer-events-none opacity-60",
          )}
        >
          {upload.isPending ? documentsCopy.uploading : documentsCopy.choose}
        </label>
      </div>
      <div aria-live="polite">
        {error ? <Alert tone="danger">{error}</Alert> : null}
        {uploaded ? (
          <Alert tone="success">
            <p className="font-medium">{uploaded.original_name}</p>
            <ul className="mt-1 flex flex-wrap gap-x-4 gap-y-1">
              {[
                documentsCopy.validPdf,
                documentsCopy.pages(uploaded.page_count),
                documentsCopy.textDetected,
              ].map((item) => (
                <li key={item} className="flex items-center gap-1">
                  <CheckCircle2 className="size-4" aria-hidden="true" />
                  {item}
                </li>
              ))}
            </ul>
          </Alert>
        ) : null}
      </div>
    </div>
  );
}
