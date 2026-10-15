"""Compose the run prompt.

The vendored skill is dispatched by its qualified name. Plugin-provided
skills are addressed ``plugin:skill`` — the same convention Claude Code uses
for its own bundled plugins — and dispatch-by-name works even when the skill
is absent from the ``skills`` allowlist, which makes it the robust path.

The constraints block deliberately overrides the skill where they conflict:
the laptop version of the skill assumes Docker, an interactive human, and a
Node toolchain, none of which exist in server mode.
"""

from __future__ import annotations


PLUGIN_NAME = "zango-agent-mode"
# Builds every app written in the generic Zango app spec (app_spec.yaml).
STUDIO_SKILL_NAME = "zango-app-studio"
STUDIO_SKILL = f"{PLUGIN_NAME}:{STUDIO_SKILL_NAME}"
# The general developer skill. Only loaded beside a template build skill of
# its own (PSP's), which still hands migrations, sync and the frontend to it.
DEVELOPER_SKILL_NAME = "zango-app-developer-server"
DEVELOPER_SKILL = f"{PLUGIN_NAME}:{DEVELOPER_SKILL_NAME}"

MAX_REQUIREMENT_CHARS = 20_000

_CONSTRAINTS = """\
## Server-mode constraints (these override the skill where they conflict)

1. Headless. There is NO human to answer questions. Where the skill tells you
   to ask the user, choose the most reasonable option instead and list every
   assumption you made in your final summary.
2. The app already exists and is deployed. Skip environment bootstrap, app
   creation and domain setup.
3. The `appbuilder`, `crud` and `workflow` packages are ALREADY INSTALLED for
   you (see installed_packages above). You must build on them: `BaseCrudView`
   for CRUD, `BaseForm`/`FormRenderer` for forms, the workflow package for any
   entity with a lifecycle, and AppBuilder route/menu config for pages. Do NOT
   hand-roll Django views, serializers, a bespoke JSON API, or a status field.
   A raw class-based view is acceptable only where the operation genuinely does
   not map to CRUD — and say why in your summary.
4. You MAY run these, and only these, management commands — use them to apply
   and verify your own work, and fix what they report:
     python {manage_py} ws_makemigration {app_name}
     python {manage_py} ws_migrate {app_name}
     python {manage_py} ws_sync {app_name}
     python {manage_py} sync_static {app_name}
     python {manage_py} collectstatic --noinput
   The platform re-runs this same sequence after you finish as a backstop, so
   a step you already completed is simply a no-op. Everything else is denied:
   docker, git commit/push, pip, npm/npx/yarn, the zango CLI, `python -c`,
   and any other manage.py subcommand.
5. Every file you create or modify must be inside the workspace directory
   above, which is your working directory. Writes elsewhere are blocked and
   will be reported as a policy violation.
6. The Bash tool is read-only **for the filesystem**. Use Read, Write, Edit,
   Glob and Grep for all file work; shell commands that write files are
   blocked. This does NOT restrict network calls: `curl` POST/PUT to this
   app's own domain is permitted and required by constraint 8.
7. {frontend_rule}
8. Registering AppBuilder routes and menus is MANDATORY for every page you
   create — a CRUD view with no route never appears in the app's navigation.
   Use the appbuilder_config_url and appbuilder_token above with `curl`; see
   references/packages/appbuilder/api-configuration.md. curl is permitted
   against this app's own domain and localhost, and **POST with a request body
   is allowed** — `-X POST`, `-d`, `--data-raw`, `--data-binary`, `-F` and
   `-H` all work against those hosts. Writing the payload to a file for an
   operator to send later does NOT complete this step: it is only done once
   the API has accepted it and `action=get_routes` reads it back. If a call
   fails, report the exact command and the server's response in your summary —
   never assume the method is blocked without attempting it.
9. Declare test users in `users.json` at the workspace root — one per role
   you define ({"users":[{"name":..,"email":..,"role":..}]}). The platform
   creates them and generates temporary passwords; never invent a password or
   write one to a file. Roles you define automatically receive the baseline
   AllowFromAnywhere userAccess policy.
10. Finish with a summary containing: files created or modified, models added
   or changed, whether migrations are needed, policies added, roles required,
   assumptions you made, and any remaining manual steps.
"""


