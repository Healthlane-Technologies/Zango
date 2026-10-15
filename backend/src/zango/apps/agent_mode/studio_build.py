"""Studio builds: the platform runs the zango-app-studio skill's scripts; the agent writes code.

The App Studio build skill is written for a developer's machine: it runs its
own Python scripts (``spec_check.py``, ``zango_platform.py``, the ``zas_test``
layers), copies its runtime into the app and pins npm packages. The build
agent runs in a sandbox that allows none of that — no interpreter, no ``cp``,
a closed set of npm and manage.py commands, no platform credentials.

So the build is split (``references/server-mode.md`` in the skill tells the
agent the same):

* before the agent — :meth:`StudioBuild.prepare`: lint and resolve the spec,
  copy the runtime, prepare the frontend;
* the agent — writes the modules, holes, pages and test scenarios;
* after the agent — :meth:`StudioBuild.finish`: migrations, roles, policy and
  task sync, test users, static files, AppBuilder routes and menus, the hole
  audit and the test layers, with fix rounds that resume the agent's session.

Every script runs as a subprocess of the platform's own interpreter, with the
Anthropic credentials stripped from its environment. The platform API is
reached with a service account minted for the run (:func:`service_account`):
its password only ever exists in a subprocess environment, never in the
agent's context or the run's events, and the account is disabled afterwards.
"""

from __future__ import annotations

import json
import logging
import os
import re
import secrets
import shutil
import string
import subprocess
import sys
import time

from contextlib import contextmanager
from dataclasses import dataclass, field
from pathlib import Path

from .postrun import STRIPPED_ENV, StepResult, _tail, run_step


logger = logging.getLogger("zango.agent_mode")

STUDIO_MARKER = "scripts/spec_check.py"
STEP_PREFIX = "studio:"
SCRIPT_TIMEOUT = 600
NPM_TIMEOUT = 900
TEST_TIMEOUT = 1800
REPORT_SUMMARY_CHARS = 6_000
DIGEST_MAX_ITEMS = 40
DEFAULT_PLATFORM_URL = "http://localhost:8000"
PLAYWRIGHT_REASON = (
    "Playwright is not installed in the platform environment "
    "(pip install playwright && python -m playwright install chromium)"
)
CRUD_VERSION = "2.0.0"
LUCIDE_VERSION = "1.31.0"
# Declared list views (SPEC_EXTENSIONS.md): their switcher label and lucide icon.
VIEW_LABELS = {
    "table": ("Table", "table"),
    "kanban": ("Board", "kanban"),
    "cards": ("Cards", "layout-grid"),
    "calendar": ("Calendar", "calendar"),
    "timeline": ("Timeline", "gantt-chart"),
}
# A custom view shorter than this is a stub, whatever it says.
VIEW_MIN_CHARS = 600
BASE_PROXY_ROUTES = ["/api", "/zango", "/appbuilder", "/crud", "/workflow"]

# Test layers in the order the skill runs them. ``browser`` layers need
# Playwright; ``app`` layers sign in to the running app as the test users.
LAYERS = (
    # name, runner, needs browser, needs the app
    ("app_shell", "app_shell", False, False),
    ("views", "views", False, False),
    ("audit_holes", "audit", False, False),
    ("design_lint", "zas_test.design", False, False),
    ("api", "zas_test.api", False, True),
    ("ui", "zas_test.ui", True, True),
    ("design", "zas_test.design", True, True),
    ("scenarios", "zas_test.scenarios", False, True),
)
DESIGN_BROWSER_GROUPS = ("gallery", "tokens", "tree", "layout", "parity")
# Preview parity failures go to the fix rounds, then stay in the report as gaps, never failing the build.
NON_FAILING = ("design.parity",)
APP_LAYERS = tuple(name for name, _, _, needs_app in LAYERS if needs_app)
BROWSER_LAYERS = tuple(name for name, _, browser, _ in LAYERS if browser)
# The one bring-up step that needs the app reachable on its own domain.
HELD_STEP = "appbuilder"
LOCAL_HOSTS = {"localhost", "127.0.0.1", "0.0.0.0", "::1"}
# zas_test.api result ids start with a singular group name.
API_GROUP = {
    "access": "access",
    "create": "create",
    "transition": "transitions",
    "tag": "tags",
    "row_action": "row_actions",
    "scoping": "scoping",
    "detail": "detail",
}


class StudioError(Exception):
    """A studio build that cannot continue; ``error_type`` goes on the run."""

    def __init__(self, error_type: str, message: str):
        super().__init__(message)
        self.error_type = error_type


def is_studio(template_build) -> bool:
    """Whether a template build uses the App Studio skill (and so this pipeline)."""
    skill_dir = getattr(template_build, "skill_dir", "") if template_build else ""
    return bool(skill_dir) and (Path(skill_dir) / STUDIO_MARKER).is_file()


def platform_url() -> str:
    from django.conf import settings

    return (
        getattr(settings, "AGENT_MODE_PLATFORM_URL", "") or DEFAULT_PLATFORM_URL
    ).rstrip("/")


def blocking(layers: dict) -> bool:
    """Whether a failing check fails the build: any failure except preview parity (NON_FAILING)."""
    return any(
        any(not str(f.get("id", "")).startswith(NON_FAILING) for f in x.failures)
        or (x.status == "fail" and not x.failures)
        for x in layers.values()
    )


def fix_rounds() -> int:
    from django.conf import settings

    return max(0, int(getattr(settings, "AGENT_MODE_STUDIO_FIX_ROUNDS", 2)))


# ---------------------------------------------------------------------------
# The per-run service account
# ---------------------------------------------------------------------------


def _service_password() -> str:
    """Satisfies PlatformUserModel.validate_password: 8-18 chars, upper, lower, digit, special."""
    specials = "@$!%*#?&"
    pool = string.ascii_letters + string.digits
    core = [secrets.choice(pool) for _ in range(12)]
    core += [
        secrets.choice(string.ascii_uppercase),
        secrets.choice(string.ascii_lowercase),
        secrets.choice(string.digits),
        secrets.choice(specials),
    ]
    secrets.SystemRandom().shuffle(core)
    return "".join(core)


@contextmanager
def service_account(tenant):
    """A platform user that can reach this one app, for the length of a build.

    Yields the environment the skill's platform script reads
    (``PLATFORM_USERNAME`` / ``PLATFORM_USER_PASSWORD``). Not a superadmin:
    it is scoped to the tenant through ``PlatformUserModel.apps``, which is
    all the App Panel endpoints the script calls require. Disabled on exit
    (inactive, unusable password, no apps), whatever happened in between.
    """
    from django_tenants.utils import schema_context

    from zango.apps.shared.platformauth.models import PlatformUserModel

    email = f"agent-build-{secrets.token_hex(6)}@agent-mode.invalid"
    password = _service_password()
    with schema_context("public"):
        result = PlatformUserModel.create_user(
            name="Agent Mode build",
            email=email,
            mobile="",
            password=password,
            is_superadmin=False,
            require_verification=False,
            app_uuids=[str(tenant.uuid)],
        )
        if not result.get("success"):
            raise StudioError(
                "ServiceAccountFailed",
                f"Could not create the build's service account: {result.get('message')}",
            )
    try:
        yield {"PLATFORM_USERNAME": email, "PLATFORM_USER_PASSWORD": password}
    finally:
        # Deactivated, not deleted: deleting a platform user cascades into
        # tenant-only tables (the audit log), and a disabled row with no
        # password and no apps is as dead as a deleted one, with a trail.
        with schema_context("public"):
            try:
                for user in PlatformUserModel.objects.filter(email=email):
                    user.is_active = False
                    user.set_unusable_password()
                    user.save()
                    user.apps.clear()
                    if user.user_id:
                        type(user.user).objects.filter(pk=user.user_id).update(
                            is_active=False
                        )
            except Exception:  # noqa: BLE001 - never mask the build's own outcome
                logger.exception(
                    "agent_mode: could not disable the build service account"
                )


