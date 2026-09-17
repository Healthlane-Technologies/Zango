"""Containment for an Agent Mode run: path sandbox and bash policy.

Layering (see the plan's Safety section):

  1. ``permissions.deny`` rules written to a per-run settings JSON and passed
     as ``ClaudeAgentOptions.settings`` — the highest-priority
     user-controlled layer, so tenant app code cannot loosen it.
  2. The native ``sandbox`` setting, where the platform supports it.
  3. These PreToolUse hooks — defence in depth, and the thing that produces a
     legible "blocked" row in the transcript.

Honest scoping: in production the container is the real boundary; in local
development (a bare virtualenv) these hooks plus the deny rules are the only
containment. They stop a *confused* agent, not a determined one.

Hook callbacks run on the SDK's event loop, so nothing here may touch the
Django ORM (it would raise SynchronousOnlyOperation, and asgiref's executor
would hand it a public-schema connection). Denials are pushed to a
thread-safe sink instead.
"""

from __future__ import annotations

import os
import re
import shlex

from typing import Any, Callable


# Tools whose inputs name filesystem paths we must contain.
WRITE_TOOLS = frozenset({"Write", "Edit", "MultiEdit", "NotebookEdit"})
READ_TOOLS = frozenset({"Read", "Glob", "Grep"})
PATH_TOOLS = WRITE_TOOLS | READ_TOOLS

# Input keys that carry a path, per tool.
_PATH_KEYS = ("file_path", "path", "notebook_path", "filePath")
# Grep/Glob scope their search with these.
_DIR_KEYS = ("dir", "directory")

# Commands that are never acceptable, matched anywhere in the command string
# (including after ;, &&, |, backticks and $( ) ). Ordered roughly by risk.
_BASH_HARD_DENY = [
    (r"\bdocker(-compose)?\b", "docker is managed by the platform"),
    (r"\bkubectl\b", "kubectl is not permitted"),
    (r"\b(sudo|su)\b", "privilege escalation is not permitted"),
    (r"\b(systemctl|service)\b", "service control is not permitted"),
    (r"manage\.py", "migrations and sync are run by the platform, not the agent"),
    (r"\bdjango-admin\b", "django-admin is not permitted"),
    (r"(^|[\s;&|])zango\b", "the zango CLI is run by the platform, not the agent"),
    (r"\bcelery\b", "celery is not permitted"),
    (r"\bgunicorn\b", "gunicorn is not permitted"),
    (
        r"\b(pip|pip3|uv|uvx|poetry|pipenv|conda)\b",
        "package installation is not permitted",
    ),
    (
        r"\b(yarn|pnpm|bun|bunx)\b",
        "use npm/npx; other Node package managers are not permitted",
    ),
    (
        r"\bgit\s+(commit|push|reset|checkout|clean|rebase|merge)\b",
        "mutating git is not permitted",
    ),
    (r"\b(crontab|at)\b", "scheduling is not permitted"),
    (r"\b(ssh|scp|sftp|rsync|nc|netcat|telnet)\b", "remote access is not permitted"),
    (r"\bchown\b", "chown is not permitted"),
    (r"\bchmod\s+777\b", "chmod 777 is not permitted"),
    (r"\bmkfs\b", "mkfs is not permitted"),
    (
        r"rm\s+(-[A-Za-z]*\s+)*-?[A-Za-z]*[rf]{2}[A-Za-z]*\s+/(?!\w)",
        "rm -rf / is not permitted",
    ),
    (r":\(\)\s*\{", "fork bomb pattern"),
    (r">\s*/etc/", "writing to /etc is not permitted"),
    (r"/dev/(tcp|udp)/", "raw network redirection is not permitted"),
    (r"\bANTHROPIC_API_KEY\b", "the API key must not be referenced"),
    (r"^\s*(env|printenv|set)\s*$", "dumping the environment is not permitted"),
    # Interpreters: the easiest sandbox bypass. Read/Write/Edit/Grep cover
    # every legitimate need.
    (
        r"\b(python|python3|node|deno|ruby|perl|php|lua|Rscript)\b",
        "interpreters are not permitted; use the Read/Write/Edit/Grep tools",
    ),
    (r"\b(bash|sh|zsh|fish|eval|exec)\s+-c\b", "nested shells are not permitted"),
    # Write vectors that would bypass the (unguarded) Bash path checks.
    (r"\bsed\b[^|;&]*\s-[A-Za-z]*i", "sed -i writes in place; use the Edit tool"),
    (r"\b(tee|dd|truncate|shred|install)\b", "use the Write tool instead"),
    (
        r"\b(cp|mv|rm|rmdir|mkdir|touch|ln)\b",
        "file manipulation must go through the Write/Edit tools, which are path-guarded",
    ),
]
_BASH_HARD_DENY_RE = [(re.compile(p, re.I), m) for p, m in _BASH_HARD_DENY]