def _format_list(items: list, empty: str = "(none)") -> str:
    return ", ".join(str(i) for i in items) if items else empty


def _format_theme(theme: dict) -> str:
    """The app's palette, flattened onto one line for the run context.

    The login page needs these values literally: it renders before
    authentication, so `useAppContext()` is unavailable and the CSS variables
    the initializer sets are not in scope either. Given no source, an agent
    hard-codes a hex it guessed -- which then stops matching the moment the
    app is re-themed. Everywhere else in the app, the tokens remain correct.
    """
    if not isinstance(theme, dict) or not theme:
        return "(not configured — use var(--color-*) tokens everywhere)"
    colour = theme.get("color") or {}
    button = theme.get("button") or {}
    typography = theme.get("typography") or {}
    parts = [
        f"primary {colour['primary']}" if colour.get("primary") else "",
        f"secondary {colour['secondary']}" if colour.get("secondary") else "",
        f"background {colour['background']}" if colour.get("background") else "",
        f"button {button['background']}" if button.get("background") else "",
        f"radius {button['border_radius']}px" if button.get("border_radius") else "",
        f"font {typography['font_family']}" if typography.get("font_family") else "",
    ]
    return ", ".join(p for p in parts if p) or "(not configured)"


RESUME_PREAMBLE = """\
## You are RESUMING an interrupted build

A previous run on this same workspace stopped before it finished:

    {reason}

Everything it wrote is still on disk, and this session continues from where it
left off. **Do not start over.**

1. First, look at what is already there — read `settings.json` and list the
   modules under `backend/`. Trust the files, not your memory of them.
2. Work out what is missing or half-finished against the requirement below.
3. Finish only that. Re-writing files that are already correct wastes the
   budget that ran out last time.
4. Then complete the remaining steps as normal: routes and menus, test users,
   migrations and sync.

"""


def compose_resume_prompt(requirement_text: str, ctx, reason: str, skill: str) -> str:
    """Prompt for a run that continues an interrupted one."""
    return RESUME_PREAMBLE.format(
        reason=(reason or "the run was interrupted").strip()
    ) + compose_prompt(requirement_text, ctx, skill=skill)


def _manage_py_path() -> str:
    from django.conf import settings

    return f"{settings.BASE_DIR}/manage.py"


_TEMPLATE_BUILD = """\
## Build this app from its {name} journey

This app runs on Zelthy's **{name}** template (version {version}). The user
answered the template's interview and approved the result: a {spec_format}
journey in the template's own vocabulary. It is at

    {spec_path}

Read it in full before changing anything. Every key in it is a decision the
user signed off — implement all of it, and say in your summary what you could
not honour and why. The `{skill}` skill explains how each section maps onto
the template; follow it.{engine}
"""


def template_build_request(template, spec_path: str, engine_paths=()) -> str:
    """The ask for a template build: where the approved journey is, which skill."""
    engine = ""
    if engine_paths:
        engine = (
            "\n\nThe template's engine ("
            + ", ".join(f"`{p}`" for p in engine_paths)
            + ") is already in the workspace and is restored before every build. "
            "Do not edit it; anything the engine cannot do goes in the app's own code."
        )
    return _TEMPLATE_BUILD.format(
        name=template.name,
        version=template.version or "current",
        spec_format=template.spec_format,
        spec_path=spec_path,
        skill=template.qualified_skill,
        engine=engine,
    )


