#!/usr/bin/env python3
"""
Run Zango commands the right way for this machine (docker or venv), without anyone retyping them.

    zango_env.py detect  --workspace <ws> | --project <project dir>     find / write .claude/zango-config.json
    zango_env.py manage  --workspace <ws> -- ws_makemigration <app>     python manage.py … (docker exec or venv)
    zango_env.py zango   --workspace <ws> -- update-apps --app_name <app>
    zango_env.py static  --workspace <ws>                               sync_static <app> + collectstatic
    zango_env.py celery  --workspace <ws>                               restart the Celery worker (docker) / say how (venv)
    zango_env.py health  [--platform http://localhost:8000]             is the platform up?
    zango_env.py call    --workspace <ws> -- sites.tasks.site__req__2     run one backend function in the app's tenant
                                                                         (scenario tests: scheduled jobs, hooks); prints ZAS_RESULT=<json>

Layout (references/setup.md):
  project dir  = the directory with manage.py; workspaces live in <project dir>/workspaces/<app>
  docker mode  = <project dir>/../docker_compose.yml (the deploy/ folder mounted at /zango);
                 commands run as `docker compose -f <deploy>/docker_compose.yml exec app bash -c "cd <project> && …"`
  venv mode    = `cd <project dir> && <venv>/bin/python manage.py …`
Config: .claude/zango-config.json in the project dir or any parent (or the file named by $ZAS_CONFIG):
  {"setup_mode": "docker"} or {"setup_mode": "venv", "venv_path": "/abs/path"}  (+ optional "project_dir")
"""

import argparse
import json
import os
import shlex
import subprocess
import sys
import urllib.request

CONFIG = os.path.join(".claude", "zango-config.json")


class EnvError(RuntimeError):
    pass


def project_dir(ws=None, project=None):
    if project:
        p = os.path.abspath(project)
    else:
        p = os.path.abspath(os.path.join(ws, "..", ".."))
    if not os.path.exists(os.path.join(p, "manage.py")):
        raise EnvError(f"no manage.py in {p}: expected <project dir>/workspaces/<app>")
    return p


def find_config(start):
    # Inside the Zango platform the build runner writes the config next to the run, never into the
    # project, and points here with ZAS_CONFIG (references/server-mode.md).
    forced = os.environ.get("ZAS_CONFIG")
    if forced:
        if not os.path.exists(forced):
            raise EnvError(f"ZAS_CONFIG={forced} does not exist")
        return forced
    d = os.path.abspath(start)
    for _ in range(6):
        p = os.path.join(d, CONFIG)
        if os.path.exists(p):
            return p
        d = os.path.dirname(d)
    return None


def compose_file(proj):
    for name in ("docker_compose.yml", "docker-compose.yml"):
        p = os.path.join(os.path.dirname(proj), name)
        if os.path.exists(p):
            return p
    return None


def docker_running(compose):
    try:
        out = subprocess.run(["docker", "compose", "-f", compose, "ps", "--services", "--filter", "status=running"],
                             capture_output=True, text=True, timeout=30)
        return "app" in out.stdout.split()
    except (OSError, subprocess.SubprocessError):
        return False


def venv_candidates(proj):
    seen = []
    for base in (proj, os.path.dirname(proj), os.path.dirname(os.path.dirname(proj))):
        for name in ("venv", ".venv", "env", "zango_venv"):
            p = os.path.join(base, name)
            if os.path.exists(os.path.join(p, "bin", "zango")) and p not in seen:
                seen.append(p)
    return seen


def detect(ws=None, project=None, write=True):
    """Return the config dict; write it when it had to be inferred. EnvError when it cannot decide."""
    proj = project_dir(ws, project)
    path = find_config(proj)
    if path:
        cfg = json.load(open(path))
        if cfg.get("setup_mode") == "venv" and not os.path.exists(os.path.join(cfg.get("venv_path", ""), "bin", "python")):
            raise EnvError(f"{path}: venv_path {cfg.get('venv_path')!r} has no bin/python")
        cfg.setdefault("project_dir", proj)
        return cfg
    compose = compose_file(proj)
    if compose and docker_running(compose):
        cfg = {"setup_mode": "docker"}
    else:
        venvs = venv_candidates(proj)
        if len(venvs) == 1:
            cfg = {"setup_mode": "venv", "venv_path": venvs[0]}
        else:
            raise EnvError("cannot tell docker from venv: "
                           + (f"several venvs with zango: {venvs}" if venvs else "no running app container and no venv with zango found")
                           + f". Ask the user, then write {os.path.join(proj, CONFIG)}")
    cfg["project_dir"] = proj
    if write:
        os.makedirs(os.path.join(proj, ".claude"), exist_ok=True)
        with open(os.path.join(proj, CONFIG), "w") as f:
            json.dump(cfg, f, indent=2)
    return cfg