# Leading executables permitted for each command segment. Read-only or
# workspace-local file manipulation only.
# Read-only only. Anything that can write is deliberately absent: the Bash
# tool is NOT path-guarded (arguments are not resolved against the workspace),
# so a writable command here would silently defeat path containment. Writes
# must go through Write/Edit/MultiEdit, which are guarded.
_BASH_ALLOWED = frozenset(
    """
ls cat head tail wc sort uniq cut tr grep rg egrep fgrep find tree file stat
awk jq diff comm cmp basename dirname realpath readlink echo printf true
false test pwd date which type seq cd sed curl
""".split()
)

# Hosts curl may reach when the caller supplies an allow-list. The agent needs
# curl for the AppBuilder route/menu API, which lives on the app's own domain;
# it has no reason to reach anything else.
_LOCAL_HOSTS = frozenset({"localhost", "127.0.0.1", "0.0.0.0", "[::1]", "::1"})
_URL_RE = re.compile(r'https?://([^/\s"\')]+)', re.I)

# git subcommands that only read.
_GIT_READONLY = frozenset(
    "status diff log show blame branch tag remote ls-files rev-parse describe "
    "shortlog cat-file for-each-ref stash".split()
)


def _split_segments(command: str) -> list:
    r"""Split on ; | && || and newlines, but only OUTSIDE quotes.

    A naive regex split breaks `grep -n "^a \|^b" f` at the pipe inside the
    pattern, leaving a fragment that looks like a command — observed on the
    first successful run.
    """
    segments, buf, quote, i = [], [], None, 0
    while i < len(command):
        ch = command[i]
        if quote:
            buf.append(ch)
            if ch == quote and command[i - 1 : i] != "\\":
                quote = None
            i += 1
            continue
        if ch in "'\"":
            quote = ch
            buf.append(ch)
            i += 1
            continue
        if command.startswith("&&", i) or command.startswith("||", i):
            segments.append("".join(buf))
            buf = []
            i += 2
            continue
        if ch in ";|\n":
            segments.append("".join(buf))
            buf = []
            i += 1
            continue
        buf.append(ch)
        i += 1
    segments.append("".join(buf))
    return [seg.strip() for seg in segments if seg.strip()]


def _strip_quoted(command: str) -> str:
    """Blank out quoted spans, so scans never match inside a string literal."""
    out, quote = [], None
    for ch in command:
        if quote:
            out.append(" " if ch != quote else ch)
            if ch == quote:
                quote = None
            continue
        if ch in "'\"":
            quote = ch
        out.append(ch)
    return "".join(out)


def resolve_within_any(path: str, roots) -> tuple[bool, str]:
    """True when *path* resolves inside any of *roots*."""
    if not path:
        return True, ""
    reasons = []
    for root in roots:
        ok, why = resolve_within(path, root)
        if ok:
            return True, ""
        reasons.append(why)
    return False, reasons[0] if reasons else "path not permitted"


def resolve_within(path: str, root: str) -> tuple[bool, str]:
    """True when *path* resolves inside *root*.

    Uses realpath on both sides plus commonpath, which defeats ``..``
    traversal and symlinks that point out of the tree. String prefixing
    does not.
    """
    if not path:
        return True, ""
    try:
        real_root = os.path.realpath(root)
        candidate = path if os.path.isabs(path) else os.path.join(real_root, path)
        real_path = os.path.realpath(candidate)
        if real_path == real_root:
            return True, ""
        if os.path.commonpath([real_root, real_path]) == real_root:
            return True, ""
        return False, f"{path!r} resolves outside the app workspace"
    except Exception as exc:  # noqa: BLE001 - unresolvable => refuse
        return False, f"could not resolve {path!r}: {type(exc).__name__}: {exc}"