def compose_prompt(requirement: str, ctx, skill: str) -> str:
    """Build the full prompt: skill dispatch, run context, constraints, ask.

    ``skill`` is the skill the prompt dispatches: the template's own build
    skill. (Builds on the generic spec use ``compose_studio_prompt``.)
    """
    requirement = (requirement or "").strip()
    if not requirement:
        raise ValueError("requirement must not be empty")
    if len(requirement) > MAX_REQUIREMENT_CHARS:
        raise ValueError(
            f"requirement is {len(requirement)} chars; "
            f"the maximum is {MAX_REQUIREMENT_CHARS}"
        )

    frontend_state = (
        "present at frontend/"
        if getattr(ctx, "frontend_exists", False)
        else "not scaffolded yet"
    ) + (
        " · Node available, builds permitted"
        if getattr(ctx, "frontend_build_allowed", False)
        else " · Node unavailable, no custom React build"
    )
    packages = _format_list(
        [f"{p['name']} {p['version']}".strip() for p in ctx.packages]
    )
    modules = _format_list([f"{m['name']} ({m['path']})" for m in ctx.modules])
    roles = _format_list(ctx.roles)
    theme = _format_theme(getattr(ctx, "theme", None))
    domain = ctx.primary_domain or "(no domain configured)"
    manage_py = _manage_py_path()
    if getattr(ctx, "frontend_build_allowed", False):
        frontend_rule = (
            "Node IS available for this app and custom React builds are "
            "enabled, so scaffolding and building the frontend is REQUIRED, "
            "not optional — follow STEP 5 in order (5a scaffold, 5b plan the "
            "pages, 5c shared primitives, 5d custom pages, 5e branded login, "
            "5f build, 5g app module, 5h routes and menus). Do not stop at "
            "appbuilder's prebuilt shell: it renders "
            'only page_type "crud" pages, so it cannot show an entity-360 '
            "detail page, a role landing page or a branded login. You may run "
            "only: `npx @zango-core/create-zango-app frontend`, `npm "
            "install`, `npm run build:zango`, and `npm install` of the "
            "approved design packages (echarts, echarts-for-react, recharts, "
            "date-fns, clsx, tailwind-merge). Anything else npm-related is "
            "denied. lucide-react is already installed and Google Fonts are "
            "reachable -- use both. Deploy the build with exactly "
            "`cp -r frontend/zango-build/. static/js/` — that one copy is "
            "permitted; every other cp/mv/mkdir is blocked."
        )
    else:
        frontend_rule = (
            "Node is not available, so you cannot scaffold or build a custom "
            "React app. Use backend modules plus CRUD routes rendered by "
            "appbuilder's prebuilt shell. If a requirement genuinely needs a "
            "custom React page, implement the backend and state clearly in "
            "your summary what frontend work remains for a developer."
        )
    if getattr(ctx, "appbuilder_token", ""):
        appbuilder = (
            f"appbuilder_config_url: {ctx.appbuilder_config_url}\n"
            f"appbuilder_token: {ctx.appbuilder_token}\n"
            "  (pass as ?token=<appbuilder_token> on every AppBuilder API call;\n"
            "   valid 2 hours from the start of this run)"
        )
    else:
        appbuilder = (
            "appbuilder_config_url: UNAVAILABLE — "
            f"{getattr(ctx, 'appbuilder_reason', '') or 'not configured'}.\n"
            "  Register routes/menus is not possible this run; say so in your summary."
        )

    # Plain replacement, not .format(): the text contains literal JSON braces.
    constraints = (
        _CONSTRAINTS.replace("{manage_py}", manage_py)
        .replace("{app_name}", ctx.app_name)
        .replace("{frontend_rule}", frontend_rule)
    )
    return f"""/{skill}

## Run context (authoritative — do not re-discover this)

app_name: {ctx.app_name}
manage_py: {manage_py}
frontend: {frontend_state}
workspace: {ctx.workspace_path}   <- this is your working directory
schema: {ctx.schema_name}
primary_domain: {domain}
installed_packages: {packages}
existing_modules: {modules}
roles: {roles}
theme: {theme}
{appbuilder}

{constraints}
## Requirement

{requirement}
"""


