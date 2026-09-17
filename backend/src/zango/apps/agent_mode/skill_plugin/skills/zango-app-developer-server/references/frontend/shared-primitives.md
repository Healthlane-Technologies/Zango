# `shared.tsx` — the primitives every custom page composes from

Write this file **first**, before any detail page or dashboard. Every other
custom page imports from it. See [design-system.md](design-system.md) §4 for
why this is mandatory rather than an optimisation.

This is a **floor, not a template to transcribe.** Adapt the anatomy to the app
you were asked to build — add an avatar to `PageHeader` if entities have one,
add a `Sparkline` if the dashboard needs one, drop what the app has no use for.
What must survive adaptation: primitives defined once at module scope, theme
tokens instead of hexes, Tailwind classes instead of inline styles, and all
four states from §3.

Two things to check against the real scaffold before you rely on them: the
`@zango-core/crud/table` exports you import, and the exact theme variable names
the initializer set. Both are documented in
[appbuilder.md](appbuilder.md) and [crud.md](crud.md).

---

## The file

```tsx
// src/custom/pages/shared.tsx
//
// Shared UI primitives. Everything here is module scope and defined exactly
// once -- components defined inside a render are remounted on every parent
// render, which makes CrudHandler lose its state (see entity-360.md §5).

import { ReactNode } from 'react';
import { useNavigate } from 'react-router-dom';
import { TableBody } from '@zango-core/crud/table';

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

export const Money = ({ value }: { value: any }) => {
  if (value === null || value === undefined || value === '') return <>&mdash;</>;
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
  if (!value) return <>&mdash;</>;
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

/* The app already renders inside the platform's sidebar shell, so the content
 * area is roughly `viewport - 260px`. A narrow cap here strands the rest as an
 * empty grey band: a 1080px cap on a 1920px screen left ~640px of unused page
 * beside a detail view. `max-w-[1600px]` fills a laptop and still stops lines
 * from running to absurd lengths on an ultrawide. */
export const PageShell = ({ children }: { children: ReactNode }) => (
  <div className="min-h-full bg-[color:var(--color-gray-50)]">
    <div className="mx-auto w-full max-w-[1600px] px-4 py-6 md:px-6">{children}</div>
  </div>
);

export const Card = ({
  children,
  tinted = false,
  tone,
  className = '',
}: {
  children: ReactNode;
  tinted?: boolean;
  tone?: 'good' | 'warn' | 'bad' | 'info';
  className?: string;
}) => {
  /* `tone` carries meaning -- a monitoring block that is healthy, a
     warning that needs action. Never use it for decoration: an
     app where every card is tinted has no emphasis left to spend. */
  const toned = tone
    ? {
        good: 'border-[color:var(--color-green-200,#bbf7d0)] bg-[color:var(--color-green-50,#f0fdf4)]',
        warn: 'border-[color:var(--color-amber-200,#fde68a)] bg-[color:var(--color-amber-50,#fffbeb)]',
        bad: 'border-[color:var(--color-red-200,#fecaca)] bg-[color:var(--color-red-50,#fef2f2)]',
        info: 'border-[color:var(--color-brand-200)] bg-[color:var(--color-brand-50)]',
      }[tone]
    : tinted
      ? 'border-[color:var(--color-brand-200)] bg-[color:var(--color-brand-50)]'
      : 'border-[color:var(--color-gray-200)] bg-white';

  return (
    <div
      className={
        'rounded-xl border p-4 shadow-[0_1px_2px_rgba(16,24,40,0.04)] ' +
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
        good: 'border-[color:var(--color-green-200,#bbf7d0)] bg-[color:var(--color-green-50,#f0fdf4)]',
        warn: 'border-[color:var(--color-amber-200,#fde68a)] bg-[color:var(--color-amber-50,#fffbeb)]',
        bad: 'border-[color:var(--color-red-200,#fecaca)] bg-[color:var(--color-red-50,#fef2f2)]',
        info: 'border-[color:var(--color-brand-200)] bg-[color:var(--color-brand-50)]',
      }[tone]
    : 'border-[color:var(--color-gray-200)] bg-[color:var(--color-gray-50)]';
  return (
    <div className={'rounded-lg border p-3.5 ' + toned + ' ' + className}>
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
    neutral: 'bg-[color:var(--color-gray-400)]',
    good: 'bg-[color:var(--color-green-500,#22c55e)]',
    warn: 'bg-[color:var(--color-amber-500,#f59e0b)]',
    bad: 'bg-[color:var(--color-red-500,#ef4444)]',
  }[tone];
  const txt = {
    neutral: 'text-[color:var(--color-gray-600)]',
    good: 'text-[color:var(--color-green-700,#15803d)]',
    warn: 'text-[color:var(--color-amber-700,#b45309)]',
    bad: 'text-[color:var(--color-red-700,#b91c1c)]',
  }[tone];
  return (
    <div className="rounded-lg border border-[color:var(--color-gray-200)] bg-white p-3.5">
      <span className="block text-[10.5px] font-semibold uppercase tracking-[0.07em] text-[color:var(--color-gray-500)]">
        {label}
      </span>
      <div className="mt-1.5 flex items-baseline justify-between gap-2">
        <span className="text-[19px] font-semibold tabular-nums tracking-[-0.02em] text-[color:var(--color-gray-900)]">
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
        <span className="mt-1 block text-[11.5px] text-[color:var(--color-gray-500)]">
          {hint}
        </span>
      ) : null}
    </div>
  );
};

export const SectionTitle = ({ children }: { children: ReactNode }) => (
  <h2 className="mb-3 text-[16px] font-semibold text-[color:var(--color-gray-900)]">
    {children}
  </h2>
);

/* Small uppercase eyebrow label. The one place ALL-CAPS is allowed. */
export const Eyebrow = ({ children }: { children: ReactNode }) => (
  <span className="text-[11px] font-semibold uppercase tracking-[0.07em] text-[color:var(--color-gray-500)]">
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
    <div className="mb-4 border-b border-[color:var(--color-gray-200)] pb-4">
      {backLabel && (
        <button
          type="button"
          onClick={() => navigate(-1)}
          className="mb-2 rounded text-[13px] text-[color:var(--color-gray-500)] transition-colors hover:text-[color:var(--color-gray-900)] focus-visible:outline focus-visible:outline-2 focus-visible:outline-[color:var(--color-brand-500)]"
        >
          &larr; {backLabel}
        </button>
      )}
      <div className="flex flex-wrap items-center gap-3">
        {avatar}
        <h1 className="text-[20px] font-bold tracking-[-0.02em] text-[color:var(--color-gray-900)] md:text-[24px]">
          {title}
        </h1>
        {reference && (
          <span className="font-mono text-[12px] text-[color:var(--color-gray-500)]">
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
    neutral: 'bg-[color:var(--color-gray-100)] text-[color:var(--color-gray-700)]',
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
        <div className="col-span-2 rounded-xl border border-[color:var(--color-brand-200)] bg-[color:var(--color-brand-50)] p-4">
          <span className="block text-[10.5px] font-semibold uppercase tracking-[0.07em] text-[color:var(--color-gray-500)]">
            {labelOf(anchorField, anchor!.key)}
          </span>
          <span className="mt-1 block text-[25px] font-bold leading-none tracking-[-0.025em] tabular-nums text-[color:var(--color-brand-700)]">
            {render?.[anchor!.key]
              ? render[anchor!.key](anchorField.value)
              : (anchorField.value ?? <>&mdash;</>)}
          </span>
          {anchor!.sub && (
            <span className="mt-1.5 block text-[11px] text-[color:var(--color-gray-500)]">
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
            className="rounded-xl border border-[color:var(--color-gray-200)] bg-white p-3.5"
          >
            <span className="block text-[10.5px] font-semibold uppercase tracking-[0.07em] text-[color:var(--color-gray-500)]">
              {labelOf(f, k)}
            </span>
            <span className="mt-1 block text-[15px] font-semibold tabular-nums text-[color:var(--color-gray-900)]">
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
            <span className="block text-[10.5px] font-semibold uppercase tracking-[0.07em] text-[color:var(--color-gray-500)]">
              {labelOf(f, k)}
            </span>
            <span className="mt-0.5 block break-words text-[13.5px] text-[color:var(--color-gray-900)]">
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
    className="flex gap-5 overflow-x-auto border-b border-[color:var(--color-gray-200)] text-[13px]"
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
              ? 'border-[color:var(--color-brand-500)] font-semibold text-[color:var(--color-gray-900)]'
              : 'border-transparent text-[color:var(--color-gray-500)] hover:text-[color:var(--color-gray-900)]')
          }
        >
          {it.label}
          {typeof it.count === 'number' && (
            <span className="ml-1.5 rounded bg-[color:var(--color-gray-100)] px-1.5 py-0.5 text-[11px] tabular-nums text-[color:var(--color-gray-600)]">
              {it.count}
            </span>
          )}
        </button>
      );
    })}
  </div>
);

/* ------------------------------------------------------------------ *
 * The four states (design-system.md §3)
 * ------------------------------------------------------------------ */

export const Skeleton = ({ className = '' }: { className?: string }) => (
  <div
    className={
      'animate-pulse rounded bg-[color:var(--color-gray-100)] ' + className
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
      className="mb-3 h-12 w-12 text-[color:var(--color-gray-300)]"
      aria-hidden="true"
    >
      <path d="M3 7h18M3 12h18M3 17h10" />
    </svg>
    <h3 className="text-[15px] font-semibold text-[color:var(--color-gray-900)]">{title}</h3>
    {description && (
      <p className="mt-1 max-w-[320px] text-[13px] text-[color:var(--color-gray-500)]">
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
    <p className="mt-1 max-w-[320px] text-[13px] text-[color:var(--color-gray-500)]">
      {message}
    </p>
    {onRetry && (
      <button
        type="button"
        onClick={onRetry}
        className="mt-4 rounded-lg border border-[color:var(--color-gray-300)] bg-white px-3 py-1.5 text-[13px] font-medium transition-colors hover:bg-[color:var(--color-gray-50)]"
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
  <section className="mb-4 rounded-xl border border-[color:var(--color-gray-200)] bg-white shadow-[0_1px_2px_rgba(16,24,40,0.05)]">
    <header className="flex items-center gap-3 border-b border-[color:var(--color-gray-100)] px-4 py-3">
      <h2 className="text-[12.5px] font-semibold text-[color:var(--color-gray-700)]">{title}</h2>
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
      'rounded-lg px-3 py-1.5 text-[12.5px] font-medium transition-colors focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-1 focus-visible:outline-[color:var(--color-brand-500)] ' +
      (variant === 'primary'
        ? 'bg-[color:var(--color-brand-500)] text-white hover:bg-[color:var(--color-brand-700)]'
        : 'border border-[color:var(--color-gray-300)] bg-white text-[color:var(--color-gray-700)] hover:bg-[color:var(--color-gray-50)]')
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
        className="inline-flex items-center gap-1.5 text-[12.5px] text-[color:var(--color-gray-600)]"
      >
        {it.icon ? (
          <span className="text-[color:var(--color-gray-400)]">{it.icon}</span>
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
  children,
}: {
  title: string;
  icon?: ReactNode;
  count?: number;
  children: ReactNode;
}) => (
  <section className="rounded-xl border border-[color:var(--color-gray-200)] bg-white">
    <header className="flex items-center gap-2 px-4 pb-2 pt-3.5">
      {icon ? (
        <span className="text-[color:var(--color-gray-400)]">{icon}</span>
      ) : null}
      <h3 className="text-[13.5px] font-semibold tracking-[-0.01em] text-[color:var(--color-gray-900)]">
        {title}
      </h3>
      {typeof count === 'number' && (
        <span className="rounded-md bg-[color:var(--color-gray-100)] px-1.5 py-0.5 text-[11px] font-semibold tabular-nums text-[color:var(--color-gray-600)]">
          {count}
        </span>
      )}
    </header>
    <div className="px-4 pb-4 text-[13px] text-[color:var(--color-gray-700)]">
      {children}
    </div>
  </section>
);

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
        <span className="mt-[1px] text-[color:var(--color-gray-400)]">
          {it.icon}
        </span>
        <span className="min-w-0 text-[13px] text-[color:var(--color-gray-700)]">
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
    good: 'var(--color-green-600, #16a34a)',
    warn: 'var(--color-amber-500, #f59e0b)',
    bad: 'var(--color-red-600, #dc2626)',
  }[tone];
  return (
    <div>
      <div className="flex items-baseline justify-between gap-3">
        <span className="text-[13px] text-[color:var(--color-gray-800)]">
          {label}
        </span>
        {right ? (
          <span className="text-[12.5px] tabular-nums text-[color:var(--color-gray-600)]">
            {right}
          </span>
        ) : null}
      </div>
      <div className="mt-1.5 h-1.5 w-full overflow-hidden rounded-full bg-[color:var(--color-gray-200)]">
        <div
          className="h-full rounded-full transition-[width] duration-500"
          style={{ width: `${pct}%`, background: bar }}
        />
      </div>
      {hint ? (
        <p className="mt-1 text-[11.5px] text-[color:var(--color-gray-500)]">
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
                      : 'bg-[color:var(--color-gray-200)] text-[color:var(--color-gray-500)]')
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
                      ? 'text-[color:var(--color-gray-700)]'
                      : 'text-[color:var(--color-gray-400)]')
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
                    : 'bg-[color:var(--color-gray-200)]')
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
            <span className="mt-1 w-px flex-1 bg-[color:var(--color-gray-200)]" />
          )}
        </span>
        <div className="min-w-0 pb-0.5">
          <div className="flex flex-wrap items-center gap-x-2 gap-y-1">
            <span className="text-[13px] font-medium text-[color:var(--color-gray-900)]">
              {e.label}
            </span>
            <span className="text-[11.5px] tabular-nums text-[color:var(--color-gray-500)]">
              <DateText value={e.at} />
            </span>
            {e.actor ? (
              <span className="text-[11.5px] text-[color:var(--color-gray-500)]">
                · {e.actor}
              </span>
            ) : null}
          </div>
          {e.from && e.to ? (
            <div className="mt-1 flex items-center gap-1.5">
              <StatusChip value={e.from} />
              <span className="text-[color:var(--color-gray-400)]">&rarr;</span>
              <StatusChip value={e.to} />
            </div>
          ) : null}
        </div>
      </li>
    ))}
  </ol>
);
```

