// src/custom/pages/shared.tsx
//
// Shared UI primitives. Everything here is module scope and defined exactly
// once -- components defined inside a render are remounted on every parent
// render, which makes CrudHandler lose its state (see entity-360.md §5).

import { ReactNode } from 'react';
import { useNavigate } from 'react-router-dom';
import { TableBody } from '@zango-core/crud/table';

/* The token layer. Written at 5c from references/frontend/design/tokens.md,
   with --accent set from the direction row picked at 5b. It defines every
   --surface-*, --text-*, --border, --shadow-* and --brand-* name used below,
   so this import is required, not optional: without it the primitives fall
   back to unstyled and the pages come out flat. */
import './tokens.css';

/* ================================================================== *
 * DESIGN TOKENS -- the TS half
 * ==================================================================
 *
 * Colour, type and shadow live in tokens.css. What lives here is what
 * Tailwind classes must be chosen for at build time -- radius, padding
 * and figure sizes, which vary by direction and cannot be a CSS
 * variable in a utility class.
 *
 * Set DIRECTION from the row picked at 5b
 * (references/frontend/design/directions.md) and every page changes
 * together. This is what stops two Zango apps built from the same
 * primitives looking like the same app.
 *
 * Colour still comes from the theme -- never hard-code a brand or gray
 * hex. tokens.css derives the whole brand ramp from the tenant's one
 * configured colour.
 *
 *   precision   dense rows, tight radius. An all-day worklist.
 *   editorial   generous air, large display type, soft radius.
 *   ledger      dense and figure-led: money and records.
 *   care        airy with larger text; a person is the subject.
 *   console     very dense, mono-heavy: systems and health.
 */

const DIRECTION: 'precision' | 'editorial' | 'ledger' | 'care' | 'console' = 'precision';

/* Derived treatment. Read these; do not re-derive them per component. */
const T = {
  precision: {
    radius: 'rounded-lg',
    radiusSm: 'rounded-md',
    pad: 'p-3.5',
    padTight: 'p-3',
    gap: 'gap-3',
    sectionGap: 'space-y-4',
    body: 'text-[12.5px]',
    row: 'py-2',
    display: 'text-[26px]',
    anchor: 'text-[44px]',
  },
  editorial: {
    radius: 'rounded-2xl',
    radiusSm: 'rounded-xl',
    pad: 'p-5',
    padTight: 'p-4',
    gap: 'gap-5',
    sectionGap: 'space-y-6',
    body: 'text-[14px]',
    row: 'py-3.5',
    display: 'text-[36px]',
    anchor: 'text-[56px]',
  },
  ledger: {
    radius: 'rounded-xl',
    radiusSm: 'rounded-lg',
    pad: 'p-4',
    padTight: 'p-3.5',
    gap: 'gap-3',
    sectionGap: 'space-y-4',
    body: 'text-[12.5px]',
    row: 'py-2',
    display: 'text-[30px]',
    anchor: 'text-[48px]',
  },
  care: {
    radius: 'rounded-2xl',
    radiusSm: 'rounded-xl',
    pad: 'p-5',
    padTight: 'p-4',
    gap: 'gap-4',
    sectionGap: 'space-y-5',
    body: 'text-[14px]',
    row: 'py-3',
    display: 'text-[30px]',
    anchor: 'text-[48px]',
  },
  console: {
    radius: 'rounded-md',
    radiusSm: 'rounded',
    pad: 'p-3',
    padTight: 'p-2.5',
    gap: 'gap-2.5',
    sectionGap: 'space-y-3',
    body: 'text-[12px]',
    row: 'py-1.5',
    display: 'text-[24px]',
    anchor: 'text-[40px]',
  },
}[DIRECTION];

/* ------------------------------------------------------------------ *
 * Surfaces -- three tones, not one.
 *
 * A page where everything is white on white is the single clearest tell
 * of an unfinished UI. The 1-2% tonal step between the page ground and
 * a raised card is what produces depth; the sunken tone is what lets a
 * block sit *inside* a card without another border.
 *
 *   PAGE    the ground. Slightly off-white, never pure #fff.
 *   CARD    raised. Pure white, so it reads as lifted off the ground.
 *   SUNKEN  recessed. For insets, table headers, quiet sub-blocks.
 * ------------------------------------------------------------------ */

const SURFACE = {
  page: 'bg-[color:var(--surface-page)]',
  card: 'bg-[color:var(--surface-card)]',
  sunken: 'bg-[color:var(--surface-sunken)]',
  tinted: 'bg-[color:var(--surface-tinted)]',
};

/* Borders and text come from tokens.css too, written inline as
   `text-[color:var(--text-muted)]` / `border-[color:var(--border)]`.
   The seven text levels are the point -- three levels of gray is what
   makes a page read flat, so reach past --text and --text-muted for
   --text-sub, --text-faint and --text-ghost where the hierarchy needs
   them. */

/* ------------------------------------------------------------------ *
 * Shadows -- compound, never single-layer.
 *
 * Each level stacks an ambient spread, a tighter key shadow, and (at
 * rest, on a raised surface) a 1px inset white highlight along the top
 * edge. That inset is invisible until you look for it and is most of
 * what separates a modern card from a bordered rectangle -- it fakes
 * the light catching the card's top lip.
 *
 * RAISE is the hover partner for CARD: the same shape, lifted. Always
 * pair it with a transform so the lift is felt, not just seen.
 * ------------------------------------------------------------------ */

