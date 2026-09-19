import os
import shlex
import subprocess

from django.core.management.base import BaseCommand, CommandError
from django.db import connection

from zango.apps.shared.tenancy.models import TenantModel


# The composed prompt's constraints block (constraint 6: "Bash is read-only
# for the filesystem") describes the SDK's PreToolUse guard, which this REPL
# does not enforce (see the class docstring). Left as-is, a subagent this
# session delegates to (e.g. Explore, spawned via Task) can read that framing
# as "no tools at all" rather than "Bash present but restricted," and report a
# false hard blocker. This note overrides that one line for REPL runs only --
# every other constraint (workspace-only writes, permitted manage.py
# subcommands, etc.) still describes real policy the agent should follow.
_REPL_TOOL_OVERRIDE_NOTE = """\
## REPL session note (overrides constraint 6 below)

This is an interactive Claude Code session, not a guarded Agent Mode run.
Read, Write, Edit, Glob, Grep and Bash are all fully available to you and to
any subagent you delegate to via Task -- Bash is NOT restricted to read-only
here, unlike in a real Agent Mode run. If a tool call fails, treat it as an
ordinary error, not evidence that the tool is disabled.

"""


# Vars a parent Claude Code session sets in its own shell. Inherited by a
# child `claude` process, they trip the CLI's nested-session guard -- Bash,
# Read, Write, Edit and Glob all come back "disabled for this session, in
# subagents as well as here" -- even though this is meant to be a fresh,
# independent session. Strip them so the REPL works from a terminal that is
# itself running inside Claude Code, not just a bare terminal.
_NESTED_SESSION_ENV_VARS = (
    "CLAUDECODE",
    "CLAUDE_CODE_SESSION_ID",
    "CLAUDE_CODE_CHILD_SESSION",
    "CLAUDE_CODE_ENTRYPOINT",
    "CLAUDE_CODE_SSE_PORT",
    "CLAUDE_CODE_MESSAGING_SOCKET",
    "CLAUDE_CODE_MESSAGING_TOKEN",
    "CLAUDE_CODE_EXECPATH",
    "CLAUDE_PID",
    "CLAUDE_EFFORT",
)


