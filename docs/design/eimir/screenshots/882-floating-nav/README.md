# Floating Bottom Navigation visual evidence — #882

Rendered visual evidence for the #882 integration of Quick Create into a floating bottom navigation on Compact/Mobile Web (`Wir · Momente · + · Planen · Mehr`). Every image is a real browser render of the Web client at the stated viewport and theme state via Playwright (`web/e2e/tests/floating-bottom-nav.spec.ts`).

## Visual Evidence Matrix

| File | Viewport / State | What it shows |
| :--- | :--- | :--- |
| [`00-quick-create-sheet-open-390.png`](./00-quick-create-sheet-open-390.png) | 390×844, Light | Quick Create bottom sheet opened via center trigger. Demonstrates layer stacking (`z-index: 100` sheet and `z-index: 95` backdrop over `z-index: 50` floating shell) and authoritative 7-action taxonomy (`Erinnerung`, `Herzmoment`, `Meilenstein`, `Wunsch`, `Plan`, `Notiz`, `Geschenkidee` under `NUR FÜR MICH`). |
| [`01-today-390-light.png`](./01-today-390-light.png) | 390×844, Light | `/today` canonical view with floating bottom navigation. Pill-shaped elevated surface, exactly 4 navigation destinations (`Wir`, `Momente`, `Planen`, `Mehr`) and center action button (`+`). Active state on `Wir`. |
| [`02-today-390-dark.png`](./02-today-390-dark.png) | 390×844, Dark | `/today` in Dark mode (`data-theme="dark"`). Pill surface, frosted backdrop, brand glow, and calm active highlight. |
| [`03-memory-create-390-light.png`](./03-memory-create-390-light.png) | 390×844, Light | Memory Create (`/story/memories/new`) scrolled to bottom. Save and Cancel buttons clear the floating navigation with safe-area padding (`--shell-content-bottom-clearance`). |
| [`04-memory-create-390-dark.png`](./04-memory-create-390-dark.png) | 390×844, Dark | Memory Create (`/story/memories/new`) in Dark mode scrolled to bottom. Active destination indicator on `Momente`. |
| [`05-plan-390-light.png`](./05-plan-390-light.png) | 390×844, Light | Plan surface (`/plan`) with active state on `Planen`. Symmetrical horizontal balance around center button. |
| [`06-momente-390-light.png`](./06-momente-390-light.png) | 390×844, Light | Story surface (`/story`) with active state on `Momente`. |
| [`07-reflow-320px.png`](./07-reflow-320px.png) | 320 CSS px reflow | Responsive reflow down to 320px width without horizontal scroll (`scrollWidth <= clientWidth`). Floating shell maintains legible typography and touch targets. |
| [`08-small-height-390x640.png`](./08-small-height-390x640.png) | 390×640, small height | Constrained height viewport demonstrating non-disruptive vertical footprint and clearance. |
| [`09-keyboard-open-state.png`](./09-keyboard-open-state.png) | 390×844, form focus | Focused title input on Memory Create form, showing floating navigation integration during form data entry. |
| [`10-expanded-desktop-1280x800.png`](./10-expanded-desktop-1280x800.png) | 1280×800, Desktop | Expanded viewport regression check. Floating bottom shell is hidden (`display: none`), standard top navigation and shell elements remain authoritative. |
