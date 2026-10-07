import { brand, legal } from "@/content/es";

export default function HomePage() {
  return (
    <main id="contenido" className="mx-auto flex w-full max-w-4xl flex-1 flex-col gap-6 px-6 py-16">
      <p className="text-primary text-sm font-semibold tracking-wide uppercase">{brand.name}</p>
      <h1 className="text-foreground text-3xl font-semibold">{brand.headline}</h1>
      <p className="text-muted-foreground text-lg">{brand.definition}</p>
      <p className="text-muted-foreground text-sm">{legal.scopeDisclaimer}</p>
    </main>
  );
}