---

## Card treatments — pick one per block, never the same one five times

**This is the section that decides whether the page looks designed.** A real
run composed a whole detail page from five `Section`s, which is structurally
correct and renders as five identical white boxes with grey title bars — a
wireframe. `Section` is the *plainest* treatment, not the default one.

Choose per block:

### A. `Section` — a plain group of fields

The floor. Use for secondary field groups only, never for the lead block.

```tsx
<Section title="Patient & policy">
  <FieldGrid fields={fields} keys={['patient', 'tpa_name', 'policy_number']} />
</Section>
```

### B. `Card` + `Inset` — the lead card (the one that carries the page)

A card whose sub-blocks sit on their own quiet fill. **The nesting is the
single biggest contributor to perceived quality** — one level of `Inset`
separates "designed" from "boxes".

```tsx
<Card className="mb-4">
  <div className="mb-3 flex items-center justify-between">
    <SectionTitle>Billing summary</SectionTitle>
    <StatusChip label="Partially approved" tone="warn" />
  </div>

  <Meter label="Amount billed"   value={billed}   max={billed} />
  <Meter label="Amount approved" value={approved} max={billed} tone="good" />

  <div className="mt-4 grid max-md:grid-cols-1 gap-3 md:grid-cols-3">
    <MetricTile label="Paid by TPA"  value={<Money value={paid} />}
                qualifier="1 of 3 instalments" tone="warn" />
    <MetricTile label="Outstanding"  value={<Money value={outstanding} />}
                qualifier="Awaiting TPA"       tone="bad" />
    <MetricTile label="Approved"     value={`${pct}%`}
                qualifier="of billed"          tone="good" />
  </div>

  <Inset className="mt-3" tone="warn">
    <b>Pending documents</b> — the discharge summary has not been uploaded.
  </Inset>
</Card>
```