_STUDIO_RULES = """\
## Server-mode rules (these override the skill where they conflict)

1. Read `{skill_dir}/references/server-mode.md` FIRST. The platform runs every
   script of the skill itself, before and after your turn; you write code.
2. Headless: nobody answers questions. Decide, and list every assumption in
   your final summary.
3. Already done for you: the spec was linted and resolved into `.zas/`
   (`spec.resolved.json`, `plan.md`, `holes.md`, `test_plan.md`, `issues.md`),
   the `zas_core` runtime is in `backend/zas_core/` and registered.
   Frontend: {frontend}
4. You cannot run Python (no `py_compile`, no skill scripts), migrations,
   `cp`/`mv`/`mkdir`, the zango CLI or the platform API. Use Read, Write, Edit,
   Glob and Grep for every file. Bash is read-only{npm}.
5. Never edit `backend/zas_core/`, `packages/` or the spec. Every file you
   write is inside the workspace (your working directory).
6. After you finish, the platform runs migrations, roles, policy and task sync,
   test users, static files, AppBuilder routes and menus, the hole audit and
   the test layers. If something fails it resumes this session with the
   failures: fix them at their cause, then stop.
"""

_STUDIO_BUILD = """\
## Build this app from its approved App Studio spec

{update}The user approved the spec in the App Studio preview; build exactly
what it describes. The approved YAML is at `{spec_path}`; the resolved form
every phase reads is `.zas/spec.resolved.json`. Follow the `{skill}` skill:
Phase 3 (every module in `.zas/plan.md` order), Phase 4 (every hole in
`.zas/holes.md`), Phase 6 steps 4-6{frontend_steps}, and Phase 7 step 1 (test
fixtures and scenarios). Finish with the summary server-mode.md asks for.
"""


def compose_studio_prompt(ctx, template_build, studio) -> str:
    """The prompt for an App Studio build (see studio_build.py): run context, rules, ask."""
    skill = template_build.skill
    if studio.frontend_ready:
        frontend = (
            "prepared — `frontend/` is scaffolded, crud 2.0.0 and lucide-react are "
            "pinned and patched, `src/zas/`, `src/custom/spec.ui.json`, `src/index.css` "
            "and the icons are in place."
        )
        npm = (
            ", except, from `frontend/`: `npx --no tsc --noEmit`, `npm run build:zango`, "
            "`npm install`; and the deploy copy `cp -r frontend/zango-build/. static/js/`"
        )
        frontend_steps = (
            " (pages index, App.tsx, slots, type-check, build, deploy, app module)"
        )
    else:
        frontend = (
            f"SKIPPED ({studio.frontend_reason or 'not available'}). Do the backend "
            "phases only and say in your summary that the frontend was not built."
        )
        npm = ""
        frontend_steps = " — skipped this run"
    update = (
        "This is an UPDATE build: keep `hooks.py`, `tasks.py`, `slots/` and "
        "`.zas/holes.md` from the previous build and regenerate everything else.\n\n"
        if studio.update
        else ""
    )
    views = studio.custom_views() if studio.frontend_ready else []
    if views:
        frontend_steps += (
            ". The spec declares list views this runtime has no component for — "
            + ", ".join(f"{v['page']} ({v['type']})" for v in views)
            + " — write each as a custom view (`.zas/views.md`, `references/views.md`); "
            "the build is not done without them"
        )
    bundle = studio.zas_dir / "bundle" / "index.md"
    if studio.frontend_ready and bundle.is_file():
        frontend_steps += (
            ". The user approved how every custom page, tab and panel looks: `.zas/bundle/index.md` "
            "lists each with its sketch, kit outline and screenshots. Port each sketch onto the zas "
            'kit (`references/custom-code.md`, "Porting a sketch"); the platform checks the result '
            "against that outline"
        )
    rules = _STUDIO_RULES.format(
        skill_dir=template_build.skill_dir, frontend=frontend, npm=npm
    )
    ask = _STUDIO_BUILD.format(
        update=update,
        spec_path=template_build.spec_path,
        skill=skill,
        frontend_steps=frontend_steps,
    )
    return f"""/{skill}

## Run context (authoritative — do not re-discover this)

app_name: {ctx.app_name}
workspace: {ctx.workspace_path}   <- this is your working directory
skill_dir: {template_build.skill_dir}
spec: {template_build.spec_path}
template: {template_build.template.name} v{template_build.template.version or 'current'}
primary_domain: {ctx.primary_domain or '(no domain configured)'}
build: {'update' if studio.update else 'first build'}

{rules}
{ask}"""
