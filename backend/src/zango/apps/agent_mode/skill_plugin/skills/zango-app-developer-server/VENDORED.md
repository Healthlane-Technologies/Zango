# Vendored skill — provenance and delta

**Source:** `~/.claude/skills/zango-app-developer/` (user-level Claude Code skill)
**Vendored:** 2026-09-10
**Vendored as:** `zango-agent-mode:zango-app-developer-server`

The interactive skill runs on a developer's laptop with Docker, a human to
answer questions, and a Node toolchain. None of those exist in server mode, so
this copy is a fork rather than a mirror.

## Delta from the source

### SKILL.md — rewritten (406 → ~190 lines)

| Source section | Change |
|---|---|
| Capability 1 — Bootstrap Docker environment | **Deleted.** The platform is already running. `references/bootstrap-templates.md` deleted with it. |
| Post-Bootstrap: Create App | **Deleted.** The app exists before the run starts. |
| Capability 3 — App Panel API automation | **Deleted.** It authenticated with platform admin credentials via a curl cookie jar; the agent must never hold those. `references/app-panel-api.md` is kept as reference only. |
| STEP 1 — Discover Context | Replaced: the run-context block in the prompt is authoritative; discovery is confined to the workspace. |
| STEP 3 — Create Roles | The agent now *names* required roles in its summary instead of creating them (role creation needs platform credentials). |
| STEP 4 (planning) — "ask the user" throughout | Converted to "decide, and record the assumption". This is the single most important edit: a headless run that tries to ask burns turns and then guesses anyway. The UX decision tables are kept — they are the most valuable part of the skill. |
| Two sections both numbered **STEP 4** | Renumbered. This was a bug in the source. |
| STEP 5 — Post-Implementation (`docker compose exec … ws_makemigration / ws_migrate / update-apps`, Celery restart) | Replaced with a hand-off: the platform runs the sequence and reports each step. |
| STEP 5 — Frontend setup (`npx @zango-core/create-zango-app`, `npm run build:zango`) | **Deleted.** No Node in the platform container. The agent implements the backend plus a CRUD route and describes remaining React work. |
| STEP 6 — Verify (`docker compose logs`) | Replaced: report what to verify. |
| STEP 7 — Create Test Users | **Deleted** (needs platform credentials). |
| Capability 4 — Frontend Reference | Kept as reference so existing React sources can still be edited coherently; the build step is gone. |
| Critical Rules | Kept verbatim apart from the docker-logs debugging line. These rules are the highest-value part of the skill. |

### references/ — kept, with two bug fixes and five banners

Otherwise byte-identical to the source, so upstream diffs stay reviewable.

**Bugs fixed** (both present in the source and verified against this repo):

1. `templates/app-module/README.md` told the agent to run
   `zango manage-app <app> sync_policies`. **No such CLI command exists** — the
   registered commands are `start-project`, `list-packages`, `install-package`,
   `git-setup`, `update-apps`. Replaced with a note pointing at `ws_sync`.
2. `zango-architecture.md` listed `urls_tenant.py`; the real project-template
   file is `urls_tenants.py` (plural).

**Server-mode banners** prepended to the five files whose commands cannot run
here (`core/models.md`, `core/async-tasks.md`, `app-panel-api.md`,
`templates/app-module/README.md`, `frontend/appbuilder.md`) rather than
deleting content that remains useful as background.

### Known divergences left alone

- The source lists packages `appbuilder`/`crud`/`workflow`/`communication`,
  while `examples/tutorial_app/` in this repo still references the legacy
  `frame`/`login` packages. The modern set is correct.

## 2026-09-17 — correctness gates, SVG icons, treatment library (v1.5.0)

v1.4.0 gave the agent ambition. Live runs on `wapp5`/`wapp6`/`wapp7` then showed
that the remaining failures were not ambition but **three blind spots**: pages
that were confidently wrong, steps that failed silently and got reported as
done, and a component vocabulary the agent never reached for. Every item below
came from a page rendered in a browser, not from review.

