# Auditor Virtual — brand essence

## Purpose
Help small and medium businesses in Valle del Cauca take a **clear first look** at their
information-security gaps from the documents they already have, with AI doing the first reading
and a person validating every result.

- **Tagline (fixed):** "Autoevaluación inicial de seguridad de la información."
- **Main message (fixed):** "Obtén una primera lectura clara de tus brechas de seguridad a partir
  de tus documentos."
- **Promise:** clarity you can trust — every conclusion shows where it came from (document and
  page) and was reviewed by a person.

## Personality
| Trait | What it means | What it is not |
|---|---|---|
| Clear | Plain Spanish, short sentences, counts instead of jargon | Technical, cryptic |
| Trustworthy | Honest limits, traceable evidence, human review | Overpromising, "certified" |
| Close | Speaks to SME owners and their teams as a helpful colleague | Distant, bureaucratic |
| Calm | Soft surfaces, generous whitespace, no alarmist colours | "Hacker" aesthetics, fear-based messages |

## Voice and tone
- Use: "autoevaluación inicial", "cobertura documental preliminar", "resultado preliminar sujeto a
  revisión", "brechas", "plan inicial de mejora".
- Never: "porcentaje de cumplimiento", "certificado", "Cumple/No cumple ISO", "Compliance",
  "auditoría ISO automática", "la IA es gratuita", "nunca son almacenados". Coverage is always
  expressed as counts ("14 de 30 criterios con evidencia documental").
- Always show the scope disclaimer on results and the report, and the approved privacy wording
  about the inference provider (CLAUDE.md section 1).
- Errors explain what happened and what to do next; they never blame the user.

## Logo
- **Symbol:** a rounded shield (protection) holding a check mark (validated by a person) and a
  small spectrum spark (the AI that reads the documents). Source: `apps/web/src/components/shared/BrandMark.tsx`
  and the favicon `apps/web/src/app/icon.svg`.
- **Wordmark:** "Auditor" in Poppins SemiBold + "Virtual" in Poppins Light, violet.
- **Inverted version** (white shield, violet check) on violet backgrounds.
- Minimum size: 24 px symbol; keep clear space equal to the spark's diameter. Do not rotate,
  recolour outside the palette, add effects or place on busy images.

## Colour
| Token | Value | Use |
|---|---|---|
| Brand violet | `#6161ff` | Logo, large decorative elements |
| Action violet | `#5050f0` (hover `#3f3fd8`) | Buttons, links, active states (AA on white and canvas) |
| Ink | `#2b2d3a` | Headings and body text |
| Slate | `#535768` | Secondary text |
| Canvas | `#f5f6f8` | Page background |
| Card | `#ffffff` | Surfaces, with border `#d0d4e4` and soft shadow |
| Pastels | mint `#e3fbd0`, sky `#dcf7ff`, lavender `#eddff7`, periwinkle `#e7ecff`, peach `#ffe6d5` | Category and feature cards only — never text, borders or buttons |
| Status | success `#1b6b36`/`#e3f7d6`, warning `#8a4b00`/`#fff0dc`, danger `#b42318`/`#fde8e7`, info `#3434c9`/`#e7ecff` | Finding and review states (text/soft background pairs, ≥ 4.5:1) |

Violet is the **only** action colour. Gradients: the warm violet→pink headline accent on the
landing page, and the prism line (logo spark, small dividers). Never as button or surface fills.

## Typography
Poppins (self-hosted through `next/font`): Light 300 for display headlines with slight negative
tracking, Regular 400 for body, Medium 500 for UI labels, SemiBold 600 for card titles.

## Shape and depth
Pill buttons (fully rounded), 24 px cards, 6 px inputs and badges, 16 px tiles inside cards. One
soft shadow (`0 2px 48px rgba(205,208,223,.4)`); a slightly stronger one on hover. Generous
spacing (8 px grid, ~64 px between landing sections).

## Imagery
The product is the hero: illustrative UI previews (always labelled "Vista ilustrativa con datos de
ejemplo") instead of stock photos. No fake testimonials, client logos or invented statistics.

## Accessibility
WCAG 2.1 AA is part of the brand: every text/background pair is checked, focus is always visible
(violet 3 px outline), and axe runs on every screen in the E2E suite.