### C. `Card tone=` — a block whose whole meaning is its status

```tsx
<Card tone="bad">
  <SectionTitle>Rejected by TPA</SectionTitle>
  <p className="text-[13px] text-[color:var(--color-gray-700)]">
    Policy lapsed before the admission date. Re-submit under the new policy.
  </p>
</Card>
```

**Never tint for decoration.** Most cards on a page stay plain white; a tint
that appears everywhere stops meaning anything.

### D. `RailCard` — right-rail blocks

Quieter than a main-column card: smaller title, optional count.

```tsx
<RailCard title="At a glance">
  <AtAGlance items={[
    { text: `Patient: ${fields.patient?.value ?? '—'}` },
    { text: `TPA: ${fields.tpa_name?.value ?? '—'}` },
  ]} />
</RailCard>

<RailCard title="Needs attention" count={openItems.length}>
  {openItems.length === 0
    ? <span className="text-[13px] text-[color:var(--color-gray-500)]">No open items right now.</span>
    : openItems.map((i) => <div key={i.key} className="text-[13px]">{i.text}</div>)}
</RailCard>
```

### The composition rule

On any detail page: **exactly one** B (the lead card), zero or one C, as many A
and D as the content needs. If your page has no B, it has no anchor — and that
is the page that reads as a wireframe no matter how correct the data is.

