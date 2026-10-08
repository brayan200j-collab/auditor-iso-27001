import { confidence as copy, reviewCopy } from "@/content/es";

const formatter = new Intl.NumberFormat("es-CO", {
  minimumFractionDigits: 2,
  maximumFractionDigits: 2,
});

/** The model's confidence, always labelled and explained; never shown as a percentage. */
export function ConfidenceValue({ value }: { value: number | null }) {
  return (
    <div className="flex flex-col gap-1 text-sm">
      <span className="text-muted-foreground">{copy.label}</span>
      <span className="text-foreground font-semibold">
        {value === null ? reviewCopy.noModelCall : formatter.format(value)}
      </span>
      <details className="text-muted-foreground text-xs">
        <summary className="cursor-pointer">{copy.whatIs}</summary>
        <p className="mt-1">{value === null ? reviewCopy.noModelCallHelp : copy.help}</p>
      </details>
    </div>
  );
}

export function formatConfidence(value: number | null): string {
  return value === null ? "—" : formatter.format(value);
}