| Problem | Fix |
|---|---|
| **A detail page rendered `₹0.00` for every amount while the record held ₹1000/₹100 (`wapp7`).** `BaseDetail` with no `Meta.fields` makes `get_general_details` fall back to **the table's columns** — and `ClaimTable` never carried `amount_billed`. The page read `undefined`, and a `toNum` helper mapping `undefined → 0` turned "the server never sent this" into "the value is zero". HTTP 200, no warning, and the missing "Amounts" section read as a *styling* problem, which hid the data bug. | New entity-360.md **§3b** with the framework source, the `Meta.sections` signature trap (`get_sections(self, obj)` is never called — the framework calls `get_sections(self.Meta.sections)`), and a right/wrong `toNum` where absent stays `null` and renders `—`. New gate: **open one record and check the page against the stored values**. Gate 20 could not catch this — when every derived number is `0` the page is internally consistent and uniformly wrong. |
| **Routes and menus repeatedly ended up empty, and the agent reported success anyway.** Four distinct failures all return `success: true`: route ids invented rather than read back from the save response; menus posted before routes; icons silently replaced; a role skipped because `get_available_roles` shrinks as configs are created and a cached loop stops early. | 5h rewritten around **the sequence that works** — save routes, read back the server-generated ids, resolve the numeric role id, post one config per role, then read *both* back and check values rather than status codes. A failure is now explicitly **a blocker, not an outstanding item**: the observed pattern was filing it as a remaining task inside a summary that otherwise read as success, leaving an app whose sidebar is empty or entirely dead links. |
| **Emoji icons.** `clean_icon()`'s second branch discards any icon containing `�` for the grey `📄`. Emoji are multi-byte and need only one mis-encoded hop — a heredoc, JSON written without `ensure_ascii=False`, `curl -d` under a non-UTF-8 locale — to arrive corrupted. The POST still returns `success: true`. | **Inline SVG only, never emoji**, with the source branch quoted. The references were actively contradicting this: `api-configuration.md` said "SVG string ONLY — no emoji" on one line and "**Emoji are valid here** (menus)" forty lines later, with a dozen emoji examples to copy. **16 emoji examples replaced with real SVG** across five files, plus two icon-*name* examples that silently render as a broken `<img>`. |
| **The login left panel shipped with three children and 31% fill** — brandmark, headline, footer, with two ~265px dead gaps. §5's ASCII sketch showed a stepper and value rows; nothing made them binding. | auth-login.md **§5b**: a JS snippet returning `{count, fill}` and three numeric gates (≥4 children, ≥50% fill, no gap >120px), a mandatory **middle band**, and copy-paste CSS for the layered background and the `justify-content:center` + absolutely-positioned brandmark/footer that closes the gaps. |
| **A detail page composed from five `Section`s (`wapp7`)** — structurally correct, and rendered as five identical white boxes with grey title bars. The primitives for better (`Card`, `Inset`, `MetricTile`) were written and shipped, and used **zero** times. | Root cause: **the only complete worked example in `shared-primitives.md` used `Section` twice and `Card`/`Inset`/`MetricTile` zero times.** The agent copied what it was shown. Added a **card-treatment library** (A `Section` plain group / B `Card`+`Inset`+`MetricTile` lead card / C `Card tone=` status / D `RailCard`) with the composition rule *exactly one B per detail page*, and rewrote the worked example to lead with B. |
| **~640px of empty grey beside a detail page on a 1920px screen.** `PageShell` capped content at 1080px while the usable area is `viewport − 260`; the rail was also stranded at 331px against a 713px main column. | `PageShell` widened to `max-w-[1600px]`, with a design-system.md rule covering both causes and a snippet checking content width against the usable area and the rail-to-main height ratio (≥0.6). The reference PSP page fills 1598px of 1920 and runs 1433px tall. |
| **SKILL.md had grown to 1005 lines**, 656 of them STEP 5 — the references exist precisely so it stays an orchestration document. | Cut to ~780. The 5h call sequence moved to `api-configuration.md`; the 23-item gate moved to a new `references/frontend/verify-gate.md` (now 24 items). No block exceeds 84 lines. |

