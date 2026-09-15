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
SKILL_NAME = "zango-app-developer-server"
QUALIFIED_SKILL = f"{PLUGIN_NAME}:{SKILL_NAME}"

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
6. The Bash tool is read-only in this environment. Use Read, Write, Edit,
   Glob and Grep for all file work; shell commands that write are blocked.
7. {frontend_rule}
8. Registering AppBuilder routes and menus is MANDATORY for every page you
   create — a CRUD view with no route never appears in the app's navigation.
   Use the appbuilder_config_url and appbuilder_token above with `curl`; see
   references/packages/appbuilder/api-configuration.md. curl is permitted, but
   only against this app's own domain and localhost.
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


def compose_resume_prompt(requirement_text: str, ctx, reason: str) -> str:
    """Prompt for a run that continues an interrupted one."""
    return RESUME_PREAMBLE.format(
        reason=(reason or "the run was interrupted").strip()
    ) + compose_prompt(requirement_text, ctx)


def _manage_py_path() -> str:
    from django.conf import settings

    return f"{settings.BASE_DIR}/manage.py"


def compose_prompt(requirement: str, ctx) -> str:
    """Build the full prompt: skill dispatch, run context, constraints, ask."""
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
    domain = ctx.primary_domain or "(no domain configured)"
    manage_py = _manage_py_path()
    if getattr(ctx, "frontend_build_allowed", False):
        frontend_rule = (
            "Node IS available for this app, so you may scaffold and build a "
            "custom React frontend when the requirement genuinely needs one "
            "(see STEP 5d). You may run only: "
            "`npx @zango-core/create-zango-app frontend`, `npm install`, "
            "`npm run build:zango`. Anything else npm-related is denied. For "
            "ordinary CRUD pages prefer appbuilder's prebuilt shell — it "
            "needs no build at all."
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
            "   valid 30 minutes from the start of this run)"
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
    return f"""/{QUALIFIED_SKILL}

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
{appbuilder}

{constraints}
## Requirement

{requirement}
"""
