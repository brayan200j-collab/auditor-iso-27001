import { PublicShell } from "@/components/shared/PublicShell";
import {
  Benefits,
  Hero,
  HowItWorks,
  LimitsAndCta,
  Results,
  Trust,
  WhatItIs,
} from "@/features/landing";

export default function HomePage() {
  return (
    <PublicShell>
      <Hero />
      <WhatItIs />
      <HowItWorks />
      <Benefits />
      <Results />
      <Trust />
      <LimitsAndCta />
    </PublicShell>
  );
}
