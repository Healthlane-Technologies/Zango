"""
The resolved spec at runtime.

backend/zas_core/spec.json is a copy of .zas/spec.resolved.json, refreshed every
time the spec checker runs (Phase 3, step 0). Everything that is configuration
(expressions, choices, statuses, 360 layouts, hole function names) is read from
here, so generated classes stay short: they declare Zango fields and set
`zas_entity = "<code>"`.

The file is re-read when its mtime changes, so a spec refresh needs no restart
for config-only changes. Changes to models/forms/tables still need one.
"""

import functools
import importlib
import json
import logging
import os
import threading

logger = logging.getLogger(__name__)

_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "spec.json")
_lock = threading.Lock()
_cache = {"mtime": None, "data": None}

# backend package, e.g. "workspaces.vendor_hub.backend" - siblings are importable from it
BACKEND_PKG = __package__.rsplit(".", 1)[0] if __package__ and "." in __package__ else "backend"


def load():
    """The whole resolved spec (dict). Raises if spec.json is missing."""
    mtime = os.path.getmtime(_PATH)
    if _cache["mtime"] != mtime:
        with _lock:
            if _cache["mtime"] != mtime:
                with open(_PATH, encoding="utf-8") as f:
                    _cache["data"] = json.load(f)
                _cache["mtime"] = mtime
                _model.cache_clear()
    return _cache["data"]


def app():
    return load()["app"]


def entity(code):
    try:
        return load()["entities"][code]
    except KeyError:
        raise KeyError(f"zas: entity {code!r} is not in spec.json - re-run spec_check and copy spec.json")


def view(code):
    return load()["detail_views"][code]


def roles():
    return load()["roles"]


def entities():
    return load()["entities"]


def holes_for(where_prefix):
    return [h for h in load().get("holes", []) if h["where"].startswith(where_prefix)]


def hole_fn(where):
    """Function name of the hole registered at exactly this spec path, or None."""
    for h in load().get("holes", []):
        if h["where"] == where:
            return h["function"]
    return None


def _import(module, name):
    return importlib.import_module(f"{BACKEND_PKG}.{module}.{name}")


@functools.lru_cache(maxsize=None)
def _model(code):
    E = entity(code)
    mod = _import(E["module"], "models")
    return getattr(mod, E["names"]["model"])


def model(code):
    """Model class for an entity code."""
    return _model(code)


def workflow_class(code):
    E = entity(code)
    if not E.get("workflow"):
        return None
    try:
        return getattr(_import(E["module"], "workflow"), E["names"]["workflow"])
    except (ImportError, AttributeError):
        logger.exception("zas: workflow class for %s not found", code)
        return None


def table_class(code):
    E = entity(code)
    return getattr(_import(E["module"], "tables"), E["names"]["table"])


def hook(module, fn):
    """A function from backend/<module>/hooks.py, or None (logged) if not written yet."""
    if not fn:
        return None
    try:
        hooks = _import(module, "hooks")
    except ImportError:
        logger.warning("zas: backend/%s/hooks.py not found (looking for %s)", module, fn)
        return None
    f = getattr(hooks, fn, None)
    if f is None:
        logger.warning("zas: hook %s.%s is not implemented yet", module, fn)
    return f


def call_hook(module, fn, *args, default=None, **kwargs):
    f = hook(module, fn)
    if f is None:
        return default
    return f(*args, **kwargs)


def tone_of_choice(entity_code, field, value):
    E = entity(entity_code)
    for f in E["fields"]:
        if f["key"] == field:
            for c in f.get("choices") or []:
                if str(c["id"]) == str(value):
                    return c.get("color"), c.get("label")
    return None, None
