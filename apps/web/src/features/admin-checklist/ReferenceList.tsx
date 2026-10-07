import { Badge } from "@/components/ui/badge";
import { checklistCopy } from "@/content/es";

type References = {
  iso_reference: string | null;
  cis_reference: string | null;
  nist_reference: string | null;
  reference_status: "draft" | "confirmed";
};

/** Framework references are identifiers only; unconfirmed ones are always labelled as such. */
export function ReferenceList({ item }: { item: References }) {
  const entries = [
    ["ISO/IEC 27001:2022", item.iso_reference],
    ["CIS Controls v8.1", item.cis_reference],
    ["NIST CSF 2.0", item.nist_reference],
  ].filter((entry): entry is [string, string] => Boolean(entry[1]));
  return (
    <div className="flex flex-col gap-1 text-xs">
      {entries.map(([framework, reference]) => (
        <span key={framework}>
          <span className="text-muted-foreground">{framework}:</span> {reference}
        </span>
      ))}
      <Badge
        tone={item.reference_status === "draft" ? "warning" : "success"}
        className="self-start"
      >
        {item.reference_status === "draft"
          ? checklistCopy.pendingReference
          : checklistCopy.confirmedReference}
      </Badge>
    </div>
  );
}
