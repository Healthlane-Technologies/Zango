"""Build the ClaudeAgentOptions for one run.

Every field here was checked against ``claude_agent_sdk/types.py`` in the
pinned wheel rather than taken from prose docs.

Two choices worth their justification:

* ``setting_sources=["user"]``, never ``"project"``. The project source loads
  ``.claude/`` from the cwd *and every parent up to the repo root*. The cwd is
  tenant-authored app code, so ``"project"`` would let an app inject settings,
  hooks or MCP servers into a privileged platform run.
* The skill is delivered as a **local plugin**, not by symlinking into HOME.
  Plugin-provided skills are addressed ``plugin:skill``.

The SDK is imported lazily so this module — and therefore the Django app —
stays importable on installs that do not have it.
"""

from __future__ import annotations

import os
import re

from pathlib import Path

from .prompt import DEVELOPER_SKILL


SKILL_PLUGIN_DIR = str(Path(__file__).resolve().parent / "skill_plugin")
ZANGO_PACKAGE_DIR = str(Path(__file__).resolve().parents[2])

# Bash is present but the PreToolUse guard reduces it to read-only. Hooks are
# evaluated before every other permission step and a hook deny is absolute,
# which is what makes that safe.
ALLOWED_TOOLS = [
    "Read",
    "Write",
    "Edit",
    "MultiEdit",
    "Glob",
    "Grep",
    "TodoWrite",
    # The spawn tool reports as "Agent" in transcripts; "Task" is its alias.
    # Both are listed so the allowlist matches whichever name the CLI uses.
    "Task",
    "Agent",
    # Agent launches in the BACKGROUND and returns immediately. TaskOutput is
    # how the parent collects a finished agent's result, and TaskStop cancels
    # one. Without them a dispatching run cannot ever retrieve its subagents'
    # work -- which is exactly how one run discarded an entire frontend while
    # reporting success.
    "TaskOutput",
    "TaskStop",
    "Bash",
    "Skill",
]

# Bare names remove the tool from Claude's context entirely.
DISALLOWED_TOOLS = [
    "WebFetch",
    "WebSearch",
    "NotebookEdit",
    # Waiting tools: a run has no later session to wake up into. Run 6 ended
    # its turn on a ScheduleWakeup to wait for its subagents.
    "ScheduleWakeup",
    "CronCreate",
    "CronDelete",
    "CronList",
    "Monitor",
    "RemoteTrigger",
    "PushNotification",
]

SYSTEM_PROMPT_APPEND = """\
You are running inside the Zango platform as a server-side app developer.
There is no interactive user. Never ask a question you could answer by
reading the workspace; state assumptions in your final summary instead.

Bash is restricted by a policy hook; denied commands cost a turn, so do not
try them: no shell loops (for/while), no interpreters (python, node), no
nested shells, no file manipulation (cp, mv, rm, mkdir, touch, sed -i, tee) -
use Read, Write, Edit, Glob and Grep instead, and read files one Read call
each (in parallel) rather than with a loop. Paths outside the app workspace
are readable only under the skill and the installed zango package.
No run_in_background on Bash.

Subagents (the Agent tool) run in the background and do not see these
rules: paste the Bash paragraph above into every Agent prompt. Their results
arrive as task notifications; the platform keeps the session open until
every one has reported, then asks you to collect them. Your final summary is
written only after all of them have finished and you have checked their
files.
"""


def agent_home() -> str:
    """A platform-controlled HOME for CLI state.

    Never rely on ``~``: outside compose the UID may not exist in
    /etc/passwd and HOME can end up as "/".
    """
    from django.conf import settings

    home = getattr(settings, "AGENT_MODE_HOME", "") or os.path.join(
        str(settings.BASE_DIR), ".agent_mode", "home"
    )
    os.makedirs(home, exist_ok=True)
    return home


def cli_session_dir(home: str, cwd: str) -> str:
    """The CLI's own folder for sessions started in ``cwd``.

    A tool result too large to return inline is saved under its
    ``tool-results/`` and the agent is told to Read it there; without this
    root the guard denied those reads. Only this workspace's folder: HOME is
    shared by every app's runs.
    """
    return os.path.join(home, ".claude", "projects", re.sub(r"[^A-Za-z0-9]", "-", cwd))


def build_env(creds, home: str) -> dict:
    env = {
        "HOME": home,
        "XDG_CONFIG_HOME": os.path.join(home, ".config"),
        "CLAUDE_CONFIG_DIR": os.path.join(home, ".claude"),
        "PATH": os.environ.get("PATH", ""),
        "API_TIMEOUT_MS": "600000",
        "CLAUDE_CODE_MAX_RETRIES": "3",
        "CLAUDE_ENABLE_STREAM_WATCHDOG": "1",
        "CLAUDE_STREAM_IDLE_TIMEOUT_MS": "300000",
        # Lets workspace code detect that it is running under Agent Mode.
        "ZANGO_AGENT_MODE": "1",
    }
    if creds.api_key:
        env["ANTHROPIC_API_KEY"] = creds.api_key
    elif creds.oauth_token:
        env["CLAUDE_CODE_OAUTH_TOKEN"] = creds.oauth_token
        # The SDK lays this env over the worker's own, and the CLI prefers an
        # API key to the login, so a key inherited from the worker would
        # silently bill the API. Blank every API-billing variable.
        env["ANTHROPIC_API_KEY"] = ""
        env["ANTHROPIC_AUTH_TOKEN"] = ""
        return env
    env.update(creds.extra_env or {})
    return env


