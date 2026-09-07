# eimir. Brand Guidelines

**Status:** Authoritative Brand & Design Foundation  
**Version:** 2.0  
**Effective Date:** September 7, 2026  
**Claim:** „Euer gemeinsamer Ort.“

---

## 1. Brand Identity & Philosophy

`eimir.` is the digital home for two people in a relationship. It is not a social network, not an administrative productivity dashboard, and not a dating app.

### Core Character
- **Warm & Tactile:** Feels like a real, physical place of trust, warmth, and shared memories—not a sterile SaaS CRUD interface.
- **Calm & Protected:** Prioritizes calm togetherness over stimulation, dopamine loops, and artificial urgency.
- **Authentic & Mature:** Celebrates genuine shared life and quiet everyday rituals without falling into kitsch, pink heart clichés, or superficial pastel decoration.
- **Equal & Balanced:** Designed for two equal partners. Neither profile nor person takes precedence over the shared space.

---

## 2. Brand Name & Wordmark

### Canonical Name: `eimir.`
- **Strictly lowercase with terminal dot:** The public consumer brand name is always written as `eimir.` (lowercase "e", followed by "imir", terminated with a period/dot).
- **The Terminal Dot:** In display and brand lockups, the terminal dot is accented with the primary brand color (`Brand Strong` / `Brand Coral`). The dot symbolizes a deliberate pause, an anchor, and the grounding center of a shared space.
- **Code & Namespaces:** Technical namespaces (`de.sidebyside.next`), database schemas, and existing internal classes (`SideBySideTheme`) remain stable to ensure platform reliability. Only public, user-facing touchpoints use `eimir.`.

### Wordmark Usage
- In headers and navigation, the wordmark uses `Instrument Sans` with bold weight and tight letter spacing (`-0.035em`).
- In inverse presentation (e.g., dark hero cards), the dot adopts the high-contrast accent token (`--color-on-accent`).

---

## 3. The Brand Symbol (Interlocking Rings)

### Symbolism
The `eimir.` mark evolves the signature two-ring motif:
- **Two Independent People:** Two distinct circles represent two independent partners with their own identity, thoughts, and personal space.
- **A Protected Shared Space:** Where the two rings intersect, a shared, protected third space emerges—representing their relationship, shared memories, and plans.
- **NOT an Infinity Loop:** The mark is deliberately composed of two intersecting rings, **not** a figure-8 or infinity symbol. The relationship is grounded in mutual choice and presence, not endless abstraction.

### Asset Delivery
- **Web:** Self-contained inline vector mark and standalone `favicon.svg` with 135° warm gradient (`#D93D59` → `#BE2340`).
- **Android:** Adaptive vector drawable (`ic_launcher_foreground.xml`, `ic_launcher_monochrome.xml`) and dynamic Compose component (`BrandMark.kt`) rendered with hardware-accelerated linear gradient brush.

---

## 4. Color Architecture & Token Authority

`design/tokens.json` is the sole source of truth for all color, typography, spacing, radius, and motion tokens across Web and Android.

### Primary Palette
| Role | Hex (Light) | Hex (Dark) | Meaning & Emotional Intent |
|---|---|---|---|
| **Brand Strong** | `#BE2340` | `#BE2340` | Primary interactive elements, buttons, high emphasis |
| **Brand Coral** | `#D93D59` | `#FF6B85` | Signature brand accent, wordmark dot, interactive focus |
| **Brand Glow / Aura** | `#D93D5926` | `#FF6B8524` | Ambient warm aura behind hero surfaces |
| **Brand Surface** | `#FFF0F2` | `#401925` | Soft tinted brand container |

### Relationship & Space Palette
| Role | Hex (Light) | Hex (Dark) | Meaning & Emotional Intent |
|---|---|---|---|
| **Shared Mint** | `#207266` | `#72D8C4` | Togetherness, shared tasks, synchronized state, memories |
| **Shared Surface** | `#EDF7F5` | `#143630` | Shared badge container, collaborative list highlight |
| **Private Rose** | `#D13B65` | `#FF658E` | Private personal notes, gifts, solo wishlists |
| **Peach / Sunset** | `#F5A882` | `#FFD68A` | Warmth, discovery, milestones, optimism |
| **Soft Lavender** | `#8A7DB8` | `#D6CBE0` | Dusk, contemplation, quiet moments |

### Neutral & Foundation Palette
| Role | Hex (Light) | Hex (Dark) | Meaning & Emotional Intent |
|---|---|---|---|
| **Background (Cream / Night)** | `#FAF7F5` | `#18131D` | Calm, warm, tactile ground (never clinical `#FFFFFF` or cold `#000000`) |
| **Surface** | `#FFFFFF` | `#231C29` | Cards, sheets, dialog surfaces |
| **Surface Subtle** | `#F5EFE9` | `#2C2333` | Receding panels, segmented controls, table headers |
| **Surface Raised** | `#FFFFFF` | `#32283A` | Modals, elevated cards, floating menus |
| **Ink (Text Primary)** | `#231E28` | `#FCF8FA` | High-contrast typography (Deep Aubergine) |
| **Text Secondary** | `#5E5466` | `#D6CBE0` | Subtitles, supporting copy |
| **Text Muted** | `#8C8094` | `#9D90A8` | Helper text, disabled states, timestamps |
| **Border / Divider** | `#E4DDD6` | `#473B54` | Warm card outlines and dividers |

---

## 5. Typography

Typography is self-hosted with zero runtime CDN dependencies.

1. **Editorial & Emotion — Literata:**
   - Used for emotional milestones, Today hero moments, story titles, memory quotes.
   - Conveys intimacy, permanence, and editorial warmth.
2. **UI & Structure — Instrument Sans:**
   - Used for navigation, controls, forms, planning cards, list items, and settings.
   - Modern, human, grotesque typeface with high legibility at all densities.

---

## 6. Voice & Tone

- **Perspective:** Speak directly to the couple (*„ihr“*, *„euer“*, *„gemeinsam“*).
- **Tone:** Empathetic, calm, respectful, unhurried.
- **Clarity over cleverness:** Explain actions concretely and empathetically rather than with abstract system terminology.
- **No artificial pressure:** Never use streaks, guilt mechanics (e.g. "You haven't sent Lea anything today!"), or manipulative push notifications.

---

## 7. Do's and Don'ts

### Do:
- Always write `eimir.` with lowercase "e" and the terminal dot in consumer copy.
- Use warm cream (`#FAF7F5`) as the light page background.
- Highlight the terminal dot in the brand lockup with `Brand Strong` / `Brand Coral`.
- Maintain WCAG 2.2 AA contrast ratios (at least 4.5:1 for body text, 3:1 for UI controls).
- Keep design tokens in sync between `design/tokens.json`, Web CSS, and Android Compose.

### Don't:
- Never capitalize as "Eimir" or "EIMIR" in marketing copy, app titles, or UI strings.
- Do not draw the symbol as an infinity loop or continuous ribbon.
- Do not overload views with pink hearts, glitter, or kitschy romance graphics.
- Do not design dense data tables, KPI cards, or admin grids that look like a corporate SaaS product.
- Never hardcode color hex values in feature components—always consume semantic tokens.