def command(cfg, argv, tool="manage"):
    """The argv list to run `python manage.py <argv>` (tool=manage) or `zango <argv>` (tool=zango)."""
    proj = cfg["project_dir"]
    if cfg["setup_mode"] == "docker":
        compose = compose_file(proj)
        if not compose:
            raise EnvError(f"docker mode but no docker_compose.yml next to {proj}")
        inner = ("python manage.py " if tool == "manage" else "zango ") + " ".join(shlex.quote(x) for x in argv)
        if tool == "zango" and argv and argv[0] == "update-apps":
            inner = "SINGLE_BEAT_REDIS_SERVER=redis://redis:6379/1 single-beat " + inner
        return ["docker", "compose", "-f", compose, "exec", "-T", "app", "bash", "-c",
                f"cd {shlex.quote(os.path.basename(proj))} && {inner}"], None
    v = cfg["venv_path"]
    exe = [os.path.join(v, "bin", "python"), "manage.py"] if tool == "manage" else [os.path.join(v, "bin", "zango")]
    return exe + list(argv), proj


def run(cfg, argv, tool="manage", check=True):
    cmd, cwd = command(cfg, argv, tool)
    print("zango_env: $ " + " ".join(shlex.quote(c) for c in cmd), file=sys.stderr)
    r = subprocess.run(cmd, cwd=cwd)
    if check and r.returncode != 0:
        raise EnvError(f"command failed (exit {r.returncode})")
    return r.returncode


def call_script(app, target, args):
    """Python for `manage.py shell -c`: load the app's tenant + workspace, call backend.<target>(*args)."""
    mod, fn = target.rsplit(".", 1)
    return (
        "import json, importlib\n"
        "from django.db import connection\n"
        "from zango.apps.shared.tenancy.models import TenantModel\n"
        "from zango.apps.dynamic_models.workspace.base import Workspace\n"
        f"t = TenantModel.objects.get(name={app!r}); connection.set_tenant(t)\n"
        "Workspace(t, as_systemuser=True).ready()\n"
        f"f = getattr(importlib.import_module('workspaces.{app}.backend.{mod}'), {fn!r})\n"
        f"r = f(*{list(args)!r})\n"
        "print('ZAS_RESULT=' + json.dumps(r, default=str))\n"
    )


def app_of(ws):
    with open(os.path.join(ws, "settings.json"), encoding="utf-8") as f:
        return json.load(f)["app_name"]


def health(url):
    try:
        with urllib.request.urlopen(url.rstrip("/") + "/platform", timeout=10) as r:
            return r.status < 500
    except Exception:
        return False


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    rest = []
    if "--" in argv:
        i = argv.index("--")
        argv, rest = argv[:i], argv[i + 1:]
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("command", choices=["detect", "manage", "zango", "static", "celery", "health", "call"])
    ap.add_argument("--workspace")
    ap.add_argument("--project")
    ap.add_argument("--platform", default="http://localhost:8000")
    a = ap.parse_args(argv)
    try:
        if a.command == "health":
            up = health(a.platform)
            print(f"platform {'up' if up else 'NOT reachable'} at {a.platform}")
            return 0 if up else 1
        if not (a.workspace or a.project):
            ap.error("--workspace or --project is required")
        cfg = detect(a.workspace, a.project)
        if a.command == "detect":
            print(json.dumps(cfg, indent=2))
        elif a.command == "manage":
            return run(cfg, rest)
        elif a.command == "zango":
            return run(cfg, rest, tool="zango")
        elif a.command == "call":
            if not rest:
                ap.error("call needs a function path after --, e.g. sites.tasks.site__req__2")
            return run(cfg, ["shell", "-c", call_script(app_of(a.workspace), rest[0], rest[1:])])
        elif a.command == "static":
            app = app_of(a.workspace)
            run(cfg, ["sync_static", app])
            run(cfg, ["collectstatic", "--noinput"])
        elif a.command == "celery":
            if cfg["setup_mode"] == "docker":
                subprocess.run(["docker", "compose", "-f", compose_file(cfg["project_dir"]), "restart", "celery"], check=True)
                print("celery restarted")
            else:
                print("venv mode: restart your Celery worker yourself: "
                      f"cd {cfg['project_dir']} && {cfg['venv_path']}/bin/celery -A {os.path.basename(cfg['project_dir'])} worker -l info")
                return 3
    except EnvError as e:
        print(f"zango_env: {e}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