**Lesson, and it is the same one as v1.3.0 one level up.** v1.3.0 learned that *a
visual rule that exists only as prose does not reach the output — it has to be
in the primitive*. This round learned the sequel: **when a rule and an example
disagree, the example wins.** `Card`, `Inset` and `MetricTile` were in the
primitives, documented, and described in prose as required — and were used zero
times, because the one copyable page composed itself from `Section`. Adding
rules would not have fixed that. Changing the example is what fixes it.

The corollary for verification: several of these failures return HTTP 200 and
look correct. Gates that compare the page to itself cannot see them. The gates
that matter compare the page to **the stored data**, to **a read-back from the
server**, and to **measured geometry**.

## 2026-09-17 — ambition ported, constraints corrected (v1.4.0)

v1.3.0 made polish *checkable* and got exactly what a checklist produces: pages
that clear every bar and still look like wireframes. Checklists prevent bad
output; they do not produce good output.

**The constraints were also factually wrong**, which suppressed most of what
makes UI look premium. Verified in this repo, not assumed:

| Previously claimed | Reality |
|---|---|
| "No icon library — inline SVG only" | `lucide-react` is **already installed** transitively via `@zango-core` (4 copies in the lockfile). A probe component importing it typechecks clean. Zero install needed. |
| "No external fonts — CDN blocked" | **No CSP exists anywhere in the codebase.** The platform's own `frontend/src/index.css` imports Google Fonts. `fonts.googleapis.com` returns 200. |
| "No new packages" | True, and kept — but now with a vetted allowlist. |

| Change | Detail |
|---|---|
| **Reference standard** | New opening section naming Linear / Stripe Dashboard / Vercel / Notion / Height / Mercury as the bar, with three self-check questions. Replaces "polished", which meant nothing. States plainly that the rules are a floor and a page satisfying all of them can still be unfinished — with the observed wireframe described. |
| **§0 design brief expanded** | Six questions including a per-page anchor and an explicit aesthetic direction. Adds **"the one deliberate moment"** — every app gets one element executed with real care, and you must be able to point at it. |
| **§1a aesthetic direction (new)** | Four directions — Operational / Editorial / Clinical / Approval — each with surface, type, density and a signature treatment. Without this every Zango app is the same grey-and-indigo CRUD shell, since the brand colour is fixed by the theme. Also requires deciding where colour appears beyond status pills. |
| **§10 rewritten** | Icons: import `lucide-react`, one size and stroke width per context. Type: Inter variable (`opsz`, weights 450/530/575) + JetBrains Mono for IDs, loaded from Google Fonts with a real fallback. Charts: approved libraries only, with a note that a CSS bar or inline sparkline often beats importing one. |
| **Guard relaxed (`guards.py`)** | `_NPM_DESIGN_PACKAGES` allows `install`/`i`/`add` of exactly: echarts, echarts-for-react, recharts, date-fns, clsx, tailwind-merge (optionally `@`-pinned, multiple per command). The package **name** stays the security boundary, since `npm install` runs lifecycle scripts. Verified: 6 allow cases pass, 7 escape attempts (`left-pad`, a bad name mixed with a good one, `../local-evil`, `-g`, `;`-chaining, `exec`, `run postinstall`) all denied. The `&&`-chaining gap is pre-existing and unrelated — confirmed by stashing the change. |
| Checklist | Split into Design (judged by looking) vs Structure/States/Style/Content/Constraints (greppable). Leads with the judgement items. |
| Contradictions removed | SKILL.md 5a, `auth-login.md` styling constraints and `prompt.py`'s `frontend_rule` all repeated the false "no fonts, no icons" claim; each now points at §10. |

Open: none of this is proven in a run yet. The bar is higher and the tools are
actually available; whether output reaches it needs a real build to confirm.

## 2026-09-17 — polish made checkable, not aspirational (v1.3.0)

v1.2.0 fixed the pipeline: `wapp3` built a real frontend, deployed its own
bundle and wrote the correct `app.html`. All six gates passed. The result was
still visibly unfinished, and testing the flow surfaced two backend bugs the
skill had not warned about.

Observed in `wapp3` (Distribution Manager):

- Four detail pages, each ~80-100 lines, were the `entity-360.md` §7 skeleton
  transcribed with its Tailwind classes converted to **inline `style` objects**.
  `shared.tsx` was 5 lines and held no primitives, so every page re-implemented
  its own tab strip and key-facts grid.
