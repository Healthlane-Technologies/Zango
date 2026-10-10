"""The build skill's own checker, run while the spec is being written.

A template's build skill may ship a checker (``scripts/spec_check.py`` in
zango-app-studio) that the build runs first and stops on. Our JSON Schema and
rules cannot express everything it checks — prose cut at an unquoted comma,
formats it does not know, modules that link in a cycle — so a spec the panel
called valid could still fail the build. Running the same checker during
validation surfaces those problems to the analyst and the user while they can
still fix them, and blocks approval on them.

It takes a fraction of a second; results are cached by spec content.
"""

from __future__ import annotations

import hashlib
import logging
import os
import re
import subprocess
import sys
import tempfile

from pathlib import Path


logger = logging.getLogger("zango.app_templates")

CHECKER = Path("scripts") / "spec_check.py"
TIMEOUT_SECONDS = 30
# "ERROR  <where>: <message>", "warn   …", "intent  …", each optionally
# followed by an indented "fix: …" line.
_LINE = re.compile(r"^(error|warn(?:ing)?|intent)\s+(.+?):\s+(.*)$", re.I)
_FIX = re.compile(r"^\s+fix:\s+(.*)$", re.I)
_cache: dict = {}
_CACHE_SIZE = 64


def checker_for(template) -> Path | None:
    """The build skill's checker for a TemplateView, if it has one on disk."""
    name = getattr(template, "build_skill_name", "")
    root = getattr(template, "build_plugin_dir", "") or getattr(template, "plugin_dir", "")
    if not name or not root:
        return None
    path = Path(root) / "skills" / name / CHECKER
    return path if path.is_file() else None


def plain_yaml(doc) -> str:
    """The spec as plain YAML, the way the build re-emits it for the checker."""
    import yaml

    return yaml.safe_dump(doc, sort_keys=False, allow_unicode=True, width=10_000)


def _issue(level: str, where: str, message: str) -> dict:
    return {
        "level": level,
        "path": "",
        "message": f"{where}: {message}" if where else message,
        "code": "build_check",
        "structural": False,
    }


def build_issues(doc, template) -> list:
    """What the build skill's checker says about ``doc`` (a plain mapping)."""
    checker = checker_for(template)
    if checker is None or not isinstance(doc, dict):
        return []
    text = plain_yaml(doc)
    key = (str(checker), hashlib.sha256(text.encode("utf-8")).hexdigest())
    if key in _cache:
        return [dict(i) for i in _cache[key]]

    with tempfile.TemporaryDirectory(prefix="zas-check-") as tmp:
        spec = Path(tmp) / "app_spec.yaml"
        spec.write_text(text, encoding="utf-8")
        env = {k: v for k, v in os.environ.items() if "ANTHROPIC" not in k}
        try:
            proc = subprocess.run(
                [sys.executable, str(checker), str(spec), "--workspace", tmp],
                cwd=str(checker.parent),
                capture_output=True,
                text=True,
                timeout=TIMEOUT_SECONDS,
                env=env,
            )
        except (OSError, subprocess.TimeoutExpired) as exc:
            logger.warning("app_templates: build checker did not run: %s", exc)
            return [_issue("warning", "", f"The build checker could not run ({exc}).")]

    issues = []
    for line in (proc.stdout or "").splitlines():
        fix = _FIX.match(line)
        if fix and issues:
            issues[-1]["message"] += f" (fix: {fix.group(1).strip()})"
            continue
        match = _LINE.match(line.strip())
        if match:
            level = "error" if match.group(1).lower() == "error" else "warning"
            issues.append(_issue(level, match.group(2), match.group(3)))
    if proc.returncode == 2:
        issues.append(
            _issue("error", "", "The build checker could not read the spec: " + _tail(proc))
        )
    elif proc.returncode not in (0, 1):
        issues.append(_issue("error", "", "The build checker failed: " + _tail(proc)))
    elif proc.returncode == 1 and not any(i["level"] == "error" for i in issues):
        issues.append(_issue("error", "", "The build checker found errors: " + _tail(proc)))

    if len(_cache) >= _CACHE_SIZE:
        _cache.pop(next(iter(_cache)))
    _cache[key] = [dict(i) for i in issues]
    return issues


def _tail(proc) -> str:
    text = (proc.stderr or proc.stdout or "").strip().splitlines()
    return (text[-1] if text else f"exit {proc.returncode}")[:300]
