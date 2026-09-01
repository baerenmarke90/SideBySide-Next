# 5. Deliver Fraunces, and let the platform supply the UI face

- **Status:** accepted
- **Date:** 2026-09-01
- **Issue:** #361

## Context

`design/tokens.json` named two faces, Inter for UI and Fraunces for display, and
both clients declared them. Neither delivered them. There was no `@font-face`
rule and no font file anywhere in the repository, and Android fell back to
`FontFamily.SansSerif` and `FontFamily.Serif`. The specified typography was
documented but never reached a user on either platform.

The two faces are not worth the same. A platform's own UI face is already a
neutral grotesque — Roboto on Android, the system face on the Web — so Inter
would have cost bytes on both clients for a difference few people could name.
Fraunces is the opposite: it is what gives an editorial moment a voice, and its
documented fallback of `Georgia, serif` does not even exist on Android, where
the fallback is Noto Serif.

The value is concentrated in one face; the cost would have been spread over two.

## Decision

Deliver **Fraunces only**, self-hosted, as one variable file per client. The UI
face is the platform's own, and `design/tokens.json` and
`docs/DESIGN-PRINCIPLES.md` say so rather than naming a face that is not
shipped.

Fraunces is used where the design principles reserve it: the page heading on the
Web, and the Story heading and a memory's own title on Android.

## Consequences

**Nothing is fetched at runtime.** The measured cost is 35 kB of woff2 on the
Web (Latin subset, which is the entire supported locale set) and 360 kB of TTF
in the APK, which Android needs because it cannot read woff2. A single variable
file covers every weight in the scale, so no static cuts are bundled.

A font host was never a real option here. It would put a third party into the
path of a product whose premise is that only two people are in it, Self-Hosted
installations have no external access to rely on, and `web/nginx.conf` already
sets `font-src 'self'`, which would have blocked it.

**Licensing.** Fraunces is under the SIL Open Font License 1.1, which explicitly
permits embedding and redistribution, including commercially, at no cost and
without registration. The licence text ships with both copies —
`web/public/fonts/OFL.txt` and `assets/OFL-Fraunces.txt` in the APK — because
the OFL requires the font to travel with it. No attribution in the interface is
required.

The Web copy is the Latin subset that Google Fonts distributes. A subset is
strictly a modification, which the OFL's Reserved Font Name clause speaks to;
in practice both Google and the Fraunces authors distribute these subsets under
the OFL with the name unchanged. Serving the unmodified 360 kB file on the Web
as well would remove even that question, at roughly 100 kB more transfer after
compression.

**A face that renders nowhere is not delivered.** Bundling Fraunces initially
changed nothing on screen, because it was attached only to a `display` role that
no surface used. That is why this decision names the headings it applies to
rather than only the file it ships.

## Alternatives considered

- **Deliver both faces.** Rejected: roughly double the cost for a UI difference
  against an already-neutral platform face.
- **A third-party font host.** Rejected on privacy grounds, and blocked by the
  existing CSP.
- **Keep the fallbacks and rewrite the specification around them.** A legitimate
  and cheaper outcome, rejected because it would give up the one face that
  carries the product's character for 35 kB and 360 kB.
- **Static cuts instead of a variable file.** Rejected: several files to cover
  the same weights, for no size gain at this scale.
