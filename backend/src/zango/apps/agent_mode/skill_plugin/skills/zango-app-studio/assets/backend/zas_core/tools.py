"""
Built-in AI tools (spec ai.agents[].tools: {use: search_records | read_record, entity}).

Zango registers them on "Sync tools" like any tools.py. They answer only while one of the
app's AI helpers is running (zas_core.ai.acting()), only for the entities that helper lists,
and only with rows the person it runs for can see: the same row rules as the list page.
"""

from django.db.models import Q

from zango.ai.tools.decorator import ToolParam, ToolSafety, tool

from . import access
from . import ai as zai
from . import records as zr
from . import spec as zs

HIDDEN = {"file", "image", "json"}


def _allowed(entity):
    act = zai.acting()
    if not act:
        return None, "This tool only works inside one of the app's AI helpers."
    if entity not in (act["agent"].get("tool_entities") or []):
        return None, f"{entity!r} is not something this helper may look up."
    return act, None


def _scoped(entity, act):
    qs = zs.model(entity).objects.all()
    req = act.get("request")
    if act.get("role"):
        qs = access.scope_queryset(entity, qs, req)
    return qs


def _row(E, obj, paths):
    out = {"id": str(obj.object_uuid)}
    for p in paths:
        fv = zr.field_value(E, obj, p)
        out[fv["label"]] = fv["display"]
    return out


def _list_paths(E):
    cols = [c["key"] for c in (E.get("table") or {}).get("columns") or [] if c.get("source") == "field"]
    types = {f["key"]: f["type"] for f in E["fields"]}
    paths = [E["display"]] + [k for k in cols if k != E["display"] and types.get(k) not in HIDDEN]
    return paths or [f["key"] for f in E["fields"] if f["type"] not in HIDDEN][:8]


@tool(
    name="zas_search_records",
    description="Search the app's records of one kind (entity) by text. Returns up to `limit` matches with their main "
    "columns and an id to pass to zas_read_record. Only records the current person may see are returned.",
    section="zas",
    safety=ToolSafety.READ_ONLY,
)
def zas_search_records(
    entity: str = ToolParam(description="The kind of record, e.g. invoice"),
    query: str = ToolParam(description="Words to look for; empty lists the latest records", default=""),
    limit: int = ToolParam(description="How many to return (at most 50)", default=10),
) -> dict:
    act, err = _allowed(entity)
    if err:
        return {"error": err}
    E = zs.entity(entity)
    qs = _scoped(entity, act)
    words = [w for w in str(query or "").split() if w]
    texty = [f["key"] for f in E["fields"] if f["type"] in ("text", "long_text", "email", "phone", "url")]
    for w in words:
        q = Q()
        for k in texty:
            q |= Q(**{f"{k}__icontains": w})
        qs = qs.filter(q) if texty else qs
    limit = max(1, min(int(limit or 10), 50))
    paths = _list_paths(E)
    rows = list(qs.order_by("-id")[:limit])
    return {"entity": entity, "count": len(rows), "records": [_row(E, r, paths) for r in rows]}


@tool(
    name="zas_read_record",
    description="Read one record (entity + the id from zas_search_records): all its fields except files.",
    section="zas",
    safety=ToolSafety.READ_ONLY,
)
def zas_read_record(
    entity: str = ToolParam(description="The kind of record, e.g. invoice"),
    id: str = ToolParam(description="The record id (from zas_search_records)"),
) -> dict:
    act, err = _allowed(entity)
    if err:
        return {"error": err}
    E = zs.entity(entity)
    uid = access.clean_uuid(id)
    obj = _scoped(entity, act).filter(object_uuid=uid).first() if uid else None
    if obj is None:
        return {"error": "No such record, or it is not visible to this person."}
    return _row(E, obj, [f["key"] for f in E["fields"] if f["type"] not in HIDDEN])