def extract_paths(tool_name: str, tool_input: dict) -> list[str]:
    """Every filesystem path referenced by a tool call."""
    paths: list[str] = []
    if not isinstance(tool_input, dict):
        return paths
    for key in _PATH_KEYS + _DIR_KEYS:
        value = tool_input.get(key)
        if isinstance(value, str) and value:
            paths.append(value)
    # MultiEdit carries a list of per-file edits.
    for entry in tool_input.get("edits") or []:
        if isinstance(entry, dict):
            for key in _PATH_KEYS:
                value = entry.get(key)
                if isinstance(value, str) and value:
                    paths.append(value)
    return paths


# manage.py subcommands the agent may run itself. Deliberately a closed set:
# these let it iterate on migrations and see the errors, which the runner's
# post-run pipeline cannot give it. Everything else about manage.py — and the
# `python` interpreter generally — stays denied.
_MANAGE_COMMANDS = frozenset(
    {"ws_makemigration", "ws_migrate", "ws_sync", "sync_static", "collectstatic"}
)
# The agent's cwd is the workspace, so manage.py is normally referenced by
# absolute path; both forms are accepted.
# Frontend scaffolding and build. Off unless AGENT_MODE_ALLOW_FRONTEND_BUILD
# is set AND Node is actually present, because `npm install` executes package
# lifecycle scripts — arbitrary code from the registry. A closed set of
# invocations, same approach as the manage.py allowance.
_NPM_RE = re.compile(r"^(?:npm|npx)\s+(.*)$", re.I)
# Design-system packages the agent may add. Deliberately a closed, exact-name
# set rather than a general `npm install <anything>`: installing a package runs
# its lifecycle scripts, so the name is the security boundary. Each entry is
# here because a polished UI genuinely needs it and nothing in the scaffold
# provides it.
#
# Not listed, because they are already installed transitively via @zango-core
# and need no install at all: lucide-react.
_NPM_DESIGN_PACKAGES = (
    "echarts",
    "echarts-for-react",
    "recharts",
    "date-fns",
    "clsx",
    "tailwind-merge",
)
# Matches `install <pkg>` / `i <pkg>` / `add <pkg>` for one or more allowlisted
# names, each optionally @-pinned. Anything else falls through to the denial.
_NPM_PKG = (
    r"(?:" + "|".join(re.escape(n) for n in _NPM_DESIGN_PACKAGES) + r")(?:@[\w.\-^~]+)?"
)
_NPM_ALLOWED = (
    re.compile(r"^@zango-core/create-zango-app\s+\S+\s*$", re.I),  # npx scaffold
    re.compile(r"^install\s*$", re.I),
    re.compile(r"^ci\s*$", re.I),
    re.compile(rf"^(?:install|i|add)\s+(?:{_NPM_PKG}\s*)+$", re.I),
    re.compile(r"^run\s+build:zango\s*$", re.I),
    re.compile(r"^run\s+build\s*$", re.I),
    re.compile(r"^-v$|^--version$", re.I),
)


def _is_allowed_npm(segment: str, allow_frontend: bool) -> tuple[bool, str]:
    """Recognise the handful of npm/npx commands the frontend setup needs."""
    match = _NPM_RE.match(segment.strip())
    if not match:
        return False, ""
    if not allow_frontend:
        return False, (
            "Node tooling is disabled for this app. Set "
            "AGENT_MODE_ALLOW_FRONTEND_BUILD=True and ensure node is installed."
        )
    rest = match.group(1).strip()
    for pattern in _NPM_ALLOWED:
        if pattern.match(rest):
            return True, ""
    return False, (
        f"`npm/npx {rest[:40]}` is not permitted; only the documented "
        "scaffold, install and build commands are"
    )


# The one write the agent must make through Bash: moving its own frontend build
# into the workspace's static dir so `sync_static` can publish it. It cannot go
# through the Write tool -- the bundle is multi-megabyte minified JS -- and
# `sync_static` only ever reads from <workspace>/static, so without this the
# built frontend is never served no matter what app.html points at.
#
# Deliberately a single closed form rather than a general `cp`: both operands
# are fixed, workspace-relative literals, so even though Bash arguments are not
# path-guarded there is nothing here to point outside the workspace. No flags
# beyond -r, no globs, no second source. Anything else still falls through to
# the hard-deny scan below.
_DEPLOY_BUILD_RE = re.compile(
    r"^cp\s+(?:-r\s+|-R\s+)?frontend/zango-build/\.?\s+static/js/?$"
)


