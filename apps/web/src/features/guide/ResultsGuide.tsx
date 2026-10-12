import { FindingStatusBadge } from "@/components/shared/FindingStatusBadge";
import { guide } from "@/content/es";

const copy = guide.results;

/** Explains statuses, levels and plan phases in plain language. */
export function ResultsGuide() {
  return (
    <div className="flex flex-col gap-5 text-sm">
      <p className="text-muted-foreground">{copy.intro}</p>
      <ul className="flex flex-col gap-3">
        {copy.statuses.map((item) => (
          <li
            key={item.status}
            className="flex flex-col gap-1.5 sm:flex-row sm:items-start sm:gap-4"
          >
            <span className="sm:w-48 sm:shrink-0">
              <FindingStatusBadge status={item.status} />
            </span>
            <span className="text-foreground leading-relaxed">{item.meaning}</span>
          </li>
        ))}
      </ul>
      <p className="text-foreground leading-relaxed">{copy.coverage}</p>
      <div className="flex flex-col gap-1.5">
        <p className="text-foreground font-semibold">{copy.levelsTitle}</p>
        <ul className="text-muted-foreground flex list-disc flex-col gap-1 pl-5">
          {copy.levels.map((level) => (
            <li key={level}>{level}</li>
          ))}
        </ul>
      </div>
      <div className="flex flex-col gap-1.5">
        <p className="text-foreground font-semibold">{copy.planTitle}</p>
        <p className="text-muted-foreground leading-relaxed">{copy.plan}</p>
      </div>
    </div>
  );
}
