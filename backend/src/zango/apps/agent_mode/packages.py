"""Ensure an app has the packages Agent Mode expects it to build against.

Without `appbuilder`, `crud` and `workflow` the agent has no `BaseCrudView`,
no `FormRenderer`, no workflow engine and no route/menu configuration — so it
hand-rolls Django views and a bespoke JSON API instead. That is exactly what
the first real run did, and it is not a Zango app in any meaningful sense.

Installation is credential-free: `zango.core.package_utils.install_package`
pulls from a public S3 bucket with an unsigned client. The platform-admin
credentials that made the interactive skill's package step unusable in server
mode are not needed here.

Ordering matters and is not cosmetic. `dep_check` requires a dependency to be
**already installed** before it will accept a dependent's version, so
versions must be resolved one package at a time, re-reading what is installed
after each step.
"""

from __future__ import annotations

import contextlib
import logging
import os
import sys

from dataclasses import dataclass


logger = logging.getLogger("zango.agent_mode")

# Install order is a dependency order, not a preference.
REQUIRED_PACKAGES = ("appbuilder", "crud", "workflow")

_SUCCESS_MARKERS = ("Package Installed", "Package already installed")


@contextlib.contextmanager
def _interpreter_on_path():
    """Make bare ``python`` resolve to the interpreter we are running under.

    ``install_package`` shells out with ``subprocess.run("python manage.py …",
    shell=True)`` and never checks the result. Under a Celery worker — or any
    process started without the virtualenv activated — bare ``python`` is the
    system interpreter, which has no Django. The three internal steps
    (sync_static, collectstatic, ws_migrate --package) then fail **silently**
    and the package reports as installed with no tables created. Observed
    exactly that on the first attempt.
    """
    bindir = os.path.dirname(sys.executable)
    previous = os.environ.get("PATH", "")
    if bindir and bindir not in previous.split(os.pathsep):
        os.environ["PATH"] = bindir + os.pathsep + previous
    try:
        yield
    finally:
        os.environ["PATH"] = previous


@dataclass
class PackageResult:
    name: str
    version: str = ""
    status: str = ""  # "installed" | "already" | "failed" | "unavailable"
    message: str = ""

    @property
    def ok(self) -> bool:
        return self.status in ("installed", "already")


def available_versions(package: str) -> list:
    """Versions of *package* in the package bucket, newest first."""
    from botocore import UNSIGNED
    from botocore.client import Config

    import boto3

    from django.conf import settings

    from packaging.version import InvalidVersion, Version

    try:
        s3 = boto3.client("s3", config=Config(signature_version=UNSIGNED))
        listing = s3.list_objects_v2(
            Bucket=settings.PACKAGE_BUCKET_NAME, Prefix=f"packages/{package}/"
        )
    except Exception:  # noqa: BLE001
        logger.exception("agent_mode: could not list versions for %s", package)
        return []

    versions = set()
    for entry in listing.get("Contents", []) or []:
        parts = entry["Key"].split("/")
        # packages/<name>/<version>/<file>
        if len(parts) >= 3 and parts[1] == package and parts[2]:
            versions.add(parts[2])

    parsed = []
    for raw in versions:
        try:
            parsed.append((Version(raw), raw))
        except InvalidVersion:
            continue
    return [raw for _, raw in sorted(parsed, reverse=True)]


def latest_compatible(package: str, tenant_name: str) -> str:
    """Highest version whose manifest passes dep_check for this app."""
    from zango.core.package_utils import (
        dep_check,
        get_installed_packages,
        get_package_manifest,
    )

    try:
        installed = get_installed_packages(tenant_name)
    except Exception:  # noqa: BLE001
        installed = {}

    for version in available_versions(package):
        manifest = get_package_manifest(package, version)
        try:
            if not manifest or dep_check(package, version, manifest, installed):
                return version
        except Exception:  # noqa: BLE001
            continue
    return ""


def ensure_packages(tenant_name: str, packages=REQUIRED_PACKAGES, emit=None) -> list:
    """Install any missing required packages, in dependency order.

    Must run with cwd == BASE_DIR: `install_package` uses relative
    ``workspaces/...`` paths and shells out to `python manage.py`. The
    management command that wraps this is what guarantees that.
    """
    from zango.core.package_utils import install_package, package_installed

    results = []
    for name in packages:
        if package_installed(name, tenant_name):
            results.append(PackageResult(name, status="already"))
            if emit:
                emit(f"{name}: already installed")
            continue

        version = latest_compatible(name, tenant_name)
        if not version:
            results.append(
                PackageResult(
                    name,
                    status="unavailable",
                    message="no compatible version found in the package bucket",
                )
            )
            if emit:
                emit(f"{name}: no compatible version available", is_error=True)
            continue

        if emit:
            emit(f"{name}: installing {version} …")
        # install_package never raises; it returns a status string, and the
        # failure string carries a traceback.
        with _interpreter_on_path():
            message = install_package(name, version, tenant_name)
        ok = any(marker in str(message) for marker in _SUCCESS_MARKERS)
        results.append(
            PackageResult(
                name,
                version=version,
                status="installed" if ok else "failed",
                message=str(message)[:2000],
            )
        )
        if emit:
            emit(
                f"{name} {version}: {'installed' if ok else 'FAILED'}",
                is_error=not ok,
            )
    return results