const SHADOW = {
  card: 'shadow-[var(--shadow-sm)]',
  raiseOnHover: 'hover:shadow-[var(--shadow-md)]',
  rail: 'shadow-[var(--shadow-xs)]',
};

/* ------------------------------------------------------------------ *
 * Motion -- every interactive surface responds, every page enters.
 *
 * Two rules, both cheap and both load-bearing:
 *   1. Nothing appears instantly. Entrance is staggered, 40ms apart,
 *      total under 400ms. See <Enter> below.
 *   2. Everything clickable changes on hover. A card that does not
 *      respond reads as a picture of a card.
 *
 * Durations are fast (200-260ms). Slow entrances feel sluggish, not
 * elegant. Easing is a decelerating cubic-bezier, never `linear`.
 *
 * REDUCED honours prefers-reduced-motion -- required, not optional.
 * ------------------------------------------------------------------ */

const MOTION = {
  base: 'transition-all duration-200 ease-[cubic-bezier(0.22,1,0.36,1)]',
  /** Hover lift for a card that navigates or opens something. */
  lift: 'hover:-translate-y-[2px] motion-reduce:hover:translate-y-0',
};

/* Staggered entrance wrapper. Wrap the major blocks of a page:
 *
 *   <Enter i={0}><KeyFacts .../></Enter>
 *   <Enter i={1}><Section  .../></Enter>
 *
 * `i` is the sibling index -- 40ms apart, capped so a long list does
 * not trail in for two seconds. Under prefers-reduced-motion the
 * animation is dropped and the content is simply present. */
export const Enter = ({
  i = 0,
  children,
  className = '',
}: {
  i?: number;
  children: ReactNode;
  className?: string;
}) => (
  <div
    className={'pe-enter ' + className}
    style={{ animationDelay: `${Math.min(i, 8) * 40}ms` }}
  >
    {children}
  </div>
);

/* `pe-enter`, its keyframes and the prefers-reduced-motion override all
 * live in tokens.css -- defined once there rather than injected from a
 * component, so they are not re-emitted per page. */

/* ------------------------------------------------------------------ *
 * Formatting -- the ONLY place currency / date / number format is
 * decided, so the whole app is consistent by construction.
 *
 * Infer LOCALE and CURRENCY from the app's context: the business the
 * spec describes, the tenant's locale, phone/address formats in existing
 * data. Do not ask -- decide, and record it as an assumption in your
 * summary. Because both live here, a wrong guess is a one-line fix.
 * Never leave the '$'/'en-US' default on a non-US app.
 * ------------------------------------------------------------------ */

const LOCALE = 'en-IN';        // <-- infer; see note below
const CURRENCY = 'INR';        // <-- infer; see note below

/* Column names arrive as `estimated_value`; never print that at a user.
   Already-humanised labels pass through unchanged. */
export const humanise = (s: string) =>
  String(s ?? '')
    .replace(/_/g, ' ')
    .replace(/\s+/g, ' ')
    .trim()
    .replace(/\b\w/g, (c) => c.toUpperCase());

/* The detail API sends empty fields as the STRING "NA", which is truthy -- so
   `v ? a : b` and `v ?? b` both render a literal "NA" at the user. Every
   formatter below goes through this, and so should your own call sites. */
export const clean = (v: any) =>
  v == null || v === 'NA' || v === '' ? undefined : v;

export const Money = ({ value }: { value: any }) => {
  if (clean(value) === undefined) return <>&mdash;</>;
  const n = Number(value);
  if (Number.isNaN(n)) return <>&mdash;</>;
  return (
    <span className="tabular-nums">
      {n.toLocaleString(LOCALE, { style: 'currency', currency: CURRENCY })}
    </span>
  );
};

export const Num = ({ value }: { value: any }) => {
  if (value === null || value === undefined || value === '') return <>&mdash;</>;
  const n = Number(value);
  if (Number.isNaN(n)) return <>&mdash;</>;
  return <span className="tabular-nums">{n.toLocaleString(LOCALE)}</span>;
};

export const DateText = ({ value }: { value: any }) => {
  if (!clean(value)) return <>&mdash;</>;
  const d = new Date(value);
  if (Number.isNaN(d.getTime())) return <>{String(value)}</>;
  return (
    <span>
      {d.toLocaleDateString(LOCALE, { day: '2-digit', month: 'short', year: 'numeric' })}
    </span>
  );
};

/* ------------------------------------------------------------------ *
 * Layout
 * ------------------------------------------------------------------ */

/* Detail pages and hand-built custom pages ONLY -- never wrap a CrudHandler
 * list in this. See "Which pages get a PageShell" below.
 *
 * The app already renders inside the platform's sidebar shell, so the content
 * area is roughly `viewport - 260px`. A narrow cap here strands the rest as an
 * empty grey band: a 1080px cap on a 1920px screen left ~640px of unused page
 * beside a detail view. `max-w-[1600px]` fills a laptop and still stops lines
 * from running to absurd lengths on an ultrawide. */
/* `pe-root` carries the Inter variable font, its optical sizing and the
   cv11/ss01/ss03 feature settings from tokens.css. Without it the page
   renders in the browser default and loses most of its typographic
   character, so every page surface starts here. */
