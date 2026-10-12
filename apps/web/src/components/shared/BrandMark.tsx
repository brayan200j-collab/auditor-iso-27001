import Link from "next/link";
import { useId } from "react";

import { brand } from "@/content/es";
import { cn } from "@/lib/utils";

/**
 * Logo symbol: a rounded shield (protection) holding a check (validated by a person), with a
 * small spectrum spark (the AI that reads the documents). See docs/BRAND.md.
 */
export function LogoSymbol({
  className,
  inverted = false,
}: {
  className?: string;
  inverted?: boolean;
}) {
  const id = useId().replace(/:/g, "");
  return (
    <svg viewBox="0 0 40 40" className={cn("size-10 shrink-0", className)} aria-hidden="true">
      <defs>
        <linearGradient
          id={`shield-${id}`}
          x1="6"
          y1="3"
          x2="34"
          y2="38"
          gradientUnits="userSpaceOnUse"
        >
          <stop offset="0" stopColor={inverted ? "#ffffff" : "#6161ff"} />
          <stop offset="1" stopColor={inverted ? "#e7ecff" : "#4a3ad8"} />
        </linearGradient>
        <linearGradient
          id={`spark-${id}`}
          x1="27"
          y1="3"
          x2="37"
          y2="13"
          gradientUnits="userSpaceOnUse"
        >
          <stop offset="0" stopColor="#33dbdb" />
          <stop offset="0.5" stopColor="#ffd633" />
          <stop offset="1" stopColor="#fc527d" />
        </linearGradient>
      </defs>
      <path
        d="M20 3.5c4.9 2.7 9.6 3.9 13.6 4.1.9 0 1.6.8 1.6 1.7v8.6c0 9.3-5.9 16.3-14.6 19.3a2 2 0 0 1-1.2 0C10.7 34.2 4.8 27.2 4.8 17.9V9.3c0-.9.7-1.7 1.6-1.7 4-.2 8.7-1.4 13.6-4.1Z"
        fill={`url(#shield-${id})`}
      />
      <path
        d="m13.2 20.4 4.6 4.6 9.2-10"
        fill="none"
        stroke={inverted ? "#4a3ad8" : "#ffffff"}
        strokeWidth="3.4"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      <circle
        cx="32"
        cy="8"
        r="4.2"
        fill={`url(#spark-${id})`}
        stroke={inverted ? "#4a3ad8" : "#ffffff"}
        strokeWidth="1.6"
      />
    </svg>
  );
}

export function Wordmark({ inverted = false }: { inverted?: boolean }) {
  return (
    <span
      className={cn(
        "text-lg leading-none tracking-tight",
        inverted ? "text-white" : "text-foreground",
      )}
    >
      <span className="font-semibold">Auditor</span>{" "}
      <span className={cn("font-light", inverted ? "text-white" : "text-primary")}>Virtual</span>
    </span>
  );
}

export function BrandMark({
  href = "/",
  showTagline = false,
  inverted = false,
}: {
  href?: string;
  showTagline?: boolean;
  inverted?: boolean;
}) {
  return (
    <Link href={href} className="flex items-center gap-2.5 rounded-md" aria-label={brand.name}>
      <LogoSymbol inverted={inverted} />
      <span className="flex flex-col gap-1">
        <Wordmark inverted={inverted} />
        {showTagline ? (
          <span className={cn("text-xs", inverted ? "text-white/85" : "text-muted-foreground")}>
            {brand.tagline}
          </span>
        ) : null}
      </span>
    </Link>
  );
}