- Literal hexes (`#5048ED`, `#667085`) throughout — the theme colour copied by
  hand, so it no longer re-skins.
- **No loading, empty or error state on any custom surface.** The stock CRUD
  list had a designed empty state; the custom pages had none.
- Hard-coded `$` on an Indian distribution business.
- Every child tab rendered **completely blank** while both its API calls
  returned `200` with correctly filtered data.
- `Add Sales Order` and `Add Purchase Order` both 500'd:
  `KeyError: 'lines'` from `self.declared_fields["lines"]` in `__init__`.
  `BaseForm` puts a `CustomSchemaField` in `self.custom_schema_fields`.
- `SalesOrderForm` omitted `retailer` entirely — a required non-null FK.

Root cause for the visual half: **the skeleton was executable and the design
rules were prose**, so the skeleton won. `design-system.md` was a good document
that no generated file complied with.

Reference direction taken from the user's interactive `pharma-enterprise-ui`
skill (design brief, layered surfaces, shape-matched skeletons, empty-state
copy table, visual anchor / anti-symmetry), adapted to Agent Mode's actual
constraints — **no CDN fonts, no icon library, no new packages**, and Zango's
initializer already emitting full `--color-brand-*` ramps, so the `color-mix`
brand-hydration pattern is unnecessary here.

