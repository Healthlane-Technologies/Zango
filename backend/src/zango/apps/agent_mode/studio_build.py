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
BASE_PROXY_ROUTES = ["/api", "/zango", "/appbuilder", "/crud", "/workflow"]

# Test layers in the order the skill runs them. ``browser`` layers need
# Playwright; ``app`` layers sign in to the running app as the test users.
LAYERS = (
    # name, runner, needs browser, needs the app
    ("audit_holes", "audit", False, False),
    ("design_lint", "zas_test.design", False, False),
    ("api", "zas_test.api", False, True),
    ("ui", "zas_test.ui", True, True),
    ("design", "zas_test.design", True, True),
    ("scenarios", "zas_test.scenarios", False, True),
)
DESIGN_BROWSER_GROUPS = ("gallery", "tokens", "tree", "layout")
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
                        type(user.user).objects.filter(pk=user.user_id).update(is_active=False)
            except Exception:  # noqa: BLE001 - never mask the build's own outcome
                logger.exception("agent_mode: could not disable the build service account")


# ---------------------------------------------------------------------------
# The build
# ---------------------------------------------------------------------------


@dataclass
class LayerResult:
    name: str
    status: str = "pass"  # pass | fail | skip
    counts: dict = field(default_factory=dict)
    failures: list = field(default_factory=list)  # [{id, title, role, spec_path, detail}]
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


