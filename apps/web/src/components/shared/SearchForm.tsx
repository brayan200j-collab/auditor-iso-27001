import type { ReactNode } from "react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

type SearchFormProps = {
  label: string;
  submitLabel: string;
  defaultValue?: string;
  /** Extra controls (e.g. a filter select) submitted together with the search box. */
  children?: ReactNode;
};

/** Plain GET form: filters live in the URL, so they survive reloads and can be shared. */
export function SearchForm({ label, submitLabel, defaultValue, children }: SearchFormProps) {
  return (
    <form method="get" role="search" className="flex flex-wrap items-end gap-3">
      <div className="flex min-w-60 flex-col gap-1.5">
        <label htmlFor="search" className="text-foreground text-sm font-medium">
          {label}
        </label>
        <Input id="search" name="search" defaultValue={defaultValue} maxLength={100} />
      </div>
      {children}
      <Button type="submit" variant="outline">
        {submitLabel}
      </Button>
    </form>
  );
}
