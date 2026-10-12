export function SectionHeading({
  id,
  eyebrow,
  title,
  description,
  center = false,
}: {
  id: string;
  eyebrow: string;
  title: string;
  description?: string;
  center?: boolean;
}) {
  return (
    <div
      className={
        center
          ? "mx-auto flex max-w-2xl flex-col gap-3 text-center"
          : "flex max-w-2xl flex-col gap-3"
      }
    >
      <p className="text-primary text-sm font-semibold tracking-[0.12em] uppercase">{eyebrow}</p>
      <h2 id={id} className="text-foreground text-3xl font-light tracking-[-0.02em] sm:text-4xl">
        {title}
      </h2>
      {description ? (
        <p className="text-muted-foreground text-base leading-relaxed">{description}</p>
      ) : null}
    </div>
  );
}