| Change | Detail |
|---|---|
| **New `references/frontend/shared-primitives.md`** | The `shared.tsx` contract: `PageShell`, `PageHeader`, `KeyFacts`, `Tabs`, `Card`, `StatusChip`, `Skeleton`, `EmptyState`, `ErrorState`, `Money`, `DateText`, `Num`, `NavigateTableBody`. Formatting is centralised so currency/date are right by construction. Labelled a floor, not a template. |
| **New STEP 5b** | Shared primitives get their own ordered sub-step, *before* the pages. Sub-steps renumbered 5a-5g; all cross-references updated. |
| `design-system.md` | Rewritten 139 → ~330 lines. Adds §0 design brief, layered surfaces, "build primitives first", "use Tailwind not inline styles", visual-anchor / anti-symmetry rule, restrained-motion section with `prefers-reduced-motion`, skeleton shape-matching, empty-state copy table, currency-from-spec. States the CDN-font prohibition explicitly, since general design skills advise the opposite. |
| STEP 5 verify gate | Six booleans → twelve. The six new ones are greppable: no literal hex in `src/custom/`, no inline `style` for static styling, four states per surface *including each child tab*, `Money`/`DateText` sourced from the spec. |
| `entity-360.md` §4 | New warning: verify the child tab actually renders. A 200 with correct data and a blank tab is the observed failure; how to diagnose against a working list page. |
| `entity-360.md` §7 | Reframed "Skeleton to copy" → "a floor, not a template", naming the transcription failure and what to carry across (mechanics) vs not (styling). |
| `packages/crud/forms.md` | **Bug fix.** `CustomSchemaField` lives in `self.custom_schema_fields`, not `declared_fields` — build-time clean, runtime 500. Plus: every required non-null field needs a form field. Both added to troubleshooting. |
| Critical rules | Primitives-before-pages; reference skeletons are floors. |
| **Run context now carries `theme:`** | `context.py` reads the app's active `ThemesModel.config` (falling back to `DEFAULT_THEME_CONFIG`) and `prompt.py` renders it as one line: `primary #5048ED, secondary …, button …, radius …, font …`. The login page renders **before authentication**, so `useAppContext()` has no theme and the initializer's `--color-*` variables are not in scope — it was the one screen with no runtime source for the palette, which is why `wapp3`'s login card hard-coded `#5048ED` plus two hand-picked gradient stops. |
| `auth-login.md` | Replaced the (incorrect for this page) "read `useAppContext().theme`" instruction with: take the values from the run context's `theme:` line, declare them once as custom properties on the root class, and derive gradient stops via `color-mix()` so a re-theme changes one line. Font is a name only — never fetched. |
| **`BaseForm.clean()` returns `None`** | **Bug fix.** `packages/crud/forms.py:92` runs its `unique_together` checks and falls off the end with **no `return`**, so the standard Django idiom `cleaned_data = super().clean()` yields `None`. Verified by executing both forms against Django: `super().clean()` → `NoneType`, value lost; reading `self.cleaned_data` → `dict`, value intact. Django's own documentation teaches the assigning form, so an agent writes it by default — and it is already live in two generated apps: `wapp3/backend/payments/forms.py:74` reads from the `None` (AttributeError → 500 on save) and `wapp4/backend/appointments/forms.py:44` returns it (validated data silently discarded). Nothing raises at import or build time. `forms.md` now carries a callout in the clean-method section, a troubleshooting entry ("cross-field validation never runs / values save as blank"), and best-practice item 9; the example comments `super().clean()` as side-effects-only. A test pins all three. |
| **Primitives were too weak to produce a polished page (`wapp4`)** | `wapp4` followed the v1.3.0 rules correctly — `shared.tsx` written first (358 lines), composed from, tokens not hexes, Tailwind not inline styles, a real skeleton — and the Patient detail page still looked like a wireframe: a back link, a title, three *unlabelled* floating values, a tab strip, and one card containing a single field. The rules were satisfied; the page was not designed. Two causes. (1) **The spec was prose, the primitives were code.** `design-system.md` §6 described a detail page in two lines pointing at another file, so the visual bar was never expressed in anything the agent could copy — while `KeyFacts` shipped as bare label/value `<span>`s, which is *exactly* the floating text observed. The agent built the best page its vocabulary allowed. (2) `KeyFacts` read `f.display_name`, but the detail API returns `name` — so every label rendered blank. Fixed: `KeyFacts` rebuilt as bordered cards with a required-in-practice `anchor` (tinted, 25px, spans two columns) and a `display_name → label → name → key` fallback; new `FieldGrid`, `Section`, `Button` and `Avatar` primitives; `PageHeader` takes an `avatar`; §6 now carries an ASCII anatomy sketch and five non-negotiables; the usage example shows the anchored/sectioned/counted shape; gate items 14-15 require checking the rendered page against the sketch and confirming labels are visible. **Lesson for future edits: a visual rule that exists only as prose does not reach the output — it has to be in the primitive.** |
| **Routes/menus silently skipped (`wapp4`)** | **Bug fix.** `wapp4` finished with **0 routes and 0 menus** in the schema, yet reported every task complete. The agent wrote `routes_payload.json` and `menu_payloads.md` to the workspace and asked an operator to POST them, claiming the sandbox blocked all curl POST-body flags. **That claim was false** — `check_bash()` with the app's `allowed_hosts` allows `-X POST`, `-d`, `--data-raw`, `--data-binary`, `-F` and `-H`; the server log shows only GETs, so no POST was ever attempted. Cause: run-prompt constraint 6 said "The Bash tool is read-only... shell commands that write are blocked" in absolute terms, two lines above constraint 8 demanding a POST — the agent resolved the contradiction by assuming POST was blocked. Fixed: constraint 6 now scopes read-only to the *filesystem* and states POST is permitted; constraint 8 lists the allowed flags, says a payload file does not complete the step, and requires reporting the verbatim failure rather than guessing. SKILL.md 5g closes the file-substitute hatch, and gate item 6 now demands `action=get_routes` read-back (a `[]` response means the step failed regardless of what was written to disk). |
| **App module mount + `urls.py` pinned** | Two linked bugs. (1) SKILL.md registered the app module at `{"re_path": "^app/"}` while every reference file and every working app uses `{"re_path": "^"}` — the module is mounted at the site root and its own `urls.py` owns the rest of the path, which is exactly why `^app/` appears *inside* `urls.py`. Mounted at `^app/` the module never sees `/` or `/login`, so both redirects are dead; the line even claimed it "catches root paths". (2) `urls.py` was never shown inline — only a one-line tree comment — so the patterns were improvised: `wapp1` wrote `r"^$"` for the root entry and broke it, while `wapp2`/`wapp3` happened to write `r"^/"`. Verified against the running app: with the `^` mount, `/` → 302 → `/app` and `/app/` → 200. SKILL.md now shows the mount as `"^"` with the reasoning, inlines the exact three-pattern `urls.py`, and names `r"^$"` as the wrong form; the template `urls.py` carries the same comment (and is aligned to the shipped `r"^login/?$"`), its README says copy verbatim, and two tests pin the mount and the pattern. |
| **Menu icons** | **Bug fix.** All nine sidebar items in `wapp3` rendered as the same grey page. Verified in the tenant schema, not just the API: every entry in all three role menus in `wapp3.dynamic_models_appmenumodel.menu` is persisted as `"icon": "\U0001F4C4"`, and every route in `dynamic_models_approutesmodel.routes` has **no `icon` key at all**. Cause: `clean_icon()` opens with `if not icon: return "\U0001F4C4"`, so an omitted icon is silently substituted before it reaches the frontend — no error, nothing logged. The docs also contradicted themselves (routes "SVG only" vs menus "emoji or SVG") and SKILL.md's own curl example used `\U0001F4C4`, i.e. taught the fallback glyph. Read the shipped renderer to get the real contract rather than trusting either doc: `<svg` → inlined; emoji **or any string ≤ 4 chars** → text; anything longer → `<img src>`. That third branch means an icon *name* (`"package"`) silently becomes a broken image — there is no name lookup. Now documented as a three-branch table, with emoji recommended, a rule in 5g, the example fixed, and gate item 6 extended to re-read the menu back and reject an all-`\U0001F4C4` response. |
| No-hex gate rescoped | Item 8 now covers `src/custom/pages/` and names `src/custom/auth/` as the sole exception, where literals are required but must all match `theme:`. An unqualified ban would have flagged a correctly-written login card. |
| `zango-requirements-analyst` | Spec template's Branding block now shows currency as an **inferred** line. Deliberately *not* a new question: currency is almost always derivable from business context, and the analyst's question budget is scarce ("three to four per turn", "detail that does not change what gets built is noise"). The builder infers it, sets it in one place, and records it as an assumption. |