# ---------------------------------------------------------------------------
# The build
# ---------------------------------------------------------------------------


@dataclass
class LayerResult:
    name: str
    status: str = "pass"  # pass | fail | skip
    counts: dict = field(default_factory=dict)
    failures: list = field(
        default_factory=list
    )  # [{id, title, role, spec_path, detail}]
    groups: list = field(default_factory=list)  # --only groups to re-run
    reason: str = ""

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "status": self.status,
            "counts": self.counts,
            "failures": self.failures[:DIGEST_MAX_ITEMS],
            "reason": self.reason,
        }

    def to_checkpoint(self) -> dict:
        return {**self.to_dict(), "groups": list(self.groups)}

    @classmethod
    def from_checkpoint(cls, data: dict):
        return cls(
            name=data.get("name", ""),
            status=data.get("status", "pass"),
            counts=dict(data.get("counts") or {}),
            failures=list(data.get("failures") or []),
            groups=list(data.get("groups") or []),
            reason=data.get("reason", ""),
        )


@dataclass
class StudioOutcome:
    ok: bool
    bring_up_ok: bool
    layers: dict
    rounds: int
    report: dict
    # A paused build: what the user has to do, and where to continue from.
    pending_actions: list = field(default_factory=list)
    checkpoint: dict | None = None

    @property
    def waiting(self) -> bool:
        return bool(self.pending_actions)

    @property
    def failing(self) -> list:
        return [n for n, layer in self.layers.items() if layer.status == "fail"]

    @property
    def skipped(self) -> list:
        return [n for n, layer in self.layers.items() if layer.status == "skip"]


