import { Button } from "@/components/ui/button";
import { Select } from "@/components/ui/input";
import { evaluations, evaluationStatusLabels, filterLabels } from "@/content/es";
import { EVALUATION_STATUSES } from "@/lib/params";

export function StatusFilter({ current }: { current?: string }) {
  return (
    <form method="get" className="flex flex-wrap items-end gap-3">
      <div className="flex flex-col gap-1.5">
        <label htmlFor="status-filter" className="text-foreground text-sm font-medium">
          {evaluations.statusFilter}
        </label>
        <Select id="status-filter" name="status" defaultValue={current ?? ""} className="w-56">
          <option value="">{filterLabels.ALL}</option>
          {EVALUATION_STATUSES.map((status) => (
            <option key={status} value={status}>
              {evaluationStatusLabels[status]}
            </option>
          ))}
        </Select>
      </div>
      <Button type="submit" variant="outline">
        {evaluations.filter}
      </Button>
    </form>
  );
}
