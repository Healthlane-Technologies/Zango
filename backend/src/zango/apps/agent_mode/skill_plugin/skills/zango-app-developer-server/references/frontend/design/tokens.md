# The token layer

Copy this file into `src/custom/pages/tokens.css` and import it once from
`shared.tsx`. Everything in the design kit references these names.

It exists because the theme gives you **one hue plus gray**. A page built from
only `--color-brand-500` and `--color-gray-*` has no tonal range to design
with, and comes out flat no matter how the components are written. This block
derives a full ramp from the tenant's single brand colour with `color-mix`, so
you get range **and** per-tenant re-skinning — the brand hex stays the only
input.

**Never hard-code a hex for brand or gray.** The literals below are only for
the accent and semantic hues, which the theme does not supply.

```css
@import url('https://fonts.googleapis.com/css2?family=Inter:opsz,wght@14..32,400..700&family=JetBrains+Mono:wght@400;500;600&display=swap');

:root {
  /* -- Brand, hydrated from the Zango theme ---------------------- */
  --brand:        var(--color-brand-500);
  --brand-hover:  color-mix(in oklch, var(--brand) 88%, white);
  --brand-active: color-mix(in oklch, var(--brand) 90%, black);
  --brand-50:     color-mix(in oklch, var(--brand)  7%, white);
  --brand-100:    color-mix(in oklch, var(--brand) 14%, white);
  --brand-200:    color-mix(in oklch, var(--brand) 28%, white);
  --brand-600:    color-mix(in oklch, var(--brand) 84%, black);
  --brand-700:    color-mix(in oklch, var(--brand) 70%, black);
  --brand-ring:   color-mix(in oklch, var(--brand) 18%, transparent);

  /* -- Accent: the SECOND hue. Without it the page reads as one
        colour plus gray, which is the "unfinished" tell. Pick from
        the direction table in directions.md. ---------------------- */
  --accent:     #2FB59E;
  --accent-50:  #EAF7F4;
  --accent-100: #C9EBE4;
  --accent-600: #1F8A78;
  --accent-700: #1A6F61;

  /* -- Surfaces: three tones. A page where everything is white on
        white is the clearest tell of an unfinished UI. ------------ */
  --surface-page:    #FAFAFB;
  --surface-card:    #FFFFFF;
  --surface-sunken:  #F4F5F8;
  --surface-tinted:  color-mix(in oklch, var(--brand) 6%, white);
  --surface-overlay: rgba(15, 18, 28, 0.6);

  /* -- Text: SEVEN levels, slightly cool. Three levels of gray is
        what makes generated pages read flat. --------------------- */
  --text-strong:  #0B0D14;
  --text:         #14171F;
  --text-sub:     #4A4F5C;
  --text-muted:   #767A88;
  --text-faint:   #A4A8B5;
  --text-ghost:   #C9CCD4;
  --text-inverse: #FFFFFF;

  /* -- Borders: cooler and softer than tailwind's gray-200 ------- */
  --border-faint:  #EEEFF2;
  --border:        #E2E4E9;
  --border-strong: #C7CAD3;

  /* -- Semantic. Warm success, amber warning; red is reserved for
        genuine failure, not for every negative number. ----------- */
  --ok:   #2E9E6B;  --ok-50:   #E9F6EF;  --ok-700:   #1C6A46;
  --warn: #DA800B;  --warn-50: #FEF6E7;  --warn-700: #91490D;
  --bad:  #C92535;  --bad-50:  #FDEEEF;  --bad-700:  #871625;

  /* -- Shadows: compound, never single-layer. The inset top
        highlight is invisible until you look for it and is most of
        what separates a modern card from a bordered rectangle. ---- */
  --shadow-xs: 0 1px 1px rgba(15,18,28,.02), 0 1px 2px rgba(15,18,28,.04);
  --shadow-sm: 0 1px 2px rgba(15,18,28,.04), 0 2px 4px rgba(15,18,28,.04),
               inset 0 1px 0 rgba(255,255,255,.5);
  --shadow-md: 0 2px 4px rgba(15,18,28,.05), 0 8px 16px -4px rgba(15,18,28,.08),
               inset 0 1px 0 rgba(255,255,255,.6);
  --shadow-lg: 0 4px 8px rgba(15,18,28,.06), 0 16px 32px -8px rgba(15,18,28,.12),
               inset 0 1px 0 rgba(255,255,255,.6);
  --shadow-brand: 0 4px 12px -2px color-mix(in oklch, var(--brand) 22%, transparent),
                  0 2px 4px rgba(15,18,28,.04);

  /* -- Radii / motion ------------------------------------------- */
  --radius-sm: 6px;  --radius: 8px;  --radius-lg: 12px;  --radius-xl: 16px;
  --ease-out:    cubic-bezier(0.22, 1, 0.36, 1);
  --ease-spring: cubic-bezier(0.34, 1.26, 0.64, 1);
  --dur-fast: 160ms;  --dur: 220ms;
}

/* Inter variable with optical sizing and the stylistic alternates that
   give Linear and Vercel their text texture: single-story a (cv11),
   open digits (ss01), curved-leg l (ss03). Apply on the page root. */
.pe-root {
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
  font-feature-settings: 'cv11', 'ss01', 'ss03';
  font-optical-sizing: auto;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  color: var(--text);
  background: var(--surface-page);
}

.pe-mono {
  font-family: 'JetBrains Mono', 'SF Mono', Consolas, monospace;
  font-variant-numeric: tabular-nums;
}

/* Figures: always tabular, always tight. */
.pe-figure {
  font-variant-numeric: tabular-nums;
  letter-spacing: -0.035em;
  font-weight: 700;
  line-height: 1;
}

/* The one place ALL-CAPS is allowed. */
.pe-eyebrow {
  font-size: 10.5px;
  font-weight: 600;
  letter-spacing: 0.07em;
  text-transform: uppercase;
  color: var(--text-muted);
}

/* Entrance: 40ms stagger, each under 400ms. Wrap major blocks. */
@keyframes pe-rise {
  from { opacity: 0; transform: translateY(8px); }
  to   { opacity: 1; transform: none; }
}
.pe-enter { opacity: 0; animation: pe-rise 320ms var(--ease-out) forwards; }

@media (prefers-reduced-motion: reduce) {
  .pe-enter { opacity: 1; animation: none; transform: none; }
}
```