Still unverified in a live run: whether the child-tab blank is fixed by extra
`CrudHandler` props (the doc now tells the agent to diagnose it against a
working list page rather than asserting a fix that has not been proven).

## 2026-09-17 — frontend setup made a hard, ordered gate (v1.2.0)

v1.1.0 asked for a polished frontend but did not get one. Observed in a real
run (`wapp2`, Vendor Onboarding): **no `frontend/` directory was ever created**,
`static/` was empty, all three registered routes were `page_type: "crud"`, and
`backend/app/templates/app.html` was a verbatim copy of
`packages/appbuilder/templates/appbuilder/app.html` — `app_initializer_endpoint`
script block and `packages/appbuilder/js/build.<version>.js` bundle included.
No error was raised at any point.

Root cause was **ordering plus an escape hatch**, not missing instructions:

- The frontend was sub-step **5d of 5**, after the `app` module (5a) and route
  registration (5b/5c), described in the same register as those. It read as an
  enhancement to an already-working app.
- 5a was reached while no `frontend/` existed, so its own text — *"Load the
  appbuilder bundle only as an interim"*, and
  *"`packages/appbuilder/templates/appbuilder/app.html` is a working
  reference"* — made copying the platform shell the sanctioned move. Nothing
  ever brought the agent back to replace it.

