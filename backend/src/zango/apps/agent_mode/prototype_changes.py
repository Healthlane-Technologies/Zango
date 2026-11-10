"""What a change request does to the app's current preview.

A change starts on the prototype of the app's last approved requirement (the *current app*) and edits
a copy. The console shows that copy as it changes, marks the screens the change touched, and can flip to
the current app for comparison. The current app is the approved requirement's own parts: a change never
writes to them, so abandoning a change loses nothing.
"""

import hashlib
import json

from .models import AgentRequirement, RequirementStatus


def current_app_requirement(requirement=None):
    """The app's current approved requirement (other than `requirement`): the baseline a change starts on."""
    qs = AgentRequirement.objects.filter(status=RequirementStatus.APPROVED)
    if requirement is not None and getattr(requirement, "pk", None):
        qs = qs.exclude(pk=requirement.pk)
    return qs.order_by("-approved_at", "-created_at").first()


def _digest(value) -> str:
    return hashlib.sha1(
        str(value if value is not None else "").encode("utf-8")
    ).hexdigest()


def _screen_id(name: str):
    if name.startswith("screens/") and name.endswith(".js"):
        return name[len("screens/") : -len(".js")]
    return None


def _titles(parts) -> dict:
    try:
        manifest = json.loads((parts or {}).get("manifest.json") or "{}")
    except (TypeError, ValueError):
        return {}
    return {
        str(s["id"]): str(s.get("title") or s["id"])
        for s in manifest.get("screens") or []
        if isinstance(s, dict) and s.get("id")
    }


def screen_diff(old, new) -> dict:
    """Screens the new parts changed, added and removed against the old ones, and whether anything shared
    (the look, the data, the menu) changed. A screen is its `screens/<id>.js` part."""
    old, new = old or {}, new or {}
    titles = {**_titles(old), **_titles(new)}
    was = {_screen_id(n): _digest(v) for n, v in old.items() if _screen_id(n)}
    now = {_screen_id(n): _digest(v) for n, v in new.items() if _screen_id(n)}

    def item(sid):
        return {"id": sid, "title": titles.get(sid, sid)}

    shared = sorted(
        n
        for n in set(old) | set(new)
        if not _screen_id(n)
        and n != "manifest.json"
        and _digest(old.get(n)) != _digest(new.get(n))
    )
    return {
        "changed": [item(s) for s in now if s in was and was[s] != now[s]],
        "added": [item(s) for s in now if s not in was],
        "removed": [item(s) for s in was if s not in now],
        "shared": shared,
    }


def _names(items, limit=2):
    names = [i["title"] for i in items]
    if len(names) <= limit:
        return " and ".join(names) if len(names) < 3 else ", ".join(names)
    return f"{', '.join(names[:limit])} and {len(names) - limit} more"


def headline(diff) -> str:
    """A change's name from what it does to the app: "Adds My Downloads", "Updates Openings"."""
    parts = []
    if diff["added"]:
        parts.append(f"Adds {_names(diff['added'])}")
    if diff["changed"]:
        parts.append(f"{'updates' if parts else 'Updates'} {_names(diff['changed'])}")
    if diff["removed"]:
        parts.append(f"{'removes' if parts else 'Removes'} {_names(diff['removed'])}")
    if not parts and diff["shared"]:
        parts.append("Updates the app's look and settings")
    return ", ".join(parts)[:80]


def retitle_change(requirement) -> bool:
    """Name a change after what it changes (the opening sentence is a poor name). True if the title moved."""
    if requirement.preview_mode != "open" or not requirement.prototype_parts:
        return False
    base = current_app_requirement(requirement)
    if base is None or not base.prototype_parts:
        return False
    title = headline(screen_diff(base.prototype_parts, requirement.prototype_parts))
    if not title or title == requirement.title:
        return False
    requirement.title = title
    return True


def describe(requirement):
    """The change summary the console shows, or None when there is nothing to compare with."""
    if requirement.preview_mode != "open" or requirement.status not in (
        RequirementStatus.GATHERING,
        RequirementStatus.READY,
    ):
        return None
    base = current_app_requirement(requirement)
    if base is None or not base.prototype_parts:
        return None
    diff = screen_diff(base.prototype_parts, requirement.prototype_parts)
    return {
        "baseline": {
            "uuid": str(base.object_uuid),
            "revision": base.prototype_revision,
            "title": base.title,
        },
        **diff,
        "headline": headline(diff),
        "has_changes": bool(
            diff["changed"] or diff["added"] or diff["removed"] or diff["shared"]
        ),
    }