## Type scale

Size, weight and **tracking** together — tracking is the half that gets
forgotten, and its absence is why generated headings look generic. Display
sizes are tight; micro-labels are wide.

| Use | Size | Weight | Tracking |
|---|---|---|---|
| Hero figure | 44-56px | 700 | -0.045em |
| Page title | 26-30px | 700 | -0.035em |
| Section title | 18-20px | 600 | -0.02em |
| Card title | 13-15px | 575 | -0.01em |
| Body | 13-14px | 400-450 | normal |
| Small / meta | 11.5-12.5px | 400-530 | normal |
| Micro-label | 10.5-11px | 600 | +0.07em, uppercase |
| Mono (ids, codes) | 12-13px | 500 | -0.01em |

**Use the in-between variable weights** — `450` for lighter body, `530` for
medium emphasis, `575` for just-shy-of-bold. Jumping 400 → 600 for everything
is what produces a page with only two levels of emphasis.

Always `font-variant-numeric: tabular-nums` on any figure that can change.

## The entrance wrapper

```tsx
const Rise = ({ i = 0, children, className = '' }:
  { i?: number; children: ReactNode; className?: string }) => (
  <div className={`pe-enter ${className}`}
       style={{ animationDelay: `${Math.min(i, 8) * 40}ms` }}>
    {children}
  </div>
);
```

Wrap each major block with an incrementing `i`. Capped at 8 so a long page
does not trail in for two seconds.