@dataclass
class StudioOutcome:
    ok: bool
    bring_up_ok: bool
    layers: dict
    rounds: int
    report: dict

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
            emit("post_step", f"{result.step} skipped: {result.skipped_reason}",
                 level="warn", data=result.to_dict())
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

    def _run(self, step, argv, *, cwd=None, timeout=SCRIPT_TIMEOUT, extra_env=None, emit=None):
        if emit is not None:
            emit("post_step", f"Running {STEP_PREFIX}{step} …", data={"step": STEP_PREFIX + step})
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
        return self._run(step, [self.python, str(Path(self.scripts_dir) / name), *args], **kw)

    def module(self, step, name, *args, **kw):
        return self._run(step, [self.python, "-m", name, *args], **kw)

    def manage(self, step, args, emit=None, timeout=SCRIPT_TIMEOUT):
        if emit is not None:
            emit("post_step", f"Running {STEP_PREFIX}{step} …", data={"step": STEP_PREFIX + step})
        result = run_step(STEP_PREFIX + step, args, self.base_dir, timeout=timeout)
        return self._record(result, emit)

    def skip(self, step, reason, emit=None):
        return self._record(StepResult(step=STEP_PREFIX + step, skipped_reason=reason), emit)

    # -- environment --------------------------------------------------------

    def write_config(self) -> None:
        """zango_env.py's config, beside the run (it finds it through $ZAS_CONFIG)."""
        # The interpreter's own environment (never resolve the symlink: a venv's
        # bin/python points at the base Python, which lacks Django).
        venv = sys.prefix if self.python == sys.executable else str(Path(self.python).parent.parent)
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
        host = self.app_domain if ":" in self.app_domain or not parsed.port else (
            f"{self.app_domain}:{parsed.port}"
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

    # -- before the agent ------------------------------------------------

    def prepare(self, emit=None) -> None:
        """Phases 0-2 and the frontend prep of Phase 6. Raises StudioError."""
        if emit:
            emit(
                "sys",
                "App Studio build: the platform runs the skill's scripts; the agent writes the code.",
                level="sys",
            )
        self.write_config()
        self.check_spec = self._write_check_spec()
        checked = self.script(
            "spec_check", "spec_check.py", self.check_spec, "--workspace", self.workspace,
            "--quiet", emit=emit,
        )
        if checked.returncode != 0:
            raise StudioError("SpecCheckFailed", self._spec_errors(checked))
        self.install_runtime(emit)
        self.prepare_frontend(emit)

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
            raise StudioError("SpecCheckFailed", f"The approved spec could not be read: {exc}")
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
        more = f"\n… and {len(errors) - 30} more (.zas/issues.md)" if len(errors) > 30 else ""
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
            shutil.copytree(src, dst, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
            shutil.copyfile(self.zas_dir / "spec.resolved.json", dst / "spec.json")
            registered = register_module(self.workspace, "zas_core", "backend.zas_core")
        except Exception as exc:  # noqa: BLE001
            raise StudioError("RuntimeInstallFailed", f"Could not copy the zas_core runtime: {exc}")
        self._record(
            StepResult(
                step=STEP_PREFIX + "runtime",
                command=["copy", str(src), str(dst)],
                duration_ms=int((time.monotonic() - started) * 1000),
                stdout_tail=(
                    "zas_core copied; spec.json is the resolved spec; "
                    + ("registered in settings.json" if registered else "already registered")
                ),
            ),
            emit,
        )
        selftest = self.script("selftest", "selftest_runtime.py", "--workspace", self.workspace, emit=emit)
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
            if result.returncode == 0:
                return False
            self.frontend_reason = f"{result.step} failed (exit {result.returncode})"
            return True

        if not (fe / "package.json").is_file():
            if failed(self._run("frontend:scaffold", ["npx", "--yes", "@zango-core/create-zango-app", "frontend"],
                                cwd=str(ws), timeout=NPM_TIMEOUT, emit=emit)):
                return
        self._write_proxy_routes(fe)
        if failed(self._run("frontend:pin", ["npm", "install", "--save-exact", "--legacy-peer-deps",
                                             f"@zango-core/crud@{CRUD_VERSION}", f"lucide-react@{LUCIDE_VERSION}"],
                            cwd=str(fe), timeout=NPM_TIMEOUT, emit=emit)):
            return
        (fe / "patches").mkdir(exist_ok=True)
        for patch in (skill / "assets" / "frontend" / "patches").glob("*.patch"):
            shutil.copyfile(patch, fe / "patches" / patch.name)
        if failed(self._run("frontend:patch-package", ["npm", "install", "--save-dev", "--legacy-peer-deps",
                                                       "patch-package"],
                            cwd=str(fe), timeout=NPM_TIMEOUT, emit=emit)):
            return
        _set_postinstall(fe / "package.json")
        if failed(self._run("frontend:patch", ["npx", "--no", "patch-package"], cwd=str(fe),
                            timeout=NPM_TIMEOUT, emit=emit)):
            return
        if (fe / "src" / "zas").exists():
            shutil.rmtree(fe / "src" / "zas")
        shutil.copytree(skill / "assets" / "frontend" / "zas", fe / "src" / "zas",
                        ignore=shutil.ignore_patterns("__pycache__"))
        (fe / "src" / "custom").mkdir(parents=True, exist_ok=True)
        shutil.copyfile(self.zas_dir / "spec.ui.json", fe / "src" / "custom" / "spec.ui.json")
        shutil.copyfile(skill / "assets" / "templates" / "frontend" / "index.css", fe / "src" / "index.css")
        if failed(self.script("frontend:icons", "lucide_icons.py", "--workspace", self.workspace, emit=emit)):
            return
        self.frontend_ready = True

    def _write_proxy_routes(self, fe: Path) -> None:
        """frontend/.env VITE_PROXY_ROUTES: the package routes plus every module prefix, never /app."""
        try:
            resolved = json.loads((self.zas_dir / "spec.resolved.json").read_text(encoding="utf-8"))
        except (OSError, ValueError):
            resolved = {}
        routes = list(BASE_PROXY_ROUTES)
        for module in resolved.get("modules") or []:
            url = "/" + str(module.get("url") or module.get("code") or "").strip("/")
            if url not in ("/", "/app") and url not in routes:
                routes.append(url)
        line = "VITE_PROXY_ROUTES=" + ",".join(routes) + ","
        env_path = fe / ".env"
        lines = env_path.read_text(encoding="utf-8").splitlines() if env_path.is_file() else []
        lines = [x for x in lines if not x.startswith("VITE_PROXY_ROUTES=")] + [line]
        env_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    # -- after the agent -------------------------------------------------

    def bring_up(self, creds: dict, emit=None) -> bool:
        """Phase 5 and Phase 6 step 7, in the skill's order. Stops at the first failure."""
        app = self.app_name
        failed_at = None

        def platform(cmd):
            return self.script(
                f"platform:{cmd}", "zango_platform.py", cmd, "--workspace", self.workspace,
                "--platform", self.platform_url, extra_env=creds, emit=emit,
            )

        steps = [
            ("platform:roles", lambda: platform("roles")),
            ("ws_makemigration", lambda: self.manage("ws_makemigration", ["ws_makemigration", app, "--noinput"], emit)),
            ("prune_first_migration", self._prune),
            ("ws_migrate", lambda: self.manage("ws_migrate", ["ws_migrate", app, "--noinput"], emit)),
            ("platform:sync", lambda: platform("sync")),
            ("platform:schedule", lambda: platform("schedule")),
            ("platform:users", lambda: platform("users")),
            ("platform:check", lambda: platform("check")),
            ("sync_static", lambda: self.manage("sync_static", ["sync_static", app], emit)),
            ("collectstatic", lambda: self.manage("collectstatic", ["collectstatic", "--noinput"], emit)),
            ("platform:appbuilder", self._appbuilder(platform, emit)),
        ]
        for name, run in steps:
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
                "not the app's first build" if not self.first_build else "nothing to prune",
                emit,
            )
        self._pruned = True
        return self.script("prune_first_migration", "prune_first_migration.py", str(initial), emit=emit)

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

    def verify(self, emit=None, only: dict | None = None, bring_up_ok: bool = True) -> dict:
        """Run the hole audit and the test layers; ``only`` = {layer: [groups]} re-runs just those."""
        layers = {}
        playwright = self.has_playwright()
        reachable, unreachable = self.app_reachable()
        users_ok = (self.zas_dir / "test_users.json").is_file()
        for name, runner, browser, needs_app in LAYERS:
            if only is not None and name not in only:
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
            elif name == "ui" and not self.frontend_ready and not (Path(self.workspace) / "frontend").is_dir():
                reason = "no frontend was built"
            if reason:
                self.skip(f"test:{name}", reason, emit)
                layers[name] = LayerResult(name=name, status="skip", reason=reason)
                continue
            layers[name] = self._run_layer(name, runner, groups, emit)
        return layers

    def _run_layer(self, name, runner, groups, emit) -> LayerResult:
        if runner == "audit":
            result = self.script("test:audit_holes", "spec_check.py", self.check_spec or self.spec_path,
                                 "--workspace", self.workspace, "--audit-holes", emit=emit)
            if result.returncode == 0:
                return LayerResult(name=name, counts={"pass": 1, "fail": 0, "skip": 0})
            return LayerResult(
                name=name,
                status="fail",
                counts={"pass": 0, "fail": 1, "skip": 0},
                failures=[{"id": "audit_holes", "title": "every hole implemented with its marker and status",
                           "detail": (result.stdout_tail or result.stderr_tail).strip()[-1500:]}],
            )
        args = ["--workspace", self.workspace]
        if name == "design_lint":
            args += ["--only", "lint"]
        elif name == "design":
            args += ["--only", ",".join(groups or DESIGN_BROWSER_GROUPS)]
        elif groups:
            args += ["--only", ",".join(groups)]
        result = self.module(f"test:{name}", runner, *args, timeout=TEST_TIMEOUT, emit=emit)
        layer_key = "design" if name in ("design", "design_lint") else name
        records = [r for r in _load_results(self.workspace) if r.get("layer") == layer_key]
        if name == "design_lint":
            records = [r for r in records if str(r.get("id", "")).startswith("design.lint")]
        elif name == "design":
            records = [r for r in records if not str(r.get("id", "")).startswith("design.lint")]
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
            failures = [{"id": f"{name}.crashed", "title": f"the {name} layer did not run",
                         "detail": (result.stderr_tail or result.stdout_tail).strip()[-1500:]}]
        status = "fail" if failures else "pass"
        return LayerResult(
            name=name,
            status=status,
            counts=counts,
            failures=failures,
            groups=sorted({g for g in (_group_of(name, f["id"]) for f in failures) if g}),
        )

    def report(self, emit=None) -> dict:
        result = self.module("report", "zas_test.report", "--workspace", self.workspace, emit=emit)
        md, html = self.zas_dir / "build_report.md", self.zas_dir / "build_report.html"
        summary = md.read_text(encoding="utf-8")[:REPORT_SUMMARY_CHARS] if md.is_file() else ""
        return {
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
                lines.append(f"- `{f.get('id')}`{who} {f.get('title', '')}{where}: {str(f.get('detail', ''))[:400]}")
            lines.append("")
        return "\n".join(lines).strip() + "\n"

    def finish(self, creds: dict, resume_agent=None, rounds: int = 2, emit=None) -> StudioOutcome:
        """Bring-up, checks, fix rounds, report.

        ``resume_agent(digest) -> bool`` resumes the agent's session with the
        digest; False (budget, error, abort) ends the fix rounds.
        """
        bring_up_ok = self.bring_up(creds, emit)
        layers = self.verify(emit, bring_up_ok=bring_up_ok)
        done = 0
        while done < rounds and resume_agent is not None and (
            not bring_up_ok or any(x.status == "fail" for x in layers.values())
        ):
            done += 1
            if emit:
                emit("sys", f"Fix round {done} of {rounds}: sending the failures back to the agent.", level="sys")
            if not resume_agent(self.digest(bring_up_ok, layers)):
                if emit:
                    emit("sys", "The agent could not continue; no more fix rounds.", level="warn")
                break
            was_ok = bring_up_ok
            bring_up_ok = self.bring_up(creds, emit)
            if not was_ok:
                fresh = self.verify(emit, bring_up_ok=bring_up_ok)
            else:
                only = {n: x.groups for n, x in layers.items() if x.status == "fail"}
                fresh = self.verify(emit, only=only, bring_up_ok=bring_up_ok)
            layers.update(fresh)
        report = self.report(emit)
        ok = bring_up_ok and not any(x.status == "fail" for x in layers.values())
        return StudioOutcome(ok=ok, bring_up_ok=bring_up_ok, layers=layers, rounds=done, report=report)

    def test_users(self) -> list:
        """The run's test users from .zas/test_users.json, in the run's own format."""
        try:
            data = json.loads((self.zas_dir / "test_users.json").read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return []
        out = []
        for user in data.get("users") or []:
            if not user.get("email"):
                continue
            roles = user.get("roles") or []
            entry = {"email": user["email"], "role": roles[0] if roles else "", "status": "created"}
            if user.get("password"):
                entry["password"] = user["password"]
            out.append(entry)
        return out


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


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
        data = json.loads((Path(workspace) / ".zas" / "test_results.json").read_text(encoding="utf-8"))
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