class Command(BaseCommand):
    """Open an interactive Claude Code session against the real skill.

    Iterating on the skill through real Agent Mode runs is slow and costs a
    full run per edit. The SDK is a wrapper around the same CLI this command
    invokes, so loading the vendored plugin into an interactive session
    exercises the real skill, the real plugin resolution and the real
    reference-doc loading for the price of an ordinary conversation.

    Two things are deliberately NOT reproduced:

    * The PreToolUse guards. Those are Python hooks supplied by the SDK
      runner; an interactive session does not enforce them. They are covered
      by ``zango.tests.apps.agent_mode.test_guards`` instead, which tells you
      more than a live run would.
    * ``permission_mode=acceptEdits`` with nobody watching. A session where
      you nudge the agent is not evidence that an unattended run succeeds.

    So this answers "is the instruction clear, findable and followed", not
    "will a headless run finish". It is a skill-authoring tool.

    One platform step IS reproduced, behind ``--ensure-users``. The agent only
    ever *declares* test users in ``users.json``; ``tasks.py`` is what creates
    them, and this command does not run ``tasks.py``. Without the flag a REPL
    run ends with a correct ``users.json`` and no users, which reads as the
    agent having skipped STEP 5 when it did its part exactly right.
    """

    help = (
        "Open an interactive Claude Code session preloaded with the Agent Mode skill."
    )

    def add_arguments(self, parser):
        super().add_arguments(parser)
        parser.add_argument(
            "app_name",
            nargs="?",
            help=(
                "App (tenant) whose context frames the prompt. Omit to load the "
                "skill with no app context."
            ),
        )
        parser.add_argument(
            "-r",
            "--requirement",
            default="",
            help="Requirement text to compose the prompt around.",
        )
        parser.add_argument(
            "--print-prompt",
            action="store_true",
            help="Write the composed prompt to stdout and exit without launching.",
        )
        parser.add_argument(
            "--cwd",
            default="",
            help=(
                "Working directory for the session. Defaults to the app's "
                "workspace, else the current directory."
            ),
        )
        parser.add_argument(
            "--model", default="", help="Model override passed through to the CLI."
        )
        parser.add_argument(
            "--ensure-users",
            action="store_true",
            help=(
                "After the session exits, create the roles and test users the "
                "agent declared in users.json, the way tasks.py does at the "
                "end of a real run. Needs an app_name. Passwords are printed "
                "once and never stored in the workspace."
            ),
        )

    def handle(self, *args, **options):
        from zango.apps.agent_mode.options import SKILL_PLUGIN_DIR
        from zango.apps.agent_mode.prompt import QUALIFIED_SKILL, compose_prompt

        prompt = ""
        cwd = options["cwd"]
        app_name = options["app_name"]

        if app_name:
            from zango.apps.agent_mode.context import build_app_context

            try:
                tenant = TenantModel.objects.get(name=app_name)
            except TenantModel.DoesNotExist:
                raise CommandError(f"No app named {app_name!r}.") from None
            # Mirrors tasks.py: the tenant schema must be active before the
            # context reads packages, roles and theme.
            connection.set_tenant(tenant)
            ctx = build_app_context(tenant)
            composed = compose_prompt(options["requirement"] or "(no requirement)", ctx)
            # The skill-dispatch line (/plugin:skill) must stay the first line
            # of the message for slash-command dispatch to fire, so the note
            # is spliced in right after it rather than prepended.
            dispatch_line, _, rest = composed.partition("\n")
            prompt = f"{dispatch_line}\n\n{_REPL_TOOL_OVERRIDE_NOTE}{rest}"
            if not cwd:
                cwd = ctx.workspace_path
            if not ctx.workspace_exists:
                self.stderr.write(
                    self.style.WARNING(
                        f"Workspace {ctx.workspace_path} does not exist yet; "
                        "the agent will see an empty tree."
                    )
                )
        elif options["requirement"]:
            raise CommandError("--requirement needs an app_name to build context from.")
        elif options["ensure_users"]:
            raise CommandError(
                "--ensure-users needs an app_name: the users are created in that "
                "app's tenant schema, from its workspace's users.json."
            )

        if options["print_prompt"]:
            self.stdout.write(prompt)
            return

        cwd = cwd or os.getcwd()
        if not os.path.isdir(cwd):
            raise CommandError(f"Working directory {cwd!r} does not exist.")

        # Matches options.py: the vendored plugin is loaded from disk and the
        # skill is addressed plugin:skill. Network tools stay off so the agent
        # cannot paper over a missing reference doc by searching the web --
        # that would mask exactly the gap this tool exists to find.
        #
        # --allowed-tools is explicit (mirrors options.py ALLOWED_TOOLS) rather
        # than relying on the CLI's own default grant: passing --plugin-dir can
        # otherwise leave the session with no file/bash tools at all.
        #
        # --setting-sources "" drops user settings (~/.claude/settings.json),
        # which is where enabledPlugins lives -- without this, any plugin you
        # have globally enabled (e.g. a different zango-app-developer build)
        # loads alongside the one under test here, contaminating the isolation
        # this command exists to give you. The only plugin in play is the one
        # passed via --plugin-dir. Mirrors options.py's intent -- there the SDK
        # achieves the same isolation via an explicit plugins=[...] list rather
        # than an ambient enabled-plugins set.
        argv = [
            "claude",
            "--setting-sources",
            "",
            "--plugin-dir",
            SKILL_PLUGIN_DIR,
            # Agent/TaskOutput/TaskStop are listed for the same reason
            # options.py lists them: the spawn tool reports as "Agent", and
            # without TaskOutput a run that delegates 5c-5e can never collect
            # its subagents' work. Omitting them here would make delegation
            # untestable in the one tool built to test the skill.
            "--allowed-tools",
            (
                "Read,Write,Edit,MultiEdit,Glob,Grep,TodoWrite,"
                "Task,Agent,TaskOutput,TaskStop,Bash,Skill"
            ),
            "--disallowed-tools",
            "WebFetch,WebSearch,NotebookEdit",
        ]
        if options["model"]:
            argv += ["--model", options["model"]]
        if prompt:
            argv.append(prompt)
        else:
            argv.append(f"/{QUALIFIED_SKILL} ")

        self.stdout.write(self.style.MIGRATE_HEADING("Agent Mode skill REPL"))
        self.stdout.write(f"  skill:  {QUALIFIED_SKILL}")
        self.stdout.write(f"  plugin: {SKILL_PLUGIN_DIR}")
        self.stdout.write(f"  cwd:    {cwd}")
        self.stdout.write(
            "  guards: NOT enforced here (see test_guards.py)\n",
        )
        self.stdout.write(f"  $ {shlex.join(argv[:-1])} <prompt>\n")

        env = {k: v for k, v in os.environ.items() if k not in _NESTED_SESSION_ENV_VARS}

        try:
            rc = subprocess.call(argv, cwd=cwd, env=env)
        except FileNotFoundError:
            raise CommandError(
                "The `claude` CLI was not found on PATH. Install Claude Code, or "
                "set it up so `claude` resolves."
            ) from None

        if options["ensure_users"]:
            self._ensure_users(ctx.workspace_path)

        raise SystemExit(rc)

    def _ensure_users(self, workspace_path):
        """Run the runner's own role/user reconciliation over users.json.

        Mirrors the RunPhase.USERS block in ``tasks.py``: roles first, because
        ``sync_policies_with_roles`` silently drops policy roles that do not
        exist, then users, which need their roles to already be there.
        """
        from zango.apps.agent_mode.roles import ensure_roles
        from zango.apps.agent_mode.users import ensure_users

        emit = lambda m, is_error=False: self.stderr.write(  # noqa: E731
            self.style.ERROR(m) if is_error else self.style.WARNING(m)
        )

        self.stdout.write(self.style.MIGRATE_HEADING("\nPost-run: roles and users"))
        for r in ensure_roles(workspace_path, emit=emit):
            self.stdout.write(f"  role {r.name}: {r.status}")
        for u in ensure_users(workspace_path, emit=emit):
            line = f"  user {u.email} ({u.role}): {u.status}"
            if u.password:
                line += f"  password: {u.password}"
            self.stdout.write(line)
