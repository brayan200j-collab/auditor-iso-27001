"use client";

import { Printer } from "lucide-react";

import { Button } from "@/components/ui/button";

/** The browser's print dialog lets the user save the guide as a PDF manual. */
export function PrintButton({ label }: { label: string }) {
  return (
    <Button type="button" variant="outline" className="print:hidden" onClick={() => window.print()}>
      <Printer className="size-4" aria-hidden="true" />
      {label}
    </Button>
  );
}