export const PageShell = ({ children }: { children: ReactNode }) => (
  <div className={'pe-root min-h-full ' + SURFACE.page}>
    <div className="mx-auto w-full max-w-[1600px] px-4 py-6 md:px-6">{children}</div>
  </div>
);

export const Card = ({
  children,
  tinted = false,
  tone,
  interactive = false,
  className = '',
}: {
  children: ReactNode;
  tinted?: boolean;
  tone?: 'good' | 'warn' | 'bad' | 'info';
  /** Set when the card navigates or opens something -- adds the hover
   *  lift. A card that responds to hover but does nothing is a lie. */
  interactive?: boolean;
  className?: string;
}) => {
  /* `tone` carries meaning -- a monitoring block that is healthy, a
     warning that needs action. Never use it for decoration: an
     app where every card is tinted has no emphasis left to spend.

     Uses the SAME semantic tokens as StatusChip below
     (--color-success/warning/error-*), not a second green/amber/red
     palette -- a real run had Card and StatusChip disagreeing about what
     "good" looked like because they drew from two different token sets. */
  const toned = tone
    ? {
        good: 'border-[color:var(--color-success-200,#bbf7d0)] bg-[color:var(--color-success-50)]',
        warn: 'border-[color:var(--color-warning-200,#fde68a)] bg-[color:var(--color-warning-50)]',
        bad: 'border-[color:var(--color-error-200,#fecaca)] bg-[color:var(--color-error-50)]',
        info: 'border-[color:var(--color-brand-200)] bg-[color:var(--color-brand-50)]',
      }[tone]
    : tinted
      ? 'border-[color:var(--color-brand-200)] bg-[color:var(--color-brand-50)]'
      : 'border-[color:var(--border)] ' + SURFACE.card;

  return (
    <div
      className={
        T.radius + ' border ' + T.pad + ' ' + SHADOW.card + ' ' + MOTION.base + ' ' +
        (interactive
          ? 'cursor-pointer ' + SHADOW.raiseOnHover + ' ' + MOTION.lift + ' '
          : '') +
        toned +
        ' ' +
        className
      }
    >
      {children}
    </div>
  );
};

/* ------------------------------------------------------------------ *
 * Inset -- a nested surface INSIDE a card. This is the single biggest
 * difference between a card that looks designed and a white box: the
 * lead card holds sub-blocks on their own quiet fill, rather than
 * stacking flat rows. No shadow (it is already on a raised surface).
 * ------------------------------------------------------------------ */

export const Inset = ({
  children,
  tone,
  className = '',
}: {
  children: ReactNode;
  tone?: 'good' | 'warn' | 'bad' | 'info';
  className?: string;
}) => {
  const toned = tone
    ? {
        good: 'border-[color:var(--color-success-200,#bbf7d0)] bg-[color:var(--color-success-50)]',
        warn: 'border-[color:var(--color-warning-200,#fde68a)] bg-[color:var(--color-warning-50)]',
        bad: 'border-[color:var(--color-error-200,#fecaca)] bg-[color:var(--color-error-50)]',
        info: 'border-[color:var(--color-brand-200)] bg-[color:var(--color-brand-50)]',
      }[tone]
    : 'border-[color:var(--border)] ' + SURFACE.sunken;
  return (
    <div
      className={
        T.radiusSm + ' border ' + T.padTight + ' ' + toned + ' ' + className
      }
    >
      {children}
    </div>
  );
};

/* ------------------------------------------------------------------ *
 * MetricTile -- a number with its qualifier. The qualifier is the
 * point: "218k/uL" alone is data, "218k/uL  . Normal" is an answer.
 * ------------------------------------------------------------------ */

export const MetricTile = ({
  label,
  value,
  qualifier,
  tone = 'neutral',
  hint,
}: {
  label: ReactNode;
  value: ReactNode;
  qualifier?: ReactNode;
  tone?: 'neutral' | 'good' | 'warn' | 'bad';
  hint?: ReactNode;
}) => {
  const dot = {
    neutral: 'bg-[color:var(--text-faint)]',
    good: 'bg-[color:var(--color-success-500,#22c55e)]',
    warn: 'bg-[color:var(--color-warning-500,#f59e0b)]',
    bad: 'bg-[color:var(--color-error-500,#ef4444)]',
  }[tone];
  const txt = {
    neutral: 'text-[color:var(--text-sub)]',
    good: 'text-[color:var(--color-success-700,#15803d)]',
    warn: 'text-[color:var(--color-warning-700,#b45309)]',
    bad: 'text-[color:var(--color-error-700,#b91c1c)]',
  }[tone];
  return (
    <div
      className={
        T.radiusSm +
        ' border border-[color:var(--border)] ' +
        SURFACE.card +
        ' ' +
        T.padTight +
        ' ' +
        SHADOW.card +
        ' ' +
        MOTION.base +
        ' hover:border-[color:var(--border)]'
      }
    >
      <span className="block text-[10.5px] font-semibold uppercase tracking-[0.07em] text-[color:var(--text-muted)]">
        {label}
      </span>
      <div className="mt-1.5 flex items-baseline justify-between gap-2">
        <span className="text-[19px] font-semibold tabular-nums tracking-[-0.02em] text-[color:var(--text-strong)]">
          {value}
        </span>
        {qualifier ? (
          <span className={'inline-flex items-center gap-1.5 text-[12px] ' + txt}>
            <span className={'h-1.5 w-1.5 rounded-full ' + dot} />
            {qualifier}
          </span>
        ) : null}
      </div>
      {hint ? (
        <span className="mt-1 block text-[11.5px] text-[color:var(--text-muted)]">
          {hint}
        </span>
      ) : null}
    </div>
  );
};

