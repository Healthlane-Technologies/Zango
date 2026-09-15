"""Per-run Claude Code settings file carrying the deny rules.

Passed as ``ClaudeAgentOptions.settings``, which the SDK loads into the
"flag settings" layer — the highest priority among user-controlled settings,
so tenant-authored app code cannot loosen it.

Rule syntax is per the SDK permissions reference, and two details are easy to
get wrong:

* ``//path`` is an **absolute** filesystem path. A single leading slash
  (``/path``) anchors at the rule's source instead, which for these rules
  would be the session cwd — not what we want.
* ``Edit(path)`` governs **every** built-in file-writing tool, including
  ``Write`` and ``NotebookEdit``. A ``Write(path)`` rule is never matched by
  the file permission checks, so writing one would be a silent no-op.

These rules are defence in depth. Glob syntax cannot express "deny everything
except this subtree", so general containment is the PreToolUse path guard in
``guards.py`` (hooks are evaluated before deny rules and a hook deny is
absolute). What we add here are hard blocks on the specific high-value
targets: other tenants' workspaces, the Django project source, the installed
zango package, and the usual credential locations.
"""

from __future__ import annotations

import json
import os

from pathlib import Path


SETTINGS_FILENAME = "agent-run-settings.json"


def _abs_rule(tool: str, path: str, suffix: str = "/**") -> str:
    """Build an absolute-path rule: Tool(//abs/path/**)."""
    resolved = os.path.realpath(str(path))
    return f"{tool}(/{resolved}{suffix})"


def build_permission_rules(
    *,
    workspace_path: str,
    workspaces_root: str,
    base_dir: str,
    project_name: str = "",
) -> dict:
    """Deny rules for one run, plus an allow rule for its own workspace."""
    workspace_real = os.path.realpath(workspace_path)
    deny: list[str] = []

    # Other tenants' workspaces — the highest-value lateral target. Enumerated
    # explicitly because a glob over the root would also match our own.
    try:
        for entry in sorted(os.listdir(workspaces_root)):
            candidate = os.path.join(workspaces_root, entry)
            if not os.path.isdir(candidate):
                continue
            if os.path.realpath(candidate) == workspace_real:
                continue
            deny.append(_abs_rule("Edit", candidate))
            deny.append(_abs_rule("Read", candidate))
    except OSError:
        pass

    # The Django project source (settings.py, urls.py, wsgi.py).
    if project_name:
        deny.append(_abs_rule("Edit", os.path.join(base_dir, project_name)))
    # manage.py itself.
    deny.append(f"Edit(/{os.path.realpath(os.path.join(base_dir, 'manage.py'))})")

    # The installed zango package — editable installs point at a real repo.
    try:
        import zango

        pkg = Path(zango.__file__).resolve().parent
        deny.append(_abs_rule("Edit", str(pkg)))
    except Exception:  # noqa: BLE001
        pass

    # Credentials, in this project and in the user's home.
    home = os.path.expanduser("~")
    for pattern in (".env", ".env.*"):
        deny.append(f"Read(/{os.path.realpath(os.path.join(base_dir, pattern))})")
        deny.append(
            f"Read(/{os.path.realpath(os.path.join(os.path.dirname(base_dir), pattern))})"
        )
    for sub in (".ssh", ".aws", ".config/anthropic", ".claude"):
        deny.append(_abs_rule("Read", os.path.join(home, sub)))
        deny.append(_abs_rule("Edit", os.path.join(home, sub)))

    # Network egress: the agent has no reason to fetch anything.
    deny.append("WebFetch")
    deny.append("WebSearch")

    return {
        "allow": [_abs_rule("Edit", workspace_real), _abs_rule("Read", workspace_real)],
        "deny": sorted(set(deny)),
    }


def write_run_settings(
    *,
    run_dir: str,
    workspace_path: str,
    workspaces_root: str,
    base_dir: str,
    project_name: str = "",
) -> str:
    """Write the per-run settings JSON. Returns its path."""
    os.makedirs(run_dir, exist_ok=True)
    payload = {
        "permissions": build_permission_rules(
            workspace_path=workspace_path,
            workspaces_root=workspaces_root,
            base_dir=base_dir,
            project_name=project_name,
        )
    }
    path = os.path.join(run_dir, SETTINGS_FILENAME)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=2, sort_keys=True)
    return path