| Change | Detail |
|---|---|
| STEP 5 title + intro | "Make the app reachable" → "**Build the frontend** and make the app reachable". Adds an ordered sub-step table and states that the order is load-bearing. |
| **Sub-steps reordered** | Was 5a app module → 5b routes → 5c menus → 5d frontend → 5e login. Now **5a scaffold → 5b custom pages → 5c branded login → 5d build → 5e app module → 5f routes and menus**. `app.html` is now written once, after a real bundle exists. This matches the upstream interactive skill, whose STEP 5 also puts "Frontend Setup (one-time)" before the app module. |
| 5a | **New framing.** Named as the step that gets skipped, with the consequence stated. Scaffold, `.env`/`VITE_PROXY_ROUTES`, target `src/` layout and the npm allowlist all moved here from the old 5d. |
| 5e | Escape hatches removed: no "interim" bundle, and the instruction to use appbuilder's `app.html` as a reference is replaced by an explicit prohibition naming both tells (`app_initializer_endpoint`, `packages/appbuilder/js/`). Full `app.html` body now inlined rather than a 3-line fragment. |
| 5f | Adds: an app whose routes are *all* `page_type: "crud"` has no custom frontend. The `appbuilder_config_url` UNAVAILABLE branch now skips only 5f — it previously read as licence to skip frontend work too. |
| Verify gate | **New.** Six booleans at the end of STEP 5, including the two `app.html` string tells. |
| `templates/app-module/README.md` | "When to create this" section added (after 5a–5d, never before) with the same prohibition. `{{BUILD_FILE}}` instruction now says to read the name off disk and shows the finished tag. |
| STEP 7 + Critical rules | Report the bundle filename and quote `app.html`'s `src` line. New critical rule: `frontend/` missing at end of run means the frontend was not built. |

Not changed: `entity-360.md`, `auth-login.md`, `design-system.md` — their
content was never the problem; they were simply never reached.

## 2026-09-16 — polished frontend & branded login (v1.1.0)

Node is now guaranteed in the Agent Mode runtime (the platform installs it if
absent), which invalidates the assumption behind most of the original frontend
delta. The server copy now asks for *more* frontend than the interactive skill,
not less.

| Change | Detail |
|---|---|
| `SKILL.md` header + description | Node stated as available; appbuilder's shell described as the floor, not the target. v1.0.0 → v1.1.0. |
| STEP 3 UX decisions | Rewritten. Focus objects (inbound `ZForeignKey` **and** worked on directly) get full-page entity-360 views with child tables. No cap — the agent justifies its selection. Adds a per-role landing page and the branded login as standing requirements. |
| STEP 5 intro | 5a–5e all mandatory; the "only when genuinely needed / if Node is available" hedge is gone. |
| **STEP 5a** | **Bug fix.** It instructed `app.html` to load appbuilder's prebuilt bundle and said "you are not building your own". With a custom frontend that silently discards every custom page and the login, with no error. Now serves the app's own `js/zango-app.<ts>.min.js`, and requires `AnonymousUsers` on `AppView`/`RedirectAppView`. |
| STEP 5d | "Do not scaffold a frontend just because you can" deleted, along with the Node-unavailable branch. Adds the expected `frontend/src` layout. |
| STEP 5e | **New.** Branded login, always. |
| STEP 7 + Critical rules | Report which bundle is served, entity-360 selection and its justification, server-side child filtering, and which of the three login paths were verified. |
| Server-mode banners (5 files) | Corrected, not deleted: Bash is still read-only, but the "npm/npx cannot run, Node is unavailable" claim was false. |

### New references (written here first)

- `references/frontend/entity-360.md`
- `references/frontend/auth-login.md`
- `references/frontend/design-system.md`

These have **no upstream counterpart**. They are deliberately written to be
portable — nothing in them is server-mode-specific — so they should be
contributed back to the interactive skill once proven in a real run. Until
then this is the only copy.

Two corrections captured in them that the rest of the docs get wrong:

1. Child-table scoping is `get_table_data_queryset()` on the **table class**
   (reading `self.crud_view_instance.request`). `BaseCrudView` has no
   `get_queryset()`; overriding that name silently no-ops and leaves child
   tables unfiltered — a cross-record data leak.
2. `customMainDetail` receives **camelCase** props (`generalDetails`,
   `workflowDetails`). The long snake_case example in `frontend/crud.md` is for
   `customDrawerDetail` only; copying it into `customMainDetail` renders a
   blank page with no error.

### `zango-requirements-analyst`

Phase 1 previously talked users *out* of custom UI ("a fully custom-designed
screen would take much longer than the rest of the app put together"), directly
contradicting Phase 2's new defaults. That example and the "steer away from
custom React" note are removed; the question table now asks what else belongs
on an entity's page (which becomes its child tabs) and collects product name
and brand colours for the login screen.

## Keeping it in sync

This copy is the source of truth for Agent Mode. When the interactive skill
changes, re-apply the delta above rather than copying over it.