export const SectionTitle = ({ children }: { children: ReactNode }) => (
  <h2 className="mb-3 text-[16px] font-semibold text-[color:var(--text-strong)]">
    {children}
  </h2>
);

/* Small uppercase eyebrow label. The one place ALL-CAPS is allowed. */
export const Eyebrow = ({ children }: { children: ReactNode }) => (
  <span className="text-[11px] font-semibold uppercase tracking-[0.07em] text-[color:var(--text-muted)]">
    {children}
  </span>
);

/* ------------------------------------------------------------------ *
 * Header / identity
 * ------------------------------------------------------------------ */

export const PageHeader = ({
  title,
  backLabel,
  avatar,
  reference,
  status,
  actions,
}: {
  title: ReactNode;
  backLabel?: string;
  /** Monogram or icon. Gives the identity block something to anchor on. */
  avatar?: ReactNode;
  reference?: ReactNode;
  status?: ReactNode;
  /** At least one action. A header with none reads as a read-only dump. */
  actions?: ReactNode;
}) => {
  const navigate = useNavigate();
  return (
    <div className="mb-4 border-b border-[color:var(--border)] pb-4">
      {backLabel && (
        <button
          type="button"
          onClick={() => navigate(-1)}
          className="mb-2 rounded text-[13px] text-[color:var(--text-muted)] transition-colors hover:text-[color:var(--text-strong)] focus-visible:outline focus-visible:outline-2 focus-visible:outline-[color:var(--color-brand-500)]"
        >
          &larr; {backLabel}
        </button>
      )}
      <div className="flex flex-wrap items-center gap-3">
        {avatar}
        <h1 className="text-[20px] font-bold tracking-[-0.02em] text-[color:var(--text-strong)] md:text-[24px]">
          {title}
        </h1>
        {reference && (
          <span className="font-mono text-[12px] text-[color:var(--text-muted)]">
            {reference}
          </span>
        )}
        {status}
        {actions && <div className="ml-auto flex items-center gap-2">{actions}</div>}
      </div>
    </div>
  );
};

export const StatusChip = ({
  label,
  tone = 'neutral',
}: {
  label: ReactNode;
  tone?: 'neutral' | 'info' | 'success' | 'warning' | 'error';
}) => {
  const tones: Record<string, string> = {
    neutral: 'bg-[color:var(--surface-sunken)] text-[color:var(--text-sub)]',
    info: 'bg-[color:var(--color-brand-50)] text-[color:var(--color-brand-700)]',
    success: 'bg-[color:var(--color-success-50)] text-[color:var(--color-success-700)]',
    warning: 'bg-[color:var(--color-warning-50)] text-[color:var(--color-warning-700)]',
    error: 'bg-[color:var(--color-error-50)] text-[color:var(--color-error-700)]',
  };
  return (
    <span
      className={
        'inline-flex items-center rounded px-2 py-0.5 text-[12px] font-medium ' +
        (tones[tone] || tones.neutral)
      }
    >
      {label}
    </span>
  );
};

/* ------------------------------------------------------------------ *
 * Key facts -- the 4-8 most consulted fields
 * ------------------------------------------------------------------ */

export const KeyFacts = ({
  fields,
  keys,
  anchor,
  render,
}: {
  fields: Record<string, any>;
  /** 3-7 most-consulted field keys. */
  keys: string[];
  /** The ONE fact this page exists for -- rendered larger, on a tinted card.
   *  Every detail page must name one; without it the strip reads as flat. */
  anchor?: { key: string; sub?: ReactNode };
  render?: Record<string, (v: any) => ReactNode>;
}) => {
  /* The API calls this `name`, NOT `display_name` -- read both so a payload
     change cannot silently blank every label (that produced a strip of
     unlabelled floating numbers on a real run). Fall back to the key.

     `name` is a COLUMN name (`estimated_value`), not a display label, so
     always humanise it -- rendering it raw under the uppercase label class
     prints ESTIMATED_VALUE at the user, which shipped on a real run. */
  const labelOf = (f: any, k: string) =>
    humanise(f?.display_name || f?.label || f?.name || k);

  const anchorField = anchor ? fields?.[anchor.key] : null;
  const rest = keys.filter((k) => k !== anchor?.key);

  return (
    <div className="grid max-md:grid-cols-2 gap-3 py-4 md:grid-cols-4">
      {anchorField && (
        <div
          className={
            'col-span-2 row-span-1 border border-[color:var(--color-brand-200)] ' +
            T.radius +
            ' ' +
            T.pad +
            ' ' +
            SHADOW.card +
            /* Tinted, and carrying a soft brand wash rather than a flat
               fill -- this is the one card on the page allowed to be
               visually louder than its neighbours. */
            ' bg-gradient-to-br from-[color:var(--color-brand-50)] to-[color:var(--color-brand-100)]'
          }
        >
          <span className="block text-[10.5px] font-semibold uppercase tracking-[0.07em] text-[color:var(--color-brand-700)] opacity-80">
            {labelOf(anchorField, anchor!.key)}
          </span>
          <span
            className={
              'mt-1 block font-bold leading-none tracking-[-0.03em] tabular-nums text-[color:var(--color-brand-700)] ' +
              T.anchor
            }
          >
            {render?.[anchor!.key]
              ? render[anchor!.key](anchorField.value)
              : (anchorField.value ?? <>&mdash;</>)}
          </span>
          {anchor!.sub && (
            <span className="mt-1.5 block text-[11px] text-[color:var(--text-muted)]">
              {anchor!.sub}
            </span>
          )}
        </div>
      )}
      {rest.map((k) => {
        const f = fields?.[k];
        if (!f) return null;
        return (
          <div
            key={k}
            className={
              T.radius +
              ' border border-[color:var(--border)] ' +
              SURFACE.card +
              ' ' +
              T.padTight +
              ' ' +
              SHADOW.card +
              ' ' +
              MOTION.base +
              ' hover:border-[color:var(--border)]'
            }
          >
            <span className="block text-[10.5px] font-semibold uppercase tracking-[0.07em] text-[color:var(--text-muted)]">
              {labelOf(f, k)}
            </span>
            <span className="mt-1 block text-[15px] font-semibold tabular-nums text-[color:var(--text-strong)]">
              {render?.[k] ? render[k](f.value) : (f.value ?? <>&mdash;</>)}
            </span>
          </div>
        );
      })}
    </div>
  );
};