@dataclass
class StudioBuild:
    skill_dir: str
    workspace: str
    spec_path: str
    run_dir: str
    base_dir: str
    app_name: str
    app_domain: str = ""
    frontend_allowed: bool = False
    platform_url: str = DEFAULT_PLATFORM_URL
    python: str = sys.executable
    first_build: bool = True
    update: bool = False
    frontend_ready: bool = False
    frontend_reason: str = ""
    check_spec: str = ""
    steps: list = field(default_factory=list)
    _pruned: bool = False
    _playwright: bool | None = None
    _reachable: tuple | None = None

    @classmethod
    def for_run(cls, template_build, ctx, run_dir: str):
        from django.conf import settings

        workspace = ctx.workspace_path
        migrations = Path(workspace) / "migrations"
        first = not any(migrations.glob("0*.py")) if migrations.is_dir() else True
        return cls(
            skill_dir=template_build.skill_dir,
            workspace=workspace,
            spec_path=template_build.spec_path,
            run_dir=run_dir,
            base_dir=str(settings.BASE_DIR),
            app_name=ctx.app_name,
            app_domain=getattr(ctx, "primary_domain", "") or "",
            frontend_allowed=bool(getattr(ctx, "frontend_build_allowed", False)),
            platform_url=platform_url(),
            first_build=first,
            update=(Path(workspace) / ".zas" / "spec.resolved.json").is_file(),
        )

    # What a continuation needs to rebuild this object in another worker.
    CHECKPOINT_FIELDS = (
        "skill_dir",
        "workspace",
        "spec_path",
        "run_dir",
        "base_dir",
        "app_name",
        "app_domain",
        "frontend_allowed",
        "platform_url",
        "first_build",
        "update",
        "frontend_ready",
        "frontend_reason",
        "check_spec",
        "_pruned",
    )

    def build_state(self) -> dict:
        return {name: getattr(self, name) for name in self.CHECKPOINT_FIELDS}

    @classmethod
    def from_checkpoint(cls, checkpoint: dict):
        """The build as it was when it paused (in a fresh worker: nothing is cached)."""
        state = dict((checkpoint or {}).get("build") or {})
        return cls(**{k: v for k, v in state.items() if k in cls.CHECKPOINT_FIELDS})

    # -- paths ------------------------------------------------------------

    @property
    def scripts_dir(self) -> str:
        return str(Path(self.skill_dir) / "scripts")

    @property
    def zas_dir(self) -> Path:
        return Path(self.workspace) / ".zas"

    @property
    def config_path(self) -> str:
        return str(Path(self.run_dir) / "zango-config.json")

    # -- running things ---------------------------------------------------

    def env(self, extra: dict | None = None) -> dict:
        env = {
            k: v
            for k, v in os.environ.items()
            if k not in STRIPPED_ENV and not k.startswith("PLATFORM_USER")
        }
        env.update(
            {
                "ZAS_CONFIG": self.config_path,
                "ZANGO_PLATFORM_URL": self.platform_url,
                "PYTHONDONTWRITEBYTECODE": "1",
                "PYTHONUNBUFFERED": "1",
                "PYTHONPATH": os.pathsep.join(
                    p for p in [self.scripts_dir, os.environ.get("PYTHONPATH", "")] if p
                ),
            }
        )
        env.update(extra or {})
        return env

    def _record(self, result: StepResult, emit=None) -> StepResult:
        self.steps.append(result)
        if emit is None:
            return result
        if result.skipped_reason:
            emit(
                "post_step",
                f"{result.step} skipped: {result.skipped_reason}",
                level="warn",
                data=result.to_dict(),
            )
            return result
        for line in (result.stdout_tail or "").splitlines()[-30:]:
            if line.strip():
                emit("stdout", line)
        for line in (result.stderr_tail or "").splitlines()[-30:]:
            if line.strip():
                emit("stderr", line, is_error=result.returncode != 0)
        emit(
            "post_step",
            f"{result.step} finished with exit {result.returncode} in {result.duration_ms}ms",
            level="err" if result.returncode != 0 else "info",
            is_error=result.returncode != 0,
            data=result.to_dict(),
        )
        return result

    def _run(
        self, step, argv, *, cwd=None, timeout=SCRIPT_TIMEOUT, extra_env=None, emit=None
    ):
        if emit is not None:
            emit(
                "post_step",
                f"Running {STEP_PREFIX}{step} …",
                data={"step": STEP_PREFIX + step},
            )
        started = time.monotonic()
        result = StepResult(step=STEP_PREFIX + step, command=list(argv))
        try:
            proc = subprocess.run(  # noqa: S603 - fixed argv, no shell
                list(argv),
                cwd=cwd or self.scripts_dir,
                env=self.env(extra_env),
                stdin=subprocess.DEVNULL,
                capture_output=True,
                text=True,
                timeout=timeout,
                check=False,
            )
            result.returncode = proc.returncode
            result.stdout_tail = _tail(proc.stdout)
            result.stderr_tail = _tail(proc.stderr)
        except subprocess.TimeoutExpired:
            result.returncode = -1
            result.stderr_tail = f"step timed out after {timeout}s"
        except Exception as exc:  # noqa: BLE001
            result.returncode = -1
            result.stderr_tail = f"{type(exc).__name__}: {exc}"
        result.duration_ms = int((time.monotonic() - started) * 1000)
        return self._record(result, emit)

    def script(self, step, name, *args, **kw):
        return self._run(
            step, [self.python, str(Path(self.scripts_dir) / name), *args], **kw
        )

    def module(self, step, name, *args, **kw):
        return self._run(step, [self.python, "-m", name, *args], **kw)

    def manage(self, step, args, emit=None, timeout=SCRIPT_TIMEOUT):
        if emit is not None:
            emit(
                "post_step",
                f"Running {STEP_PREFIX}{step} …",
                data={"step": STEP_PREFIX + step},
            )
        result = run_step(STEP_PREFIX + step, args, self.base_dir, timeout=timeout)
        return self._record(result, emit)

    def skip(self, step, reason, emit=None):
        return self._record(
            StepResult(step=STEP_PREFIX + step, skipped_reason=reason), emit
        )

    # -- environment --------------------------------------------------------

    def write_config(self) -> None:
        """zango_env.py's config, beside the run (it finds it through $ZAS_CONFIG)."""
        # The interpreter's own environment (never resolve the symlink: a venv's
        # bin/python points at the base Python, which lacks Django).
        venv = (
            sys.prefix
            if self.python == sys.executable
            else str(Path(self.python).parent.parent)
        )
        Path(self.run_dir).mkdir(parents=True, exist_ok=True)
        Path(self.config_path).write_text(
            json.dumps(
                {"setup_mode": "venv", "venv_path": venv, "project_dir": self.base_dir},
                indent=2,
            ),
            encoding="utf-8",
        )

    def has_playwright(self) -> bool:
        if self._playwright is None:
            try:
                proc = subprocess.run(  # noqa: S603
                    [self.python, "-c", "import playwright.sync_api"],
                    env=self.env(),
                    stdin=subprocess.DEVNULL,
                    capture_output=True,
                    timeout=60,
                    check=False,
                )
                self._playwright = proc.returncode == 0
            except Exception:  # noqa: BLE001
                self._playwright = False
        return self._playwright

    def app_url(self) -> str:
        from urllib.parse import urlparse

        parsed = urlparse(self.platform_url)
        host = (
            self.app_domain
            if ":" in self.app_domain or not parsed.port
            else (f"{self.app_domain}:{parsed.port}")
        )
        return f"{parsed.scheme or 'http'}://{host}"

    def app_reachable(self) -> tuple:
        """(reachable, reason): whether the app answers on its own domain from here."""
        if self._reachable is None:
            if not self.app_domain:
                self._reachable = (False, "the app has no domain configured")
            else:
                import urllib.error
                import urllib.request

                url = self.app_url() + "/"
                try:
                    urllib.request.urlopen(url, timeout=10)  # noqa: S310 - our own app
                    self._reachable = (True, "")
                except urllib.error.HTTPError:
                    self._reachable = (True, "")  # it answered
                except Exception as exc:  # noqa: BLE001
                    self._reachable = (
                        False,
                        f"the app's domain does not answer from the platform ({url}: "
                        f"{type(exc).__name__}). Point {self.app_domain} at this server "
                        "(DNS or hosts file), or set AGENT_MODE_PLATFORM_URL.",
                    )
        return self._reachable

    def environment_actions(self) -> list:
        """What only the user can fix before the rest of the build can run.

        Each is ``{id, kind, title, detail, command, blocks}``; ``blocks`` names
        the bring-up steps and checks that wait for it. Checked before those
        would be skipped: a skipped test proves nothing, a paused build can
        still be finished properly.
        """
        from urllib.parse import urlparse

        actions = []
        reachable, reason = self.app_reachable()
        if not reachable and self.app_domain:
            local = (urlparse(self.platform_url).hostname or "") in LOCAL_HOSTS
            actions.append(
                {
                    "id": "hosts_entry",
                    "kind": "hosts_entry",
                    "title": f"Point {self.app_domain} at this server",
                    "detail": (
                        f"The app does not answer on its own domain from the platform ({self.app_url()}/). "
                        "The app's menus (AppBuilder routes) and the API, UI, design and scenario "
                        "tests all sign in to the running app, so they wait for it. "
                        + (
                            "On this machine, add the domain to /etc/hosts."
                            if local
                            else "Add a DNS record for the domain that points at this server, "
                            "or set AGENT_MODE_PLATFORM_URL to where the platform answers."
                        )
                    ),
                    "command": (
                        f'echo "127.0.0.1 {self.app_domain.split(":")[0]}" | sudo tee -a /etc/hosts'
                        if local
                        else ""
                    ),
                    "blocks": [f"platform:{HELD_STEP}", *APP_LAYERS],
                    "reason": reason,
                }
            )
        if not self.has_playwright():
            actions.append(
                {
                    "id": "install_playwright",
                    "kind": "install_playwright",
                    "title": "Install Playwright in the platform environment",
                    "detail": (
                        "The UI tests (every role's menus, lists, forms and 360 pages) and the "
                        "design comparison run in a headless browser, which needs Playwright "
                        "and its Chromium in the platform's Python environment."
                    ),
                    "command": (
                        f"{self.python} -m pip install playwright && "
                        f"{self.python} -m playwright install chromium"
                    ),
                    "blocks": list(BROWSER_LAYERS),
                    "reason": PLAYWRIGHT_REASON,
                }
            )
        return actions

    # -- before the agent ------------------------------------------------

    def prepare(self, emit=None, template=None) -> None:
        """Phases 0-2 and the frontend prep of Phase 6. Raises StudioError.

        ``template``: the requirement's App Studio template; with it the approval bundle (what the
        user approved for each custom screen) is written to .zas/bundle/ for the agent.
        """
        if emit:
            emit(
                "sys",
                "App Studio build: the platform runs the skill's scripts; the agent writes the code.",
                level="sys",
            )
        self.write_config()
        self.check_spec = self._write_check_spec()
        if template is not None:
            # Before spec_check: it points each custom screen's hole at its bundle folder.
            self.write_bundle(template, emit)
        checked = self.script(
            "spec_check",
            "spec_check.py",
            self.check_spec,
            "--workspace",
            self.workspace,
            "--quiet",
            emit=emit,
        )
        if checked.returncode != 0:
            raise StudioError("SpecCheckFailed", self._spec_errors(checked))
        self.install_runtime(emit)
        self.prepare_frontend(emit)
        self.prepare_views(emit)

    def write_bundle(self, template, emit=None) -> dict | None:
        """.zas/bundle/ (approval_bundle.py): each custom screen's sketch, contract, kit trees and
        screenshots, from the approved spec in the same preview the user saw. Never fails the build:
        without it the agent builds from the hole text, as before."""
        import shutil
        import time

        from .approval_bundle import write_bundle
        from .preview_probe import probe_for

        out = self.zas_dir / "bundle"
        started = time.monotonic()
        probe = None
        try:
            shutil.rmtree(out, ignore_errors=True)
            self.zas_dir.mkdir(parents=True, exist_ok=True)
            probe = probe_for(template)
            manifest = write_bundle(
                Path(self.spec_path).read_text(encoding="utf-8"),
                out,
                probe=probe,
                template_version=getattr(template, "version", "") or "",
            )
        except Exception as exc:  # noqa: BLE001 - the bundle is an aid, not a gate
            logger.warning("agent_mode: approval bundle failed: %s", exc)
            self.steps.append(
                StepResult(
                    step=STEP_PREFIX + "bundle",
                    duration_ms=int((time.monotonic() - started) * 1000),
                    stderr_tail=str(exc)[-2000:],
                    skipped_reason=f"approval bundle failed: {exc}"[:300],
                )
            )
            return None
        finally:
            if probe is not None:
                probe.close()
        shots = sum(
            1 for s in manifest["screens"] for v in s["variants"] if v.get("shot")
        )
        self.steps.append(
            StepResult(
                step=STEP_PREFIX + "bundle",
                duration_ms=int((time.monotonic() - started) * 1000),
                stdout_tail=f"{len(manifest['screens'])} screens, {shots} screenshots; probe: {manifest['probe']}",
            )
        )
        if emit:
            emit(
                "sys",
                f"Approval bundle: {len(manifest['screens'])} custom screen(s), {shots} screenshot(s).",
                level="sys",
            )
        return manifest

    def _write_check_spec(self) -> str:
        """The approved spec as plain YAML the skill's PyYAML reads exactly as the platform did.

        The platform reads specs as YAML 1.2 (ruamel); the skill reads them with
        PyYAML, which refuses some flow-map text ruamel accepts. Re-emitting the
        parsed document keeps the meaning and removes the disagreement.
        """
        import yaml

        from zango.apps.shared.app_templates.services.spec import yamlio

        source = Path(self.spec_path)
        try:
            doc = yamlio.load(source.read_text(encoding="utf-8"))
        except Exception as exc:  # noqa: BLE001
            raise StudioError(
                "SpecCheckFailed", f"The approved spec could not be read: {exc}"
            )
        target = source.with_name(source.stem + ".build.yaml")
        target.write_text(
            yaml.safe_dump(doc, sort_keys=False, allow_unicode=True, width=10_000),
            encoding="utf-8",
        )
        return str(target)

    def _spec_errors(self, result: StepResult) -> str:
        if result.returncode == 2 or not (self.zas_dir / "issues.md").is_file():
            detail = (result.stderr_tail or result.stdout_tail or "").strip()
            return f"The build skill could not read the approved spec.\n{detail}"[:8000]
        lines = (self.zas_dir / "issues.md").read_text(encoding="utf-8").splitlines()
        errors = [line.strip() for line in lines if "**error**" in line]
        body = "\n".join(errors[:30]) or (result.stdout_tail or "").strip()
        more = (
            f"\n… and {len(errors) - 30} more (.zas/issues.md)"
            if len(errors) > 30
            else ""
        )
        return (
            f"The approved spec has {len(errors) or 'some'} error(s) the build cannot work "
            "around. Fix them in the spec (or ask the agent to) and commit again.\n"
            f"{body}{more}"
        )[:8000]

    def install_runtime(self, emit=None) -> None:
        src = Path(self.skill_dir) / "assets" / "backend" / "zas_core"
        dst = Path(self.workspace) / "backend" / "zas_core"
        started = time.monotonic()
        try:
            if dst.exists():
                shutil.rmtree(dst)
            shutil.copytree(
                src, dst, ignore=shutil.ignore_patterns("__pycache__", "*.pyc")
            )
            shutil.copyfile(self.zas_dir / "spec.resolved.json", dst / "spec.json")
            registered = register_module(self.workspace, "zas_core", "backend.zas_core")
        except Exception as exc:  # noqa: BLE001
            raise StudioError(
                "RuntimeInstallFailed", f"Could not copy the zas_core runtime: {exc}"
            )
        self._record(
            StepResult(
                step=STEP_PREFIX + "runtime",
                command=["copy", str(src), str(dst)],
                duration_ms=int((time.monotonic() - started) * 1000),
                stdout_tail=(
                    "zas_core copied; spec.json is the resolved spec; "
                    + (
                        "registered in settings.json"
                        if registered
                        else "already registered"
                    )
                ),
            ),
            emit,
        )
        selftest = self.script(
            "selftest", "selftest_runtime.py", "--workspace", self.workspace, emit=emit
        )
        if selftest.returncode != 0:
            raise StudioError(
                "RuntimeSelfTestFailed",
                "The zas_core runtime failed its self-test:\n"
                + (selftest.stdout_tail + "\n" + selftest.stderr_tail).strip()[-3000:],
            )

    def prepare_frontend(self, emit=None) -> None:
        if not self.frontend_allowed:
            self.frontend_reason = (
                "Node tooling is not enabled for this app (AGENT_MODE_ALLOW_FRONTEND_BUILD, "
                "and node must be installed)"
            )
            self.skip("frontend", self.frontend_reason, emit)
            return
        ws = Path(self.workspace)
        fe = ws / "frontend"
        skill = Path(self.skill_dir)

        def failed(result) -> bool:
            """A failed frontend step stops the build: an app without its frontend is not built."""
            if result.returncode == 0:
                return False
            self.frontend_reason = f"{result.step} failed (exit {result.returncode})"
            raise StudioError("FrontendPrepFailed", _frontend_failure(result))

        if not (fe / "package.json").is_file():
            # The scaffold installs its own pinned packages, whose peer ranges
            # conflict (crud 1.0.13-rc.11 wants components 0.2.0-rc.3, appbuilder
            # wants ^0.2.1). The skill re-pins crud with --legacy-peer-deps right
            # after, so let the scaffold's install resolve the same way.
            scaffold = self._run(
                "frontend:scaffold",
                ["npx", "--yes", "@zango-core/create-zango-app", "frontend"],
                cwd=str(ws),
                timeout=NPM_TIMEOUT,
                extra_env={"npm_config_legacy_peer_deps": "true"},
                emit=emit,
            )
            if scaffold.returncode != 0:
                if not (fe / "package.json").is_file():
                    failed(scaffold)
                if emit:
                    emit(
                        "sys",
                        "The scaffold copied its files but its own npm install failed; "
                        "the pinned install below installs every dependency.",
                        level="warn",
                    )
        self._write_proxy_routes(fe)
        if failed(
            self._run(
                "frontend:pin",
                [
                    "npm",
                    "install",
                    "--save-exact",
                    "--legacy-peer-deps",
                    f"@zango-core/crud@{CRUD_VERSION}",
                    f"lucide-react@{LUCIDE_VERSION}",
                ],
                cwd=str(fe),
                timeout=NPM_TIMEOUT,
                emit=emit,
            )
        ):
            return  # (failed() raises)
        (fe / "patches").mkdir(exist_ok=True)
        for patch in (skill / "assets" / "frontend" / "patches").glob("*.patch"):
            shutil.copyfile(patch, fe / "patches" / patch.name)
        if failed(
            self._run(
                "frontend:patch-package",
                ["npm", "install", "--save-dev", "--legacy-peer-deps", "patch-package"],
                cwd=str(fe),
                timeout=NPM_TIMEOUT,
                emit=emit,
            )
        ):
            return  # (failed() raises)
        _set_postinstall(fe / "package.json")
        if failed(
            self._run(
                "frontend:patch",
                ["npx", "--no", "patch-package"],
                cwd=str(fe),
                timeout=NPM_TIMEOUT,
                emit=emit,
            )
        ):
            return  # (failed() raises)
        if (fe / "src" / "zas").exists():
            shutil.rmtree(fe / "src" / "zas")
        shutil.copytree(
            skill / "assets" / "frontend" / "zas",
            fe / "src" / "zas",
            ignore=shutil.ignore_patterns("__pycache__"),
        )
        (fe / "src" / "custom").mkdir(parents=True, exist_ok=True)
        shutil.copyfile(
            self.zas_dir / "spec.ui.json", fe / "src" / "custom" / "spec.ui.json"
        )
        shutil.copyfile(
            skill / "assets" / "templates" / "frontend" / "index.css",
            fe / "src" / "index.css",
        )
        if failed(
            self.script(
                "frontend:icons",
                "lucide_icons.py",
                "--workspace",
                self.workspace,
                emit=emit,
            )
        ):
            return  # (failed() raises)
        self.frontend_ready = True

    # -- declared list views ------------------------------------------------

    def custom_views(self) -> list:
        """Declared list views this runtime has no component for: the agent writes those.

        A crud page may declare ``views`` (kanban, cards, calendar, timeline) and
        the user approved them in the preview. A view counts as built by the
        skill when its checker carried it into ``spec.ui.json``; every other
        declared view, table aside, is written as a custom view for this app.
        """
        try:
            resolved = json.loads(
                (self.zas_dir / "spec.resolved.json").read_text(encoding="utf-8")
            )
        except (OSError, ValueError):
            return []
        try:
            ui_pages = (
                json.loads(
                    (self.zas_dir / "spec.ui.json").read_text(encoding="utf-8")
                ).get("pages")
                or {}
            )
        except (OSError, ValueError):
            ui_pages = {}
        pages = resolved.get("pages") or {}
        if isinstance(pages, list):
            pages = {p.get("code"): p for p in pages if isinstance(p, dict)}
        out = []
        for code, page in pages.items():
            if not isinstance(page, dict) or page.get("type") != "crud":
                continue
            native = {
                v.get("type")
                for v in (ui_pages.get(code) or {}).get("views") or []
                if isinstance(v, dict)
            }
            for view in page.get("views") or []:
                kind = view.get("type") if isinstance(view, dict) else None
                if kind and kind != "table" and kind not in native:
                    out.append(
                        {
                            "page": code,
                            "entity": page.get("entity"),
                            "type": kind,
                            "view": view,
                        }
                    )
        return out

    def _views_manifest(self) -> dict:
        """{page: [declared views, in order]} for ViewsPage.tsx, with what a view needs resolved."""
        resolved = json.loads(
            (self.zas_dir / "spec.resolved.json").read_text(encoding="utf-8")
        )
        entities = resolved.get("entities") or {}
        custom = {(v["page"], v["type"]) for v in self.custom_views()}
        pages = resolved.get("pages") or {}
        manifest = {}
        for code in sorted({page for page, _ in custom}):
            page = pages.get(code) or {}
            workflow = (entities.get(page.get("entity")) or {}).get("workflow") or {}
            rows = []
            for view in page.get("views") or []:
                kind = view.get("type")
                row = dict(view)
                row["label"] = (
                    view.get("label") or VIEW_LABELS.get(kind, (kind or "").title())[0]
                )
                row["icon"] = VIEW_LABELS.get(kind, ("", "layout-grid"))[1]
                row["custom"] = (code, kind) in custom
                if kind == "kanban" and view.get("group_by") == "status":
                    row.setdefault("move", "transitions")
                    row["transitions"] = [
                        {
                            "name": t.get("name"),
                            "label": t.get("label") or t.get("name"),
                            "from": t.get("from") or [],
                            "to": t.get("to"),
                            "engine": t.get("engine") or [],
                            "has_form": bool(t.get("form")),
                            "roles": t.get("roles") or [],
                        }
                        for t in workflow.get("transitions") or []
                        if not t.get("system")
                    ]
                rows.append(row)
            manifest[code] = rows
        return manifest

    def prepare_views(self, emit=None) -> None:
        """Hand the agent the declared views it has to write, and the page that hosts them."""
        todo = self.zas_dir / "views.md"
        needed = self.custom_views()
        if not needed or not self.frontend_ready:
            todo.unlink(missing_ok=True)
            return
        target = Path(self.workspace) / "frontend" / "src" / "custom" / "views"
        target.mkdir(parents=True, exist_ok=True)
        helper = (
            Path(self.skill_dir)
            / "assets"
            / "templates"
            / "frontend"
            / "views"
            / "ViewsPage.tsx"
        )
        if not helper.is_file():
            raise StudioError(
                "ViewsHelperMissing",
                "The spec declares list views this build skill has no component for, and the "
                "skill does not ship the page that hosts custom views (assets/templates/"
                "frontend/views/ViewsPage.tsx).",
            )
        shutil.copyfile(helper, target / "ViewsPage.tsx")
        (target / "views.json").write_text(
            json.dumps(self._views_manifest(), indent=2) + "\n", encoding="utf-8"
        )
        lines = [
            "# Declared list views to write as custom views",
            "",
            "The approved spec declares these views and this runtime has no component for them.",
            "Write each one as `references/views.md` says. The platform checks every row.",
            "",
            "| Page | View | File to write | Spec |",
            "|---|---|---|---|",
        ]
        for v in needed:
            lines.append(
                f"| `{v['page']}` | `{v['type']}` | `frontend/src/custom/views/{v['page']}_{v['type']}.tsx` "
                f"| `pages.{v['page']}.views` — `{json.dumps(v['view'], separators=(',', ':'))}` |"
            )
        todo.write_text("\n".join(lines) + "\n", encoding="utf-8")
        if emit:
            emit(
                "sys",
                "Declared views the agent writes as custom views: "
                + ", ".join(f"{v['page']} ({v['type']})" for v in needed),
                level="sys",
            )

    def check_views(self, emit=None) -> LayerResult:
        """Every declared view the runtime does not ship was written, and its page uses it."""
        src = Path(self.workspace) / "frontend" / "src" / "custom"
        try:
            index = (src / "pages" / "index.ts").read_text(
                encoding="utf-8", errors="replace"
            )
        except OSError:
            index = ""
        index_code = re.sub(r"//[^\n]*|/\*.*?\*/", "", index, flags=re.S)
        needed = self.custom_views()
        problems = []
        for v in needed:
            page, kind = v["page"], v["type"]
            rel = f"frontend/src/custom/views/{page}_{kind}.tsx"
            where = f"pages.{page}.views"

            def problem(pid, title, detail="", _page=page, _kind=kind, _where=where):
                problems.append(
                    {
                        "id": f"views.{_page}.{_kind}.{pid}",
                        "title": title,
                        "spec_path": _where,
                        "detail": detail,
                    }
                )

            path = src / "views" / f"{page}_{kind}.tsx"
            if not path.is_file():
                problem(
                    "file",
                    f"the {kind} view of the {page} page is not built ({rel} is missing)",
                    "The spec declares it and the user approved it in the preview. Write it as "
                    "references/views.md says.",
                )
                continue
            code = re.sub(
                r"//[^\n]*|/\*.*?\*/",
                "",
                path.read_text(encoding="utf-8", errors="replace"),
                flags=re.S,
            )
            if not re.search(r"export\s+default\b", code):
                problem("export", f"{rel} has no default export")
            if not re.search(r"useTableRows|api\.get\(|\bget\(", code):
                problem(
                    "data",
                    f"{rel} never loads the entity's records",
                    "Use api.useTableRows(props.endpoint, …).",
                )
            if len(code.strip()) < VIEW_MIN_CHARS or re.search(
                r">[^<{]*(not built|coming soon|TODO|placeholder)", code, re.I
            ):
                problem("stub", f"{rel} is a placeholder, not the {kind} view")
            wired = re.search(
                rf"makeViewsPage\(\s*[\"']{re.escape(page)}[\"']\s*,\s*\{{([^}}]*)\}}",
                index_code,
            )
            if wired is None:
                problem(
                    "page",
                    f"src/custom/pages/index.ts does not export the {page} page with makeViewsPage",
                    f'export const Page_{page} = makeViewsPage("{page}", {{ {kind}: <the view> }});',
                )
            elif not re.search(rf"\b{re.escape(kind)}\b", wired.group(1)):
                problem(
                    "wired", f'makeViewsPage("{page}", …) does not pass the {kind} view'
                )
        if emit:
            emit(
                "post_step",
                "studio:test:views "
                + (
                    f"passed: {len(needed)} declared view(s) built"
                    if not problems
                    else f"failed: {len(problems)} problem(s) — "
                    + "; ".join(p["title"] for p in problems[:4])
                ),
                level="err" if problems else "info",
                is_error=bool(problems),
            )
        bad = {p["id"].rsplit(".", 1)[0] for p in problems}
        return LayerResult(
            name="views",
            status="fail" if problems else "pass",
            counts={"pass": len(needed) - len(bad), "fail": len(problems), "skip": 0},
            failures=problems,
        )

    def _write_proxy_routes(self, fe: Path) -> None:
        """frontend/.env VITE_PROXY_ROUTES: the package routes plus every module prefix, never /app."""
        try:
            resolved = json.loads(
                (self.zas_dir / "spec.resolved.json").read_text(encoding="utf-8")
            )
        except (OSError, ValueError):
            resolved = {}
        routes = list(BASE_PROXY_ROUTES)
        for module in resolved.get("modules") or []:
            url = "/" + str(module.get("url") or module.get("code") or "").strip("/")
            if url not in ("/", "/app") and url not in routes:
                routes.append(url)
        line = "VITE_PROXY_ROUTES=" + ",".join(routes) + ","
        env_path = fe / ".env"
        lines = (
            env_path.read_text(encoding="utf-8").splitlines()
            if env_path.is_file()
            else []
        )
        lines = [x for x in lines if not x.startswith("VITE_PROXY_ROUTES=")] + [line]
        env_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    # -- after the agent -------------------------------------------------

    def bring_up(self, creds: dict, emit=None, hold=(), only=None) -> bool:
        """Phase 5 and Phase 6 step 7, in the skill's order. Stops at the first failure.

        ``hold`` names steps left for later (the user has something to do
        first); ``only`` runs just the named steps (a continuation).
        """
        app = self.app_name
        failed_at = None

        def platform(cmd):
            return self.script(
                f"platform:{cmd}",
                "zango_platform.py",
                cmd,
                "--workspace",
                self.workspace,
                "--platform",
                self.platform_url,
                extra_env=creds,
                emit=emit,
            )

        steps = [
            ("platform:roles", lambda: platform("roles")),
            (
                "ws_makemigration",
                lambda: self.manage(
                    "ws_makemigration", ["ws_makemigration", app, "--noinput"], emit
                ),
            ),
            ("prune_first_migration", self._prune),
            (
                "ws_migrate",
                lambda: self.manage(
                    "ws_migrate", ["ws_migrate", app, "--noinput"], emit
                ),
            ),
            ("platform:sync", lambda: platform("sync")),
            ("platform:schedule", lambda: platform("schedule")),
            ("platform:users", lambda: platform("users")),
            ("platform:check", lambda: platform("check")),
            (
                "sync_static",
                lambda: self.manage("sync_static", ["sync_static", app], emit),
            ),
            (
                "collectstatic",
                lambda: self.manage(
                    "collectstatic", ["collectstatic", "--noinput"], emit
                ),
            ),
            ("platform:appbuilder", self._appbuilder(platform, emit)),
        ]
        for name, run in steps:
            if only is not None and name not in only:
                continue
            if name in hold:
                self.skip(
                    name,
                    "held until you complete the action this build is waiting for",
                    emit,
                )
                continue
            if failed_at:
                self.skip(name, f"{failed_at} failed earlier in this bring-up", emit)
                continue
            if name == "prune_first_migration":
                result = run(emit)
            else:
                result = run()
            if result is not None and not result.ok:
                failed_at = name
        return failed_at is None

    def _prune(self, emit=None):
        initial = Path(self.workspace) / "migrations" / "0001_initial.py"
        if not self.first_build or self._pruned or not initial.is_file():
            return self.skip(
                "prune_first_migration",
                "not the app's first build"
                if not self.first_build
                else "nothing to prune",
                emit,
            )
        self._pruned = True
        return self.script(
            "prune_first_migration", "prune_first_migration.py", str(initial), emit=emit
        )

    def _appbuilder(self, platform, emit):
        def run():
            if not (self.zas_dir / "menu_icons.json").is_file():
                return self.skip(
                    "platform:appbuilder",
                    "no menu icons (.zas/menu_icons.json): the frontend phase was skipped — "
                    + (self.frontend_reason or "no frontend"),
                    emit,
                )
            reachable, reason = self.app_reachable()
            if not reachable:
                return self.skip("platform:appbuilder", reason, emit)
            return platform("appbuilder")

        return run

    def verify(
        self, emit=None, only: dict | None = None, bring_up_ok: bool = True, hold=()
    ) -> dict:
        """Run the hole audit and the test layers; ``only`` = {layer: [groups]} re-runs just those.

        Layers in ``hold`` are left out altogether: they wait for the user.
        """
        layers = {}
        playwright = self.has_playwright()
        reachable, unreachable = self.app_reachable()
        users_ok = (self.zas_dir / "test_users.json").is_file()
        for name, runner, browser, needs_app in LAYERS:
            if only is not None and name not in only:
                continue
            if name in hold:
                continue
            groups = (only or {}).get(name) or []
            reason = ""
            if browser and not playwright:
                reason = PLAYWRIGHT_REASON
            elif needs_app and not bring_up_ok:
                reason = "the bring-up did not complete"
            elif needs_app and not reachable:
                reason = unreachable
            elif needs_app and not users_ok:
                reason = "no test users (.zas/test_users.json)"
            elif (
                name == "ui"
                and not self.frontend_ready
                and not (Path(self.workspace) / "frontend").is_dir()
            ):
                reason = "no frontend was built"
            elif name == "app_shell" and not self.frontend_ready:
                reason = "the frontend phase was skipped — " + (
                    self.frontend_reason or "no frontend"
                )
            elif name == "views" and not self.custom_views():
                continue  # nothing declared beyond what the runtime ships: not a check at all
            elif name == "views" and not self.frontend_ready:
                reason = "the frontend phase was skipped — " + (
                    self.frontend_reason or "no frontend"
                )
            if reason:
                self.skip(f"test:{name}", reason, emit)
                layers[name] = LayerResult(name=name, status="skip", reason=reason)
                continue
            layers[name] = self._run_layer(name, runner, groups, emit)
        return layers

    def _run_layer(self, name, runner, groups, emit) -> LayerResult:
        if runner == "app_shell":
            return self.check_app_shell(emit)
        if runner == "views":
            return self.check_views(emit)
        if runner == "audit":
            result = self.script(
                "test:audit_holes",
                "spec_check.py",
                self.check_spec or self.spec_path,
                "--workspace",
                self.workspace,
                "--audit-holes",
                emit=emit,
            )
            if result.returncode == 0:
                return LayerResult(name=name, counts={"pass": 1, "fail": 0, "skip": 0})
            return LayerResult(
                name=name,
                status="fail",
                counts={"pass": 0, "fail": 1, "skip": 0},
                failures=[
                    {
                        "id": "audit_holes",
                        "title": "every hole implemented with its marker and status",
                        "detail": (result.stdout_tail or result.stderr_tail).strip()[
                            -1500:
                        ],
                    }
                ],
            )
        args = ["--workspace", self.workspace]
        if name == "design_lint":
            args += ["--only", "lint"]
        elif name == "design":
            args += ["--only", ",".join(groups or DESIGN_BROWSER_GROUPS)]
        elif groups:
            args += ["--only", ",".join(groups)]
        result = self.module(
            f"test:{name}", runner, *args, timeout=TEST_TIMEOUT, emit=emit
        )
        layer_key = "design" if name in ("design", "design_lint") else name
        records = [
            r for r in _load_results(self.workspace) if r.get("layer") == layer_key
        ]
        if name == "design_lint":
            records = [
                r for r in records if str(r.get("id", "")).startswith("design.lint")
            ]
        elif name == "design":
            records = [
                r for r in records if not str(r.get("id", "")).startswith("design.lint")
            ]
        counts = {"pass": 0, "fail": 0, "skip": 0}
        for r in records:
            counts[r.get("status", "fail")] = counts.get(r.get("status", "fail"), 0) + 1
        failures = [
            {k: r.get(k) for k in ("id", "title", "role", "spec_path", "detail")}
            for r in records
            if r.get("status") == "fail"
        ]
        if result.returncode == 2 and name in ("ui", "design"):
            # browser.require() exits 2 when Playwright is missing.
            return LayerResult(name=name, status="skip", reason=PLAYWRIGHT_REASON)
        if result.returncode not in (0, 1) and not failures:
            failures = [
                {
                    "id": f"{name}.crashed",
                    "title": f"the {name} layer did not run",
                    "detail": (result.stderr_tail or result.stdout_tail).strip()[
                        -1500:
                    ],
                }
            ]
        status = "fail" if failures else "pass"
        return LayerResult(
            name=name,
            status=status,
            counts=counts,
            failures=failures,
            groups=sorted(
                {g for g in (_group_of(name, f["id"]) for f in failures) if g}
            ),
        )

    def check_app_shell(self, emit=None) -> LayerResult:
        """What serving /app needs: the app module, its route, and a fresh build it loads.

        Phase 6 step 6 of the skill; the agent writes it, the platform checks it,
        because without it the built frontend is never served.
        """
        ws = Path(self.workspace)
        problems = []

        def problem(pid, title, detail=""):
            problems.append(
                {"id": f"app_shell.{pid}", "title": title, "detail": detail}
            )

        try:
            settings = json.loads((ws / "settings.json").read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            settings = {}
            problem("settings", "settings.json could not be read", str(exc))
        routes = settings.get("app_routes") or []
        if not any(
            r.get("module") == "app" and r.get("re_path") == "^" for r in routes
        ):
            problem(
                "route",
                'settings.json app_routes has no {"module": "app", "re_path": "^", "url": "urls"}',
                f"app_routes is {json.dumps(routes)[:300]}",
            )
        module = next(
            (m for m in settings.get("modules") or [] if m.get("name") == "app"), None
        )
        app_dir = ws / (
            module.get("path", "backend.app") if module else "backend.app"
        ).replace(".", "/")
        if module is None:
            problem("module", 'settings.json modules has no "app" module', "")
        for rel in ("urls.py", "views.py", "templates/app.html"):
            if not (app_dir / rel).is_file():
                problem(
                    f"file:{rel}",
                    f"the app module is missing {app_dir.relative_to(ws)}/{rel}",
                )

        html_path = app_dir / "templates" / "app.html"
        build = None
        if html_path.is_file():
            html = html_path.read_text(encoding="utf-8", errors="replace")
            match = re.search(r"zango-app\.[\w.-]+?\.min\.js", html)
            if "{{BUILD_FILE}}" in html or match is None:
                problem(
                    "build_ref",
                    "app.html does not name the frontend build (zango-app.<ts>.min.js)",
                )
            else:
                build = ws / "static" / "js" / match.group(0)
                if not build.is_file():
                    problem(
                        "build_file",
                        f"app.html loads {match.group(0)}, which is not in static/js",
                        "Run `npm run build:zango` in frontend/ and deploy it with "
                        "`cp -r frontend/zango-build/. static/js/`, then point app.html at that file.",
                    )
        if build is not None and build.is_file():
            src = ws / "frontend" / "src"
            newest = (
                max(
                    (p.stat().st_mtime for p in src.rglob("*") if p.is_file()),
                    default=0,
                )
                if src.is_dir()
                else 0
            )
            if newest > build.stat().st_mtime + 1:
                problem(
                    "stale",
                    f"static/js/{build.name} is older than the frontend sources",
                    "Rebuild (`npm run build:zango`), deploy the new file and update app.html.",
                )

        if emit:
            emit(
                "post_step",
                "studio:test:app_shell "
                + (
                    "passed: /app is served by the app module"
                    if not problems
                    else f"failed: {len(problems)} problem(s) — "
                    + "; ".join(p["title"] for p in problems[:4])
                ),
                level="err" if problems else "info",
                is_error=bool(problems),
            )
        return LayerResult(
            name="app_shell",
            status="fail" if problems else "pass",
            counts={"pass": 0 if problems else 1, "fail": len(problems), "skip": 0},
            failures=problems,
        )

    def report(self, emit=None) -> dict:
        result = self.module(
            "report", "zas_test.report", "--workspace", self.workspace, emit=emit
        )
        md, html = self.zas_dir / "build_report.md", self.zas_dir / "build_report.html"
        summary = (
            md.read_text(encoding="utf-8")[:REPORT_SUMMARY_CHARS]
            if md.is_file()
            else ""
        )
        verdict = re.search(r"\*\*Verdict:\s*([^*]+)\*\*", summary)
        return {
            "verdict": verdict.group(1).strip() if verdict else "",
            "summary_md": summary,
            "md_path": str(md) if md.is_file() else "",
            "html_path": str(html) if html.is_file() else "",
            "ok": result.returncode == 0,
        }

    def digest(self, bring_up_ok: bool, layers: dict) -> str:
        """What a fix round tells the agent: the failing step or checks, briefly."""
        lines = [
            "## Fix round: the platform's checks found problems",
            "",
            "Fix every item below where its cause is (generated code, hook, slot, fixture). "
            "Never edit a test, backend/zas_core/, packages/ or the spec. Stop when done; "
            "the platform re-runs the failing checks.",
            "",
        ]
        if not bring_up_ok:
            failed = next((s for s in reversed(self.steps) if s.ran and not s.ok), None)
            if failed is not None:
                lines += [
                    f"### Bring-up step `{failed.step}` failed (exit {failed.returncode})",
                    "```",
                    (failed.stderr_tail or failed.stdout_tail or "").strip()[-2500:],
                    "```",
                    "",
                ]
        for name, layer in layers.items():
            if layer.status != "fail":
                continue
            lines.append(f"### {name}: {len(layer.failures)} failing")
            for f in layer.failures[:DIGEST_MAX_ITEMS]:
                who = f" [{f['role']}]" if f.get("role") else ""
                where = f" ({f['spec_path']})" if f.get("spec_path") else ""
                lines.append(
                    f"- `{f.get('id')}`{who} {f.get('title', '')}{where}: {str(f.get('detail', ''))[:400]}"
                )
            lines.append("")
        return "\n".join(lines).strip() + "\n"

    def finish(
        self,
        creds: dict,
        resume_agent=None,
        rounds: int = 2,
        emit=None,
        checkpoint=None,
        skip=False,
    ) -> StudioOutcome:
        """Bring-up, checks, fix rounds, report — pausing for the user when it has to.

        ``resume_agent(digest) -> bool`` resumes the agent's session with the
        digest; False (budget, error, abort) ends the fix rounds.

        If something only the user can fix stands in the way (see
        :meth:`environment_actions`), everything that does not depend on it
        runs first and the outcome comes back *waiting*, with a checkpoint.
        ``checkpoint`` continues such a build: only what was held runs.
        ``skip`` continues without it: those checks are recorded as skipped by
        the user, never as passed.
        """
        cp = checkpoint or {}
        layers = {
            n: LayerResult.from_checkpoint(d)
            for n, d in (cp.get("layers") or {}).items()
        }
        done = int(cp.get("rounds") or 0)
        actions = [] if skip else self.environment_actions()
        held_steps = {
            b.split(":", 1)[1]
            for a in actions
            for b in a["blocks"]
            if b.startswith("platform:")
        }
        held_layers = {
            b for a in actions for b in a["blocks"] if not b.startswith("platform:")
        }

        if checkpoint is None:
            bring_up_ok = self.bring_up(
                creds, emit, hold={f"platform:{x}" for x in held_steps}
            )
            layers = self.verify(emit, bring_up_ok=bring_up_ok, hold=held_layers)
        else:
            bring_up_ok = True
            was_steps = {f"platform:{x}" for x in cp.get("held_steps") or []}
            was_layers = list(cp.get("held_layers") or [])
            if skip:
                why = {
                    b: f"skipped by the user: {a.get('title', a.get('kind', ''))}"
                    for a in cp.get("actions") or []
                    for b in a.get("blocks") or []
                }
                for step in sorted(was_steps):
                    self.skip(step, why.get(step, "skipped by the user"), emit)
                for name in was_layers:
                    reason = why.get(name, "skipped by the user")
                    self.skip(f"test:{name}", reason, emit)
                    layers[name] = LayerResult(name=name, status="skip", reason=reason)
            else:
                run_steps = was_steps - {f"platform:{x}" for x in held_steps}
                if run_steps:
                    bring_up_ok = self.bring_up(creds, emit, only=run_steps)
                todo = {n: [] for n in was_layers if n not in held_layers}
                if todo:
                    layers.update(self.verify(emit, only=todo, bring_up_ok=bring_up_ok))

        hold_steps = {f"platform:{x}" for x in held_steps}
        while (
            done < rounds
            and resume_agent is not None
            and (not bring_up_ok or any(x.status == "fail" for x in layers.values()))
        ):
            done += 1
            if emit:
                emit(
                    "sys",
                    f"Fix round {done} of {rounds}: sending the failures back to the agent.",
                    level="sys",
                )
            if not resume_agent(self.digest(bring_up_ok, layers)):
                if emit:
                    emit(
                        "sys",
                        "The agent could not continue; no more fix rounds.",
                        level="warn",
                    )
                break
            was_ok = bring_up_ok
            bring_up_ok = self.bring_up(creds, emit, hold=hold_steps)
            if not was_ok:
                ran = {n: [] for n in layers} if checkpoint is not None else None
                fresh = self.verify(
                    emit, only=ran, bring_up_ok=bring_up_ok, hold=held_layers
                )
            else:
                only = {n: x.groups for n, x in layers.items() if x.status == "fail"}
                fresh = self.verify(
                    emit, only=only, bring_up_ok=bring_up_ok, hold=held_layers
                )
            layers.update(fresh)

        if actions and bring_up_ok:
            # Everything that could run has; the rest waits for the user.
            return StudioOutcome(
                ok=False,
                bring_up_ok=True,
                layers=layers,
                rounds=done,
                report={},
                pending_actions=[
                    {k: v for k, v in a.items() if k != "reason"} for a in actions
                ],
                checkpoint={
                    "build": self.build_state(),
                    "layers": {n: x.to_checkpoint() for n, x in layers.items()},
                    "rounds": done,
                    "held_steps": sorted(held_steps),
                    "held_layers": [n for n, *_ in LAYERS if n in held_layers],
                    "actions": [
                        {k: v for k, v in a.items() if k != "reason"} for a in actions
                    ],
                },
            )
        if actions:
            # The bring-up itself failed: waiting for the user would not help.
            layers.update(
                self.verify(emit, only={n: [] for n in held_layers}, bring_up_ok=False)
            )
        elif resume_agent is not None and bring_up_ok:
            # One look: the agent sees each custom screen it built next to the one the user approved.
            look = self.look_digest()
            if look:
                if emit:
                    emit(
                        "sys",
                        "One look: the agent compares each custom screen with the approved preview.",
                        level="sys",
                    )
                if resume_agent(look):
                    bring_up_ok = self.bring_up(creds, emit, hold=hold_steps)
                    design = layers.get("design")
                    groups = sorted(set(design.groups if design else []) | {"parity"})
                    layers.update(
                        self.verify(
                            emit,
                            only={"design": groups},
                            bring_up_ok=bring_up_ok,
                            hold=held_layers,
                        )
                    )
        report = self.report(emit)
        ok = bring_up_ok and not blocking(layers)
        return StudioOutcome(
            ok=ok, bring_up_ok=bring_up_ok, layers=layers, rounds=done, report=report
        )

    def look_digest(self) -> str:
        """The one-look message: each custom screen as built next to the approved one, or "".

        zas_test.design parity writes the pairs (.zas/parity_looks.json). Only screens with an
        approved screenshot are listed; the agent opens them with Read.
        """
        try:
            looks = json.loads(
                (self.zas_dir / "parity_looks.json").read_text(encoding="utf-8")
            )
        except (OSError, ValueError):
            return ""
        pairs = [x for x in looks if x.get("approved") and x.get("built")]
        if not pairs:
            return ""
        lines = [
            "## One look: your custom screens next to what the user approved",
            "",
            "Open each pair with Read: the approved screenshot (from the preview), then the screen "
            "you built. The numbers differ (the preview used demo data); compare the layout: the "
            "blocks and their order, titles and labels, emphasis, density and empty states. Fix a "
            "slot that does not match the approved one; when they all match, say so and stop.",
            "",
        ]
        for x in pairs:
            note = (
                " (hand-written in the preview: match it by eye)"
                if x.get("hand_written")
                else ""
            )
            lines.append(
                f"- `{x['screen']}` as {x['role']}{note}: approved `{x['approved']}`, built `{x['built']}`"
            )
        return "\n".join(lines) + "\n"

    def still_failing(self, pending: list) -> list:
        """The pending actions that are still not done, each with ``still_failing_reason``."""
        now = {a["kind"]: a for a in self.environment_actions()}
        out = []
        for action in pending or []:
            current = now.get(action.get("kind"))
            if current is not None:
                out.append(
                    {**action, "still_failing_reason": current.get("reason", "")}
                )
        return out

    def test_users(self) -> list:
        """The run's test users from .zas/test_users.json, in the run's own format."""
        try:
            data = json.loads(
                (self.zas_dir / "test_users.json").read_text(encoding="utf-8")
            )
        except (OSError, ValueError):
            return []
        out = []
        for user in data.get("users") or []:
            if not user.get("email"):
                continue
            roles = user.get("roles") or []
            entry = {
                "email": user["email"],
                "role": roles[0] if roles else "",
                "status": "created",
            }
            if user.get("password"):
                entry["password"] = user["password"]
            out.append(entry)
        return out


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _frontend_failure(result) -> str:
    """Why the frontend could not be prepared, with npm's own explanation when there is one."""
    tail = (result.stderr_tail or result.stdout_tail or "").strip()[-2000:]
    message = (
        f"The frontend could not be prepared: {result.step} failed (exit {result.returncode}). "
        "The build was stopped before the agent ran, because an app without its frontend "
        "has nothing to serve at /app."
    )
    report = re.search(r"\S+eresolve-report\.txt", tail)
    if "ERESOLVE" in tail or report:
        message += " npm could not resolve the packages' peer dependencies"
        message += f" (details: {report.group(0)})." if report else "."
    return message + ("\n\n" + tail if tail else "")


def register_module(workspace: str, name: str, path: str) -> bool:
    """Add a module to settings.json once; returns whether it was added."""
    settings_path = Path(workspace) / "settings.json"
    data = json.loads(settings_path.read_text(encoding="utf-8"))
    modules = data.setdefault("modules", [])
    if any(m.get("name") == name or m.get("path") == path for m in modules):
        return False
    modules.append({"name": name, "path": path})
    settings_path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    return True


def _set_postinstall(package_json: Path) -> None:
    data = json.loads(package_json.read_text(encoding="utf-8"))
    scripts = data.setdefault("scripts", {})
    if scripts.get("postinstall") != "patch-package":
        scripts["postinstall"] = "patch-package"
        package_json.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def _load_results(workspace: str) -> list:
    try:
        data = json.loads(
            (Path(workspace) / ".zas" / "test_results.json").read_text(encoding="utf-8")
        )
    except (OSError, ValueError):
        return []
    return data.get("results") or []


def _group_of(layer: str, result_id: str) -> str:
    """The --only group a failing check belongs to."""
    parts = str(result_id or "").split(".")
    if layer == "api":
        return API_GROUP.get(parts[0], "")
    if layer in ("ui", "design") and len(parts) > 1:
        return parts[1]
    if layer == "scenarios" and len(parts) > 1 and re.match(r"^H-\d+", parts[1]):
        return parts[1]
    return ""