### Numbers never travel alone

`MetricTile` takes a `qualifier` and a `tone` for a reason. `₹0.00` is data;
`₹0.00 · Awaiting TPA` is the answer the page exists to give. **A row of bare
numbers is the wireframe look.** If you cannot write a qualifier for a number,
ask whether that number belongs on the page at all.

---

## Using them

A detail page is composition. Note the treatment mix — **one `Card` lead block
with `Inset` and `MetricTile` inside it**, a right rail of `RailCard`s, and
`Section` only for the plain field groups underneath. A page built from
`Section` alone is the known wireframe failure:

```tsx
import { useState } from 'react';
import { CrudHandler } from '@zango-core/crud/table';
import {
  PageShell, PageHeader, KeyFacts, FieldGrid, Section, Tabs,
  Card, Inset, MetricTile, Meter, DetailLayout, RailCard, AtAGlance,
  SectionTitle, Avatar, Button, StatusChip, EmptyState, DetailSkeleton, Money,
} from './shared';

const CHILD_TABS = [
  { key: 'appointments',  label: 'Appointments',  endpoint: '/appointments/appointments/',   param: 'patient_uuid' },
  { key: 'bills',         label: 'Bills',         endpoint: '/bills/bills/',                 param: 'patient_uuid' },
];

const KEY_FACTS = ['outstanding', 'age', 'gender', 'phone'];

const PatientDetail = ({ data, generalDetails, objectUuid }: any) => {
  const [tab, setTab] = useState('overview');
  if (!data) return <PageShell><DetailSkeleton /></PageShell>;

  const fields = generalDetails?.fields || {};
  const counts = data?.child_counts || {};   // when the backend supplies them

  return (
    <PageShell>
      <PageHeader
        title={data.title}
        backLabel="Patients"
        avatar={<Avatar name={data.title} />}
        reference={fields.patient_id?.value}
        status={<StatusChip label="Active" tone="success" />}
        actions={<><Button>Edit</Button><Button variant="primary">Book appointment</Button></>}
      />

      {/* ONE fact dominates -- never four equal values */}
      <KeyFacts
        fields={fields}
        keys={KEY_FACTS}
        anchor={{ key: 'outstanding', sub: '2 unpaid bills' }}
        render={{ outstanding: (v) => <Money value={v} /> }}
      />

      <Tabs
        value={tab}
        onChange={setTab}
        items={[
          { key: 'overview', label: 'Overview' },
          ...CHILD_TABS.map((t) => ({ ...t, count: counts[t.key] })),
        ]}
      />

      <div className="pt-4">
        {tab === 'overview' ? (
          <DetailLayout
            rail={
              <>
                <RailCard title="At a glance">
                  <AtAGlance items={[
                    { text: `Phone: ${fields.phone?.value ?? '—'}` },
                    { text: `Registered: ${fields.created_at?.value ?? '—'}` },
                  ]} />
                </RailCard>
                <RailCard title="Needs attention" count={openItems.length}>
                  {openItems.length === 0
                    ? <span className="text-[13px] text-[color:var(--color-gray-500)]">
                        No open items right now.
                      </span>
                    : openItems.map((i) => <div key={i} className="text-[13px]">{i}</div>)}
                </RailCard>
              </>
            }
          >
            {/* THE LEAD CARD -- one per page, and the reason the page exists.
                Nested Inset + qualified MetricTiles are what make it read as
                designed rather than as another white box. */}
            <Card>
              <div className="mb-3 flex items-center justify-between">
                <SectionTitle>Outstanding balance</SectionTitle>
                <StatusChip label="2 unpaid bills" tone="warn" />
              </div>

              <Meter label="Billed"  value={billed} max={billed} />
              <Meter label="Settled" value={settled} max={billed} tone="good" />

              <div className="mt-4 grid max-md:grid-cols-1 gap-3 md:grid-cols-3">
                <MetricTile label="Outstanding" value={<Money value={outstanding} />}
                            qualifier="across 2 bills" tone="bad" />
                <MetricTile label="Settled" value={<Money value={settled} />}
                            qualifier="last on 12 Aug" tone="good" />
                <MetricTile label="Appointments" value={counts.appointments ?? '—'}
                            qualifier="1 upcoming" />
              </div>

              {overdue ? (
                <Inset className="mt-3" tone="warn">
                  <b>Payment overdue</b> — the oldest unpaid bill is 34 days old.
                </Inset>
              ) : null}
            </Card>

            {/* Plain groups stay plain -- Section is correct HERE, not above. */}
            <Section title="Patient details">
              <FieldGrid fields={fields} keys={['name', 'phone', 'age', 'gender', 'address']} />
            </Section>
            <Section title="Clinical notes">
              <FieldGrid fields={fields} keys={['allergies', 'conditions']} />
            </Section>
          </DetailLayout>
        ) : (
          (() => {
            const t = CHILD_TABS.find((x) => x.key === tab)!;
            if (counts[t.key] === 0) {
              return (
                <Section title={t.label}>
                  <EmptyState
                    title={`No ${t.label.toLowerCase()} yet`}
                    description={`${t.label} for this patient will appear here.`}
                  />
                </Section>
              );
            }
            return (
              <CrudHandler
                api_endpoint={`${t.endpoint}?${t.param}=${objectUuid}`}
                headerProps={{ title: t.label }}
              />
            );
          })()
        )}
      </div>
    </PageShell>
  );
};

export default PatientDetail;
```