/* ------------------------------------------------------------------ *
 * Overview sections -- grouped fields, not one undifferentiated card.
 * A detail page whose Overview is a single card with one value in it
 * is a wireframe; group the remaining fields into titled sections.
 * ------------------------------------------------------------------ */

export const FieldGrid = ({
  fields,
  keys,
  render,
}: {
  fields: Record<string, any>;
  keys: string[];
  render?: Record<string, (v: any) => ReactNode>;
}) => {
  const labelOf = (f: any, k: string) =>
    humanise(f?.display_name || f?.label || f?.name || k);
  return (
    <div className="grid max-sm:grid-cols-1 gap-x-6 gap-y-3.5 sm:grid-cols-2">
      {keys.map((k) => {
        const f = fields?.[k];
        if (!f) return null;
        return (
          <div key={k} className="min-w-0">
            <span className="block text-[10.5px] font-semibold uppercase tracking-[0.07em] text-[color:var(--text-muted)]">
              {labelOf(f, k)}
            </span>
            <span className="mt-0.5 block break-words text-[13.5px] text-[color:var(--text-strong)]">
              {render?.[k] ? render[k](f.value) : (f.value ?? <>&mdash;</>)}
            </span>
          </div>
        );
      })}
    </div>
  );
};

/* ------------------------------------------------------------------ *
 * Tabs -- with optional counts
 * ------------------------------------------------------------------ */

export const Tabs = ({
  value,
  onChange,
  items,
}: {
  value: string;
  onChange: (k: string) => void;
  items: { key: string; label: string; count?: number }[];
}) => (
  <div
    role="tablist"
    className="flex gap-5 overflow-x-auto border-b border-[color:var(--border)] text-[13px]"
  >
    {items.map((it) => {
      const active = value === it.key;
      return (
        <button
          key={it.key}
          role="tab"
          aria-selected={active}
          onClick={() => onChange(it.key)}
          className={
            'whitespace-nowrap border-b-2 py-2.5 transition-colors focus-visible:outline focus-visible:outline-2 focus-visible:outline-[color:var(--color-brand-500)] ' +
            (active
              ? 'border-[color:var(--color-brand-500)] font-semibold text-[color:var(--text-strong)]'
              : 'border-transparent text-[color:var(--text-muted)] hover:text-[color:var(--text-strong)]')
          }
        >
          {it.label}
          {typeof it.count === 'number' && (
            <span className="ml-1.5 rounded bg-[color:var(--surface-sunken)] px-1.5 py-0.5 text-[11px] tabular-nums text-[color:var(--text-sub)]">
              {it.count}
            </span>
          )}
        </button>
      );
    })}
  </div>
);

/* ------------------------------------------------------------------ *
 * The four states (shared-primitives.md)
 * ------------------------------------------------------------------ */

export const Skeleton = ({ className = '' }: { className?: string }) => (
  <div
    className={
      'animate-pulse rounded bg-[color:var(--surface-sunken)] ' + className
    }
  />
);

/* Shape-matched skeletons. A generic grey box is not acceptable. */
export const KeyFactsSkeleton = () => (
  <div className="grid max-md:grid-cols-2 gap-4 py-4 md:grid-cols-4">
    {[0, 1, 2, 3].map((i) => (
      <div key={i}>
        <Skeleton className="mb-2 h-3 w-16" />
        <Skeleton className="h-4 w-24" />
      </div>
    ))}
  </div>
);

export const TableSkeleton = ({ rows = 5 }: { rows?: number }) => (
  <div className="space-y-2 py-2">
    <Skeleton className="h-8 w-full" />
    {Array.from({ length: rows }).map((_, i) => (
      <Skeleton key={i} className="h-10 w-full" />
    ))}
  </div>
);