def _is_allowed_deploy(segment: str, allow_frontend: bool) -> tuple[bool, str]:
    """Recognise the single permitted frontend-build deploy copy."""
    if not _DEPLOY_BUILD_RE.match(segment.strip()):
        return False, ""
    if not allow_frontend:
        return False, (
            "Node tooling is disabled for this app, so there is no frontend "
            "build to deploy."
        )
    return True, ""


_MANAGE_RE = re.compile(
    r"^(?:python3?|\S*/python3?)\s+(?:\S*/)?manage\.py\s+([a-z_]+)\b(.*)$", re.I
)


def _is_allowed_manage(segment: str, app_name: str) -> tuple[bool, str]:
    """Recognise `python manage.py <allowed-cmd> [<this app>] [--flags]`.

    Anything else that mentions manage.py or python falls through to the
    normal deny path, so `python -c` stays blocked.
    """
    match = _MANAGE_RE.match(segment.strip())
    if not match:
        return False, ""
    command, rest = match.group(1), match.group(2)
    if command not in _MANAGE_COMMANDS:
        return False, f"manage.py {command!r} is not permitted in Agent Mode"
    # Any bare (non-flag) argument must name this app.
    for token in rest.split():
        if token.startswith("-"):
            continue
        if app_name and token != app_name:
            return False, (
                f"manage.py {command} may only target {app_name!r}, not {token!r}"
            )
    return True, ""


# Character devices that are always safe targets.
_NULL_PATHS = frozenset({"/dev/null", "/dev/stdout", "/dev/stderr", "/dev/zero"})


def _explicit_paths(tokens) -> list:
    """Tokens that name an absolute or home-relative filesystem path."""
    out = []
    for tok in tokens:
        cleaned = tok.strip("\"'")
        if cleaned in _NULL_PATHS:
            continue
        if cleaned.startswith("~") or cleaned.startswith("/"):
            out.append(os.path.expanduser(cleaned))
    return out


def _url_hosts(segment: str) -> list:
    hosts = []
    for match in _URL_RE.finditer(segment):
        host = match.group(1)
        if "@" in host:
            host = host.rsplit("@", 1)[1]
        hosts.append(host.split(":")[0].strip("\"'"))
    return hosts