What makes this finished rather than a wireframe: an identity block with an
avatar and real actions, **one `Card` lead block carrying nested `Inset`s and
qualified `MetricTile`s**, a right rail, grouped `Section`s underneath, tab
counts, and an empty state per tab.

Strip those and you get a title, three floating values and a tab strip — which
passes every token rule and still looks unbuilt. **The specific regression to
avoid: composing the whole page from `Section`.** It is the plainest treatment
and the easiest to reach for, so a page built only from it satisfies every rule
in this file and still renders as five identical grey-capped boxes.

> **Field labels: read `name`, not `display_name`.** The detail API returns
> each field as `{type, name, value, …}` — there is no `display_name` key on
> it. A primitive that reads only `display_name` renders every label blank,
> which is how a key-facts strip becomes unlabelled floating numbers. The
> `KeyFacts`/`FieldGrid` above try `display_name → label → name → the key`, so
> they survive either shape. **Open the page and confirm the labels are
> visible** before moving on.

## Checklist

- [ ] `shared.tsx` written **before** the first detail page
- [ ] `LOCALE` and `CURRENCY` inferred from context and recorded as an assumption
- [ ] Every primitive at module scope, none defined inside a render
- [ ] No page re-implements `Tabs`, `KeyFacts`, `PageHeader` or a skeleton
- [ ] Skeletons shape-matched; `EmptyState` used per tab and per table
- [ ] No literal hex anywhere in `src/custom/`