export const DetailSkeleton = () => (
  <div>
    <Skeleton className="mb-3 h-6 w-48" />
    <KeyFactsSkeleton />
    <Skeleton className="mb-4 h-9 w-full" />
    <TableSkeleton />
  </div>
);

export const EmptyState = ({
  title,
  description,
  action,
}: {
  title: string;
  description?: string;
  action?: ReactNode;
}) => (
  <div className="flex flex-col items-center justify-center px-6 py-12 text-center">
    <svg
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.5"
      strokeLinecap="round"
      strokeLinejoin="round"
      className="mb-3 h-12 w-12 text-[color:var(--text-ghost)]"
      aria-hidden="true"
    >
      <path d="M3 7h18M3 12h18M3 17h10" />
    </svg>
    <h3 className="text-[15px] font-semibold text-[color:var(--text-strong)]">{title}</h3>
    {description && (
      <p className="mt-1 max-w-[320px] text-[13px] text-[color:var(--text-muted)]">
        {description}
      </p>
    )}
    {action && <div className="mt-4">{action}</div>}
  </div>
);

export const ErrorState = ({
  message = 'Something went wrong loading this.',
  onRetry,
}: {
  message?: string;
  onRetry?: () => void;
}) => (
  <div className="flex flex-col items-center justify-center px-6 py-12 text-center">
    <h3 className="text-[15px] font-semibold text-[color:var(--color-error-600)]">
      Could not load
    </h3>
    <p className="mt-1 max-w-[320px] text-[13px] text-[color:var(--text-muted)]">
      {message}
    </p>
    {onRetry && (
      <button
        type="button"
        onClick={onRetry}
        className="mt-4 rounded-lg border border-[color:var(--border)] bg-white px-3 py-1.5 text-[13px] font-medium transition-colors hover:bg-[color:var(--surface-sunken)]"
      >
        Try again
      </button>
    )}
  </div>
);

/* ------------------------------------------------------------------ *
 * Stable table body for entity-360 list pages (entity-360.md §5).
 * Module scope is load-bearing -- do not inline this.
 * ------------------------------------------------------------------ */

export const NavigateTableBody = () => <TableBody defaultDetailView="navigate" />;

/* ------------------------------------------------------------------ *
 * Section -- a titled panel. Overview is built from these, never from
 * one anonymous Card holding everything.
 * ------------------------------------------------------------------ */

export const Section = ({
  title,
  actions,
  children,
}: {
  title: ReactNode;
  actions?: ReactNode;
  children: ReactNode;
}) => (
  <section
    className={
      /* overflow-hidden clips the sunken header bar to the card's
         radius, so the header needs no rounding of its own and cannot
         disagree with T.radius. */
      'mb-4 overflow-hidden border border-[color:var(--border)] ' +
      T.radius +
      ' ' +
      SURFACE.card +
      ' ' +
      SHADOW.card
    }
  >
    {/* The header sits on the sunken tone -- the third surface. This is
        what makes a Section read as a panel with a title bar rather
        than a white rectangle with bold text at the top. */}
    <header
      className={
        /* The parent Section is overflow-hidden, so the header's own
           corners are clipped to the card's radius -- no rounding
           needed here, and none that could disagree with T.radius. */
        'flex items-center gap-3 border-b border-[color:var(--border)] px-4 py-3 ' +
        SURFACE.sunken
      }
    >
      <h2 className="text-[12.5px] font-semibold text-[color:var(--text-sub)]">{title}</h2>
      {actions && <div className="ml-auto flex items-center gap-2">{actions}</div>}
    </header>
    <div className="p-4">{children}</div>
  </section>
);

/* ------------------------------------------------------------------ *
 * Buttons -- so actions look like actions. A detail page header with
 * no action button reads as a read-only dump.
 * ------------------------------------------------------------------ */

export const Button = ({
  children,
  variant = 'secondary',
  onClick,
  type = 'button',
}: {
  children: ReactNode;
  variant?: 'primary' | 'secondary';
  onClick?: () => void;
  type?: 'button' | 'submit';
}) => (
  <button
    type={type}
    onClick={onClick}
    className={
      T.radiusSm +
      ' px-3 py-1.5 text-[12.5px] font-medium ' +
      MOTION.base +
      /* Actions lift on hover and settle on press. The active state is
         what makes a button feel physical rather than painted. */
      ' hover:-translate-y-[1px] active:translate-y-0 motion-reduce:hover:translate-y-0' +
      ' focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-1 focus-visible:outline-[color:var(--color-brand-500)] ' +
      (variant === 'primary'
        ? 'bg-[color:var(--color-brand-500)] text-white shadow-[0_1px_2px_rgba(16,24,40,0.10),inset_0_1px_0_rgba(255,255,255,0.18)] hover:bg-[color:var(--color-brand-700)] hover:shadow-[0_4px_10px_-2px_color-mix(in_srgb,var(--color-brand-500)_40%,transparent)]'
        : 'border border-[color:var(--border)] ' +
          SURFACE.card +
          ' text-[color:var(--text-sub)] shadow-[0_1px_2px_rgba(16,24,40,0.04),inset_0_1px_0_rgba(255,255,255,0.6)] hover:bg-[color:var(--surface-sunken)] hover:border-[color:var(--border-strong)]')
    }
  >
    {children}
  </button>
);