def check_bash(
    command: str,
    read_roots=None,
    allowed_hosts=None,
    app_name: str = "",
    allow_frontend: bool = False,
) -> tuple[bool, str]:
    """Two-tier bash policy. Returns (allowed, reason_if_denied).

    When *read_roots* is supplied, absolute paths named in the command must
    resolve inside one of them. Bash is otherwise a general read primitive:
    the Read-tool deny rules do not constrain `cat`, so without this
    `cat ~/.ssh/id_rsa` would be permitted. Relative paths are left to the
    process cwd, which is the workspace.
    """
    if not command or not command.strip():
        return True, ""

    # Command substitution hides a second command from segment splitting.
    if re.search(r"\$\(|`", command):
        return False, "command substitution is not permitted"

    # Output redirection can write outside the workspace. Permit only the
    # harmless idioms (>/dev/null, 2>&1, 2>/dev/null).
    for match in re.finditer(r"(\d?)>>?\s*(&\d|[^\s;|&]+)", _strip_quoted(command)):
        target = match.group(2)
        if target.startswith("&"):
            continue
        if target in ("/dev/null", "/dev/stdout", "/dev/stderr"):
            continue
        return False, (
            f"redirecting output to {target!r} is not permitted; use the Write tool"
        )

    for segment in _split_segments(command):
        segment = segment.strip()
        if not segment:
            continue

        # The narrow manage.py allowance is checked first; a rejection here is
        # final so it cannot be smuggled past the hard-deny scan.
        allowed_manage, manage_reason = _is_allowed_manage(segment, app_name)
        if manage_reason:
            return False, manage_reason
        if allowed_manage:
            continue

        allowed_npm, npm_reason = _is_allowed_npm(segment, allow_frontend)
        if npm_reason:
            return False, npm_reason
        if allowed_npm:
            continue

        allowed_deploy, deploy_reason = _is_allowed_deploy(segment, allow_frontend)
        if deploy_reason:
            return False, deploy_reason
        if allowed_deploy:
            continue

        for pattern, message in _BASH_HARD_DENY_RE:
            if pattern.search(segment):
                return False, message

        try:
            tokens = shlex.split(segment)
        except ValueError:
            # Real grep/awk patterns routinely contain quoting shlex cannot
            # parse. The hard-deny scan above has already run over the whole
            # command, so fall back to the leading bare word rather than
            # rejecting a legitimate search outright.
            tokens = (
                shlex.split(segment, posix=False)
                if _safe_posix_split(segment)
                else segment.split()
            )
        # Drop VAR=value prefixes.
        while tokens and re.match(r"^[A-Za-z_][A-Za-z0-9_]*=", tokens[0]):
            tokens = tokens[1:]
        if not tokens:
            continue
        exe = os.path.basename(tokens[0])
        if exe == "git":
            sub = tokens[1] if len(tokens) > 1 else ""
            if sub not in _GIT_READONLY:
                return False, f"git {sub!r} is not a read-only subcommand"
            continue
        if exe not in _BASH_ALLOWED:
            return False, (
                f"{exe!r} is not permitted in Agent Mode; "
                "use the Read/Write/Edit/Grep tools instead"
            )
        if exe in ("curl", "wget"):
            permitted = set(_LOCAL_HOSTS) | {h.lower() for h in (allowed_hosts or [])}
            for host in _url_hosts(segment):
                if host.lower() not in permitted:
                    return False, (
                        f"{host!r} is not reachable from Agent Mode; curl may "
                        "only call this app's own domain or localhost"
                    )
        if read_roots:
            for path in _explicit_paths(tokens[1:]):
                ok, _ = resolve_within_any(path, read_roots)
                if not ok:
                    return False, (
                        f"{path!r} is outside the app workspace; "
                        "bash may only touch workspace paths"
                    )
    return True, ""


def _safe_posix_split(segment: str) -> bool:
    try:
        shlex.split(segment, posix=False)
        return True
    except ValueError:
        return False


def _deny(reason: str) -> dict:
    """PreToolUse deny, in the SDK's verified output shape."""
    return {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": reason,
        }
    }


def make_pre_tool_use_guard(
    workspace_root: str,
    sink: Callable[[str, str, dict], None] | None = None,
    read_roots=None,
    allowed_hosts=None,
    app_name: str = "",
    allow_frontend: bool = False,
):
    """Build the PreToolUse hook enforcing path containment and bash policy.

    Writes are confined to ``workspace_root``. Reads additionally allow
    ``read_roots`` — in practice the vendored skill's own directory. Without
    that the agent is denied its own reference documentation, which is the
    entire reason the skill is vendored; the first real run failed this way.

    ``sink(tool_name, reason, tool_input)`` is called on every denial. It must
    be thread-safe and must not touch the ORM — in the runner it is a
    ``queue.Queue.put``.
    """
    read_allowed = [workspace_root, *(read_roots or [])]

    async def guard(
        input_data: dict[str, Any], tool_use_id: str | None, context: Any
    ) -> dict:
        tool_name = input_data.get("tool_name") or ""
        tool_input = input_data.get("tool_input") or {}

        reason = ""
        if tool_name in PATH_TOOLS:
            # Writes: workspace only. Reads: workspace + the skill's docs.
            roots = [workspace_root] if tool_name in WRITE_TOOLS else read_allowed
            for path in extract_paths(tool_name, tool_input):
                ok, why = resolve_within_any(path, roots)
                if not ok:
                    reason = f"{tool_name}: {why}"
                    break
        elif tool_name == "Bash":
            ok, why = check_bash(
                tool_input.get("command") or "",
                read_roots=read_allowed,
                allowed_hosts=allowed_hosts,
                app_name=app_name,
                allow_frontend=allow_frontend,
            )
            if not ok:
                reason = f"Bash blocked: {why}"

        if reason:
            if sink is not None:
                try:
                    sink(tool_name, reason, tool_input)
                except Exception:  # noqa: BLE001 - never break the run
                    pass
            return _deny(reason)
        return {}

    return guard