def build_agent_options(
    *,
    run,
    ctx,
    creds,
    settings_path: str,
    hook_sink=None,
    stderr_sink=None,
    template_build=None,
):
    """Construct ClaudeAgentOptions for a run. Imports the SDK lazily.

    ``template_build`` (a template_build.TemplateBuild) names the build skill
    and lets the agent read the template's plugin and the approved spec
    written for this run. App Studio (the generic spec's skill) ships in this
    plugin; a template with a skill of its own (PSP) brings its plugin, and
    gets the general developer skill beside it, which that skill relies on.
    """
    from claude_agent_sdk import ClaudeAgentOptions, HookMatcher

    from django.conf import settings as dj

    from .config import load_config, node_available
    from .guards import make_pre_tool_use_guard

    cfg = load_config()
    home = agent_home()
    # Reads may also reach the vendored skill's own reference docs;
    # writes stay confined to the workspace.
    # Both conditions must hold: the operator opted in, and Node is actually
    # installed. Allowing npm where node is absent just produces confusing
    # failures deep in a run.
    allow_frontend = cfg.allow_frontend_build and node_available()

    guard = make_pre_tool_use_guard(
        ctx.workspace_path,
        hook_sink,
        read_roots=[
            SKILL_PLUGIN_DIR,
            # The framework source, read-only, for looking up core helpers.
            ZANGO_PACKAGE_DIR,
            cli_session_dir(home, ctx.workspace_path),
            *(
                [
                    template_build.plugin_dir,
                    template_build.skill_plugin_dir,
                    template_build.spec_dir,
                ]
                if template_build
                else []
            ),
        ],
        # curl is for the AppBuilder route/menu API on this app's own domain.
        allowed_hosts=[h for h in [ctx.primary_domain] if h],
        app_name=ctx.app_name,
        allow_frontend=allow_frontend,
    )

    kwargs = dict(
        cwd=ctx.workspace_path,
        add_dirs=[],
        setting_sources=["user"],
        settings=settings_path,
        plugins=[{"type": "local", "path": SKILL_PLUGIN_DIR}],
        skills=[],
        allowed_tools=list(ALLOWED_TOOLS),
        disallowed_tools=list(DISALLOWED_TOOLS),
        permission_mode=run.permission_mode
        or getattr(dj, "AGENT_MODE_PERMISSION_MODE", "acceptEdits"),
        hooks={
            "PreToolUse": [
                HookMatcher(
                    matcher="Write|Edit|MultiEdit|Read|Glob|Grep",
                    hooks=[guard],
                    timeout=15,
                ),
                HookMatcher(matcher="Bash", hooks=[guard], timeout=15),
            ]
        },
        include_partial_messages=False,
        system_prompt={
            "type": "preset",
            "preset": "claude_code",
            "append": SYSTEM_PROMPT_APPEND,
        },
        env=build_env(creds, home),
    )

    if template_build is not None and template_build.skill:
        from .studio_build import is_studio

        if os.path.realpath(template_build.skill_plugin_dir) != os.path.realpath(
            SKILL_PLUGIN_DIR
        ):
            kwargs["plugins"] = [
                *kwargs["plugins"],
                {"type": "local", "path": template_build.skill_plugin_dir},
            ]
        kwargs["skills"] = [template_build.skill]
        if not is_studio(template_build):
            kwargs["skills"].append(DEVELOPER_SKILL)
        kwargs["add_dirs"] = [template_build.spec_dir]

    # Per-run override wins; otherwise the platform setting.
    if run.model or cfg.model:
        kwargs["model"] = run.model or cfg.model
    if run.effort or cfg.effort:
        kwargs["effort"] = run.effort or cfg.effort
    if run.max_turns or cfg.max_turns:
        kwargs["max_turns"] = run.max_turns or cfg.max_turns
    if run.max_budget_usd or cfg.max_budget_usd:
        # Native hard per-run cost ceiling.
        kwargs["max_budget_usd"] = float(run.max_budget_usd or cfg.max_budget_usd)
    if getattr(dj, "AGENT_MODE_CLAUDE_BIN", ""):
        kwargs["cli_path"] = dj.AGENT_MODE_CLAUDE_BIN
    if stderr_sink is not None:
        kwargs["stderr"] = stderr_sink

    # Native OS bash sandbox. Off by default until verified on the target
    # platform — enabling it where unsupported would fail every run.
    if getattr(dj, "AGENT_MODE_SANDBOX", False):
        kwargs["sandbox"] = {
            "enabled": True,
            "autoAllowBashIfSandboxed": False,
            "allowUnsandboxedCommands": False,
            "enableWeakerNestedSandbox": True,
        }

    if run.resumed_from_id and run.resumed_from and run.resumed_from.session_id:
        kwargs["resume"] = run.resumed_from.session_id
        kwargs["fork_session"] = True

    return ClaudeAgentOptions(**kwargs)