/* ------------------------------------------------------------------ *
 * Avatar -- initials monogram. Gives the identity header something to
 * anchor on when the entity has no image.
 * ------------------------------------------------------------------ */

export const Avatar = ({ name }: { name?: string }) => {
  const initials = (name || '?')
    .split(/\s+/)
    .slice(0, 2)
    .map((w) => w[0])
    .join('')
    .toUpperCase();
  return (
    <span className="grid h-10 w-10 shrink-0 place-items-center rounded-full bg-[color:var(--color-brand-50)] text-[13px] font-bold text-[color:var(--color-brand-700)]">
      {initials}
    </span>
  );
};

/* ------------------------------------------------------------------ *
 * IdentityStrip -- the inline facts under the title. Four to six, each
 * with an optional lucide icon. This is what separates an identity
 * header from a bare title, so pass real facts: reference, key dates,
 * the one relationship that matters, contact.
 * ------------------------------------------------------------------ */

export const IdentityStrip = ({
  items,
}: {
  items: { icon?: ReactNode; text: ReactNode }[];
}) => (
  <div className="mt-1.5 flex flex-wrap items-center gap-x-5 gap-y-1.5">
    {items.filter(Boolean).map((it, i) => (
      <span
        key={i}
        className="inline-flex items-center gap-1.5 text-[12.5px] text-[color:var(--text-sub)]"
      >
        {it.icon ? (
          <span className="text-[color:var(--text-faint)]">{it.icon}</span>
        ) : null}
        {it.text}
      </span>
    ))}
  </div>
);

/* ------------------------------------------------------------------ *
 * DetailLayout -- main column + right rail, the default detail-page
 * shape (SS 6). The rail carries the flat state so the main column is
 * free to be a synthesis. Stacks to one column under lg.
 * ------------------------------------------------------------------ */

export const DetailLayout = ({
  children,
  rail,
}: {
  children: ReactNode;
  rail?: ReactNode;
}) => (
  <div className="grid max-md:grid-cols-1 items-start gap-5 md:grid-cols-3">
    <div className="min-w-0 space-y-5 md:col-span-2">{children}</div>
    {rail ? <aside className="space-y-4 md:col-span-1">{rail}</aside> : null}
  </div>
);

/* ------------------------------------------------------------------ *
 * RailCard -- one block in the right rail. Title, optional count and
 * optional icon; body is whatever the block holds.
 * ------------------------------------------------------------------ */

export const RailCard = ({
  title,
  icon,
  count,
  accent,
  children,
}: {
  title: string;
  icon?: ReactNode;
  count?: number;
  /** Optional 3px top border so multiple RailCards in the same rail read as
   *  distinct blocks rather than N identical white boxes stacked vertically
   *  (design/treatments.md, "the anchor rule" applies
   *  inside the rail too). Use sparingly -- carries meaning like `tone`
   *  elsewhere, not decoration on every card. */
  accent?: 'brand' | 'success' | 'warning' | 'error';
  children: ReactNode;
}) => {
  const topBorder = accent
    ? {
        brand: 'border-t-[3px] border-t-[color:var(--color-brand-500)]',
        success: 'border-t-[3px] border-t-[color:var(--color-success-500)]',
        warning: 'border-t-[3px] border-t-[color:var(--color-warning-500)]',
        error: 'border-t-[3px] border-t-[color:var(--color-error-500)]',
      }[accent]
    : '';
  return (
    <section
      className={
        'overflow-hidden border border-[color:var(--border)] ' +
        T.radius +
        ' ' +
        SURFACE.card +
        ' ' +
        SHADOW.rail +
        ' ' +
        topBorder
      }
    >
      <header className="flex items-center gap-2 px-4 pb-2 pt-3.5">
        {icon ? (
          <span className="text-[color:var(--text-faint)]">{icon}</span>
        ) : null}
        <h3 className="text-[13.5px] font-semibold tracking-[-0.01em] text-[color:var(--text-strong)]">
          {title}
        </h3>
        {typeof count === 'number' && (
          <span className="rounded-md bg-[color:var(--surface-sunken)] px-1.5 py-0.5 text-[11px] font-semibold tabular-nums text-[color:var(--text-sub)]">
            {count}
          </span>
        )}
      </header>
      <div className="px-4 pb-4 text-[13px] text-[color:var(--text-sub)]">
        {children}
      </div>
    </section>
  );
};

/* ------------------------------------------------------------------ *
 * AtAGlance -- the rail's flat-attribute list. Icon + line, nothing
 * else. This is where the flat fields live; do NOT also list them in
 * Overview.
 * ------------------------------------------------------------------ */

export const AtAGlance = ({
  items,
}: {
  items: { icon?: ReactNode; text: ReactNode }[];
}) => (
  <ul className="space-y-2.5">
    {items.filter(Boolean).map((it, i) => (
      <li key={i} className="flex items-start gap-2.5">
        <span className="mt-[1px] text-[color:var(--text-faint)]">
          {it.icon}
        </span>
        <span className="min-w-0 text-[13px] text-[color:var(--text-sub)]">
          {it.text}
        </span>
      </li>
    ))}
  </ul>
);

/* ------------------------------------------------------------------ *
 * Meter -- labelled progress bar. The lead card's workhorse: it turns
 * "1 of 1 funded tests used" into something readable at a glance.
 * `tone` follows status, not decoration.
 * ------------------------------------------------------------------ */

