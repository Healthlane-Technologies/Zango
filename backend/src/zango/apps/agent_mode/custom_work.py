"""The custom part of an App Studio spec: what the build writes by hand.

Lists, forms, workflows, 360 pages, views and dashboards are built by the runtime from what the
spec declares. Custom screens (pages, 360 tabs and panels drawn by a `preview` sketch) and custom
requirements are written by the build agent, so each carries a contract: what it reads, what the
user does with it and, above all, `acceptance` — how anyone can tell it works. The analyst cannot
mark a spec ready while one is missing; the counts show the user how much of the app is custom.
"""

from __future__ import annotations

from .preview_probe import custom_screens


# Requirements that happen on their own need to say when.
NEEDS_TRIGGER = {"notification", "scheduled"}


def custom_requirements(doc) -> dict:
    """{spec path: requirement} for app, entity and 360 custom requirements of a plain spec."""
    out = {}
    if not isinstance(doc, dict):
        return out
    for i, cr in enumerate((doc.get("app") or {}).get("custom_requirements") or []):
        out[f"/app/custom_requirements/{i}"] = cr
    for module in doc.get("modules") or []:
        if not isinstance(module, dict) or not module.get("code"):
            continue
        for entity in module.get("entities") or []:
            if not isinstance(entity, dict) or not entity.get("code"):
                continue
            base = f"/modules/@{module['code']}/entities/@{entity['code']}/custom_requirements"
            for i, cr in enumerate(entity.get("custom_requirements") or []):
                out[f"{base}/{i}"] = cr
    for dv in doc.get("detail_views") or []:
        if isinstance(dv, dict) and dv.get("code"):
            for i, cr in enumerate(dv.get("custom_requirements") or []):
                out[f"/detail_views/@{dv['code']}/custom_requirements/{i}"] = cr
    return out


def contract_gaps(doc) -> list:
    """[(path, what is missing)] for every custom screen and requirement without its contract."""
    gaps = []
    for path, node in custom_screens(doc).items():
        if not (node or {}).get("acceptance"):
            gaps.append((path, "acceptance: how the user will know this screen works"))
    for path, cr in custom_requirements(doc).items():
        cr = cr or {}
        if not cr.get("acceptance"):
            gaps.append((path, "acceptance: how anyone can tell it was done"))
        if cr.get("area") in NEEDS_TRIGGER and not (cr.get("trigger") or {}).get(
            "event"
        ):
            gaps.append(
                (
                    path,
                    f"trigger: when this {cr['area']} happens (event: transition, create, schedule…)",
                )
            )
    return gaps


def counts(doc) -> dict:
    """How much of the app is custom: {screens, requirements, dashboards}."""
    pages = (doc.get("pages") or []) if isinstance(doc, dict) else []
    return {
        "screens": len(custom_screens(doc)),
        "requirements": len(custom_requirements(doc)),
        "dashboards": sum(
            1 for p in pages if isinstance(p, dict) and p.get("type") == "dashboard"
        ),
    }
