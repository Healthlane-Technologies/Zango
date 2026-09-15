"""Post-run migration and sync pipeline.

Runner-owned, not agent-owned. That single rule buys three things: the
largest Bash privilege hole stays closed, the steps happen exactly once, and
every exit code and stderr line lands in the transcript as structured rows
instead of buried in agent prose.

Each step is a **subprocess**, never `call_command`, for two verified reasons:

1. Workspace code is loaded through pluginbase with ``persist=True`` and
   cached in ``sys.modules``. ``ws_makemigration`` must *see* the models the
   agent just wrote; an in-process call in a worker that already loaded this
   workspace will not.
2. ``ws_makemigration`` (line ~44) and ``ws_migrate`` (line ~23) both wrap the
   tenant lookup in ``while True:`` and fall into ``input()`` on an unknown
   app name. In-process that hangs a Celery worker forever. Here,
   ``stdin=DEVNULL`` turns it into an immediate EOFError, and there is a
   per-step timeout on top.
"""

from __future__ import annotations

import os
import subprocess
import sys
import time

from dataclasses import dataclass, field


DEFAULT_STEP_TIMEOUT = 300
OUTPUT_TAIL_CHARS = 4_000
# Never hand the Anthropic credential to a manage.py subprocess.
STRIPPED_ENV = ("ANTHROPIC_API_KEY", "ANTHROPIC_AUTH_TOKEN", "CLAUDE_CODE_OAUTH_TOKEN")


@dataclass
class StepResult:
    step: str
    command: list = field(default_factory=list)
    returncode: int = 0
    duration_ms: int = 0
    stdout_tail: str = ""
    stderr_tail: str = ""
    skipped_reason: str = ""

    @property
    def ran(self) -> bool:
        return not self.skipped_reason

    @property
    def ok(self) -> bool:
        return self.skipped_reason or self.returncode == 0

    def to_dict(self) -> dict:
        return {
            "step": self.step,
            "returncode": self.returncode,
            "duration_ms": self.duration_ms,
            "skipped_reason": self.skipped_reason,
            "stdout_tail": self.stdout_tail,
            "stderr_tail": self.stderr_tail,
        }


def _clean_env() -> dict:
    return {k: v for k, v in os.environ.items() if k not in STRIPPED_ENV}


def _tail(text: str) -> str:
    text = text or ""
    return text if len(text) <= OUTPUT_TAIL_CHARS else "…" + text[-OUTPUT_TAIL_CHARS:]


def run_step(
    step: str, args: list, base_dir: str, timeout: int = DEFAULT_STEP_TIMEOUT
) -> StepResult:
    command = [sys.executable, "manage.py", *args]
    started = time.monotonic()
    try:
        proc = subprocess.run(  # noqa: S603 - fixed argv, no shell
            command,
            cwd=base_dir,
            env=_clean_env(),
            stdin=subprocess.DEVNULL,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
        return StepResult(
            step=step,
            command=command,
            returncode=proc.returncode,
            duration_ms=int((time.monotonic() - started) * 1000),
            stdout_tail=_tail(proc.stdout),
            stderr_tail=_tail(proc.stderr),
        )
    except subprocess.TimeoutExpired:
        return StepResult(
            step=step,
            command=command,
            returncode=-1,
            duration_ms=int((time.monotonic() - started) * 1000),
            stderr_tail=f"step timed out after {timeout}s",
        )
    except Exception as exc:  # noqa: BLE001
        return StepResult(
            step=step,
            command=command,
            returncode=-1,
            duration_ms=int((time.monotonic() - started) * 1000),
            stderr_tail=f"{type(exc).__name__}: {exc}",
        )


def plan_steps(changes, app_name: str) -> list:
    """Decide which steps the file diff justifies. (step, argv) pairs."""
    paths = changes.all_paths() if changes else []
    touched_models = any(p.endswith("models.py") for p in paths)
    touched_migrations = any(
        p.startswith("migrations/") or "/migrations/" in p for p in paths
    )
    touched_sync = any(
        p.endswith(("policies.json", "tasks.py", "tools.py", "settings.json"))
        for p in paths
    )
    touched_static = any(p.startswith("static/") or "/static/" in p for p in paths)

    steps = []
    if touched_models:
        steps.append(("ws_makemigration", ["ws_makemigration", app_name, "--noinput"]))
    if touched_models or touched_migrations:
        steps.append(("ws_migrate", ["ws_migrate", app_name, "--noinput"]))
    if touched_sync:
        steps.append(("ws_sync", ["ws_sync", app_name]))
    if touched_static:
        steps.append(("sync_static", ["sync_static", app_name]))
    return steps


def run_post_steps(*, app_name: str, base_dir: str, changes, emit=None) -> list:
    """Run the pipeline in order. Emits progress if a callback is supplied."""
    results = []
    planned = plan_steps(changes, app_name)

    if not planned:
        if emit:
            emit(
                "post_step", "No migration or sync needed — no relevant files changed."
            )
        return results

    for step, args in planned:
        if emit:
            emit("post_step", f"Running {step} …", data={"step": step})
        result = run_step(step, args, base_dir)
        results.append(result)
        if emit:
            for line in (result.stdout_tail or "").splitlines()[-40:]:
                if line.strip():
                    emit("stdout", line, data=None)
            for line in (result.stderr_tail or "").splitlines()[-40:]:
                if line.strip():
                    emit("stderr", line, data=None, is_error=result.returncode != 0)
            emit(
                "post_step",
                f"{step} finished with exit {result.returncode} "
                f"in {result.duration_ms}ms",
                data=result.to_dict(),
                is_error=result.returncode != 0,
            )
        # A failed migration makes every later step meaningless.
        if result.returncode != 0 and step in ("ws_makemigration", "ws_migrate"):
            if emit:
                emit(
                    "post_step",
                    f"Stopping the pipeline: {step} failed.",
                    is_error=True,
                )
            break
    return results


def requires_restart(changes) -> bool:
    """Changes the running processes cannot pick up without a restart."""
    paths = changes.all_paths() if changes else []
    return any(p.endswith(("models.py", "tasks.py", "settings.json")) for p in paths)