export const Meter = ({
  label,
  value,
  max = 1,
  right,
  hint,
  tone = 'brand',
}: {
  label: ReactNode;
  value: number;
  max?: number;
  right?: ReactNode;
  hint?: ReactNode;
  tone?: 'brand' | 'good' | 'warn' | 'bad';
}) => {
  const pct = max > 0 ? Math.min(100, Math.round((value / max) * 100)) : 0;
  const bar = {
    brand: 'var(--color-brand-500)',
    good: 'var(--color-success-600, #16a34a)',
    warn: 'var(--color-warning-500, #f59e0b)',
    bad: 'var(--color-error-600, #dc2626)',
  }[tone];
  return (
    <div>
      <div className="flex items-baseline justify-between gap-3">
        <span className="text-[13px] text-[color:var(--text)]">
          {label}
        </span>
        {right ? (
          <span className="text-[12.5px] tabular-nums text-[color:var(--text-sub)]">
            {right}
          </span>
        ) : null}
      </div>
      <div className="mt-1.5 h-1.5 w-full overflow-hidden rounded-full bg-[color:var(--border)]">
        <div
          className="h-full rounded-full transition-[width] duration-500"
          style={{ width: `${pct}%`, background: bar }}
        />
      </div>
      {hint ? (
        <p className="mt-1 text-[11.5px] text-[color:var(--text-muted)]">
          {hint}
        </p>
      ) : null}
    </div>
  );
};

/* ------------------------------------------------------------------ *
 * ProcessStepper -- the ordered stages of a lifecycle, current one
 * marked. Use ONLY when the status field is a sequence; a flat set of
 * independent flags (Active / VIP / Interpreter required) is chips, and
 * a stepper there invents an order that does not exist (SS 6.8).
 * ------------------------------------------------------------------ */

export const ProcessStepper = ({
  stages,
  current,
}: {
  stages: string[];
  current: string;
}) => {
  const at = Math.max(0, stages.indexOf(current));
  return (
    <ol className="flex flex-wrap items-center gap-x-1 gap-y-2">
      {stages.map((stage, i) => {
        const done = i < at;
        const now = i === at;
        return (
          <li key={stage} className="flex items-center gap-1">
            <span
              className={
                'inline-flex items-center gap-2 rounded-full py-1 pl-1 pr-3 ' +
                (now
                  ? 'bg-[color:var(--color-brand-50)]'
                  : 'bg-transparent')
              }
            >
              <span
                className={
                  'grid h-5 w-5 shrink-0 place-items-center rounded-full text-[10.5px] font-bold tabular-nums ' +
                  (done
                    ? 'bg-[color:var(--color-brand-500)] text-white'
                    : now
                      ? 'bg-[color:var(--color-brand-500)] text-white ring-4 ring-[color:var(--color-brand-100)]'
                      : 'bg-[color:var(--border)] text-[color:var(--text-muted)]')
                }
              >
                {done ? '\u2713' : i + 1}
              </span>
              <span
                className={
                  'whitespace-nowrap text-[12.5px] ' +
                  (now
                    ? 'font-semibold text-[color:var(--color-brand-700)]'
                    : done
                      ? 'text-[color:var(--text-sub)]'
                      : 'text-[color:var(--text-faint)]')
                }
              >
                {stage}
              </span>
            </span>
            {i < stages.length - 1 && (
              <span
                aria-hidden
                className={
                  'h-px w-6 shrink-0 ' +
                  (done
                    ? 'bg-[color:var(--color-brand-300)]'
                    : 'bg-[color:var(--border)]')
                }
              />
            )}
          </li>
        );
      })}
    </ol>
  );
};

/* ------------------------------------------------------------------ *
 * ActivityFeed -- timestamp, actor and the transition. A record with a
 * history that shows none reads as stored rather than alive (SS 6.7).
 * ------------------------------------------------------------------ */

export const ActivityFeed = ({
  events,
}: {
  events: {
    at: string;
    actor?: string;
    label: ReactNode;
    from?: string;
    to?: string;
  }[];
}) => (
  <ol className="space-y-3.5">
    {events.map((e, i) => (
      <li key={i} className="flex gap-3">
        <span className="relative flex flex-col items-center">
          <span className="mt-1.5 h-2 w-2 shrink-0 rounded-full bg-[color:var(--color-brand-500)]" />
          {i < events.length - 1 && (
            <span className="mt-1 w-px flex-1 bg-[color:var(--border)]" />
          )}
        </span>
        <div className="min-w-0 pb-0.5">
          <div className="flex flex-wrap items-center gap-x-2 gap-y-1">
            <span className="text-[13px] font-medium text-[color:var(--text-strong)]">
              {e.label}
            </span>
            <span className="text-[11.5px] tabular-nums text-[color:var(--text-muted)]">
              <DateText value={e.at} />
            </span>
            {e.actor ? (
              <span className="text-[11.5px] text-[color:var(--text-muted)]">
                · {e.actor}
              </span>
            ) : null}
          </div>
          {e.from && e.to ? (
            <div className="mt-1 flex items-center gap-1.5">
              <StatusChip label={e.from} />
              <span className="text-[color:var(--text-faint)]">&rarr;</span>
              <StatusChip label={e.to} />
            </div>
          ) : null}
        </div>
      </li>
    ))}
  </ol>
);
