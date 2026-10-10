"""
ZasDetail - the 360 payload, added to the crud package's own detail fetch.

    class VendorDetail(ZasDetail, BaseDetail):
        zas_view = "vendor_360"
        class Meta:
            fields = [...every field the page reads...]

    class VendorTable(ZasTableMixin, ModelTable):
        class Meta:
            model = Vendor
            detail_class = VendorDetail

GET <endpoint>?view=detail&action=fetch_item_details&object_uuid=<uuid>
  → the standard payload + "zas" (contracts §8)
GET <endpoint>?view=detail&action=zas_timeline&object_uuid=<uuid>&tab=<code>
  → {"events": [...]} merged from audit logs and workflow transactions

Fixes two package behaviours (see references/zango/entity-360.md):
  * BaseDetail.get_object() looks the record up through the TABLE queryset; with
    ZasTableMixin that queryset is role-scoped but never parent-filtered on a
    detail request, so a filtered tab cannot 500 a row click. A missing or
    out-of-scope record returns zas.access = "not_found" (HTTP 200), never a 500.
  * Meta.sections / get_sections() is not used (it passes pk to an object_uuid lookup).
"""

import json
import logging

from django.db.models import Sum

from zango.core.api import get_api_response

from . import access
from . import expr as zx
from . import records as zr
from . import spec as zs

logger = logging.getLogger(__name__)


class _NotFound(Exception):
    pass


def _initials(s):
    parts = str(s or "?").strip().split()
    return ((parts[0][:1] if parts else "?") + (parts[1][:1] if len(parts) > 1 else "")).upper()


def _num(v):
    if v is None:
        return None
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


class ZasDetail:
    zas_view = None

    # ---------- object lookup ----------
    def get_object(self, object_uuid):
        uid = access.clean_uuid(object_uuid)
        if not uid:
            raise _NotFound()
        qs = self.table_obj.get_table_data_queryset()
        obj = qs.filter(object_uuid=uid).first()
        if obj is None:
            raise _NotFound()
        self._zas_obj = obj
        return obj

    # ---------- request entry ----------
    def get(self, request, *args, **kwargs):
        action = request.GET.get("action")
        if action in ("fetch_item_details", "zas_timeline"):
            V = zs.view(self.zas_view)
            role = access.role_name(request)
            hero = V["hero"]
            denied = (V.get("roles") and role not in V["roles"]) or \
                (zs.entity(hero).get("access") and not access.can(hero, "detail", role))
            if denied:
                return get_api_response(success=True, response_content={"zas": self._zas_state("no_access")}, status=200)
            try:
                if action == "zas_timeline":
                    obj = self.get_object(self.get_object_uuid())
                    return get_api_response(success=True, response_content=self.zas_timeline(obj, request.GET.get("tab")), status=200)
                return super().get(request, *args, **kwargs)
            except _NotFound:
                return get_api_response(success=True, response_content={"zas": self._zas_state("not_found")}, status=200)
        return super().get(request, *args, **kwargs)

    def _zas_state(self, state):
        V = zs.view(self.zas_view)
        return {"view": self.zas_view, "access": state, "states": V.get("states") or {}, "back_to": V.get("back_to")}

    def fetch_item_details(self):
        data = super().fetch_item_details()
        obj = getattr(self, "_zas_obj", None) or self.get_object(self.get_object_uuid())
        try:
            data["zas"] = self.zas_payload(obj)
        except Exception:
            logger.exception("zas: building the 360 payload failed for %s", self.zas_view)
            data["zas"] = {**self._zas_state("ok"), "error": "The page data could not be built. Check the server log."}
        return data

    # ---------- payload ----------
    def zas_payload(self, obj):
        req = self.request
        V = zs.view(self.zas_view)
        H = zs.entity(V["hero"])
        role = access.role_name(req)
        ctx = access.expr_ctx(req)
        self._zas_ctx, self._zas_role = ctx, role

        status = zx.current_status(obj) if H.get("workflow") else None
        tags = sorted(zx.current_tags(obj)) if H.get("workflow") else []
        wf = H.get("workflow") or {}
        smap = {s["code"]: s for s in wf.get("statuses", [])}
        tmap = {t["code"]: t for t in wf.get("tags", [])}

        out = {
            **self._zas_state("ok"),
            "record": {
                "uuid": str(obj.object_uuid), "pk": obj.pk, "status": status,
                "status_label": (smap.get(status) or {}).get("label"),
                "status_tone": (smap.get(status) or {}).get("color"),
                "tags": [{"code": c, "label": (tmap.get(c) or {}).get("label", c), "tone": (tmap.get(c) or {}).get("color")} for c in tags],
                "display": zr.field_value(H, obj, H["display"])["display"] if H["display"] != "id" else str(obj.pk),
            },
            "formats": {"locale": zs.app().get("locale"), "currency": zs.app().get("currency")},
        }
        out["header"] = self._zas_header(V, H, obj, out["record"])
        out["stats"] = self._zas_stats(V, H, obj)
        out["tabs"], out["panels"], out["mini_tables"] = self._zas_tabs(V, H, obj)
        out["actions"] = self._zas_actions(V, H, obj, status)
        out["custom"] = self._zas_custom(V, H, obj)
        return out

    def _ok(self, block, obj):
        if block.get("roles") and self._zas_role not in block["roles"]:
            return False
        if block.get("show_when_ast") is not None and not zx.evaluate(block["show_when_ast"], obj, self._zas_ctx):
            return False
        return True

    def _text(self, H, obj, value):
        if value is None:
            return None
        s = str(value)
        if "{" in s:
            return zr.interpolate(H, obj, s, txn_lookup=lambda k: zr.latest_form_value(obj, k))
        return zr.field_value(H, obj, s)["display"]

    def _zas_header(self, V, H, obj, rec):
        hd = V.get("header") or {}
        title = self._text(H, obj, hd.get("title")) if hd.get("title") else rec["display"]
        subtitle = " · ".join(x for x in (self._text(H, obj, s) for s in hd.get("subtitle") or []) if x and x != "—")
        av = hd.get("avatar") or {}
        image = zr.field_value(H, obj, av["image"]).get("url") if av.get("image") else None
        initials = _initials(self._text(H, obj, av.get("fallback_initials")) if av.get("fallback_initials") else title)
        badges = []
        for i, b in enumerate(hd.get("badges") or []):
            if not self._ok(b, obj):
                continue
            if b.get("source") == "status" and rec["status"]:
                badges.append({"key": "status", "label": rec["status_label"], "tone": rec["status_tone"]})
            elif b.get("source") == "tags":
                badges += [{"key": "tag:" + t["code"], "label": t["label"], "tone": t["tone"], "kind": "tag"} for t in rec["tags"]]
            elif b.get("field"):
                v = zr.field_value(H, obj, b["field"])
                if v["display"]:
                    badges.append({"key": b["field"], "label": (b.get("prefix") or "") + v["display"], "tone": b.get("tone") or v.get("tone") or "gray"})
        facts = []
        for i, f in enumerate(hd.get("facts") or []):
            if not self._ok(f, obj):
                continue
            item = {"key": f.get("field") or f.get("path") or f"fact{i + 1}", "label": f.get("label"),
                    "copy": bool(f.get("copyable")), "emphasis": bool(f.get("emphasis")), "link": None,
                    "format": f.get("format"), "order": i}
            if f.get("value"):
                item.update(value=None, display=self._text(H, obj, f["value"]))
            else:
                v = zr.field_value(H, obj, f.get("field") or f.get("path"), fmt=f.get("format"))
                item.update(value=v["value"], display=v["display"], type=v["type"])
                if f.get("link_to") and v.get("uuid"):
                    tv = zs.view(f["link_to"]) if f["link_to"] in zs.load()["detail_views"] else None
                    if tv and access.can(tv["hero"], "detail", self._zas_role) is not False:
                        item["link"] = {"view": f["link_to"], "uuid": v["uuid"]}
            if item.get("display") in (None, "") and f.get("fallback") is not None:
                item["display"] = f["fallback"]
            facts.append(item)
        banners = []
        for i, b in enumerate(hd.get("banners") or []):
            if not self._ok(b, obj):
                continue
            banners.append({"tone": b.get("tone", "info"), "text": self._text(H, obj, b.get("text", "")), "order": i})
        return {"title": title, "subtitle": subtitle, "avatar": {"image": image, "initials": initials},
                "badges": badges, "facts": facts, "banners": banners,
                "back_to": V.get("back_to")}

    # child queryset scoped to this hero and to the viewer's own row rules
    def _children(self, child_code, via, obj):
        C = zs.entity(child_code)
        Model = zs.model(child_code)
        info = None
        for p in (C.get("parents") or {}).values():
            if p["hero"] == zs.view(self.zas_view)["hero"] and (via is None or p["via"] == via):
                info = p
                break
        if info is None:
            return Model.objects.none()
        qs = Model.objects.filter(**{info["lookup"]: obj.object_uuid})
        return access.scope_queryset(child_code, qs, self.request)

    def _zas_stats(self, V, H, obj):
        out = []
        for i, s in enumerate(V.get("stats") or []):
            if not self._ok(s, obj):
                continue
            val = s.get("value") or {}
            value = None
            computed = False
            try:
                if val.get("count") or val.get("sum"):
                    child = val.get("count") or str(val["sum"]).split(".")[0]
                    qs = self._children(child, val.get("via"), obj)
                    if val.get("where_ast"):
                        qs = qs.filter(zx.to_q(val["where_ast"], qs.model, self._zas_ctx))
                    if val.get("count"):
                        value = qs.count()
                    else:
                        fld = str(val["sum"]).split(".", 1)[1]
                        value = _num(qs.aggregate(v=Sum(fld))["v"]) or 0
                elif val.get("field"):
                    value = _num(zr.value_of(obj, val["field"]))
                elif val.get("text"):
                    computed = True
                    value = zs.call_hook(H["module"], f"{self.zas_view}__stat__{i + 1}", self.request, obj)
                    value = _num(value)
            except Exception:
                logger.exception("zas: stat %s[%s] failed", self.zas_view, i)
            tone = s.get("tone")
            if isinstance(tone, dict):
                tone = self._tone_rule(tone, value)
            out.append({"key": f"s{i + 1}", "label": s.get("label"), "value": value, "format": s.get("format") or "number",
                        "tone": tone, "icon": s.get("icon"), "tab": s.get("link_to_tab"), "computed": computed, "order": i})
        return out

    @staticmethod
    def _tone_rule(rule, value):
        import re
        m = re.match(r"^\s*(==|!=|>=|<=|>|<)\s*(-?[\d.]+)\s*$", str(rule.get("when", "")))
        if not m or value is None:
            return rule.get("else")
        a, op, b = float(value), m.group(1), float(m.group(2))
        hit = {"==": a == b, "!=": a != b, ">": a > b, ">=": a >= b, "<": a < b, "<=": a <= b}[op]
        return rule.get("is") if hit else rule.get("else")

    def _fields_panel(self, H, obj, sec, key, order):
        items = []
        for it in sec.get("fields") or []:
            k = it if isinstance(it, str) else next(iter(it))
            opts = {} if isinstance(it, str) else (it.get(k) or {})
            if opts.get("roles") and self._zas_role not in opts["roles"]:
                continue
            items.append(zr.field_value(H, obj, k, label=opts.get("label")))
        ei = sec.get("editable_inline")
        editable = bool(ei) and self._ok(ei, obj) and access.can(H["code"], "edit", self._zas_role) is not False
        return {"key": key, "type": "fields", "title": sec.get("title"), "columns": sec.get("columns"),
                "fields": items, "editable": editable, "order": order}

    def _mini_table(self, H, obj, sec):
        T = zs.entity(sec["entity"])
        qs = self._children(sec["entity"], sec.get("via"), obj)
        if sec.get("where_ast"):
            qs = qs.filter(zx.to_q(sec["where_ast"], qs.model, self._zas_ctx))
        total = qs.count()
        sort = sec.get("sort") or "-created_at"
        rows = []
        for rec in qs.order_by(sort)[: int(sec.get("limit") or 5)]:
            cells = {}
            for c in sec.get("columns") or []:
                k = c if isinstance(c, str) else next(iter(c))
                cells[k] = zr.field_value(T, rec, k)
            rows.append({"uuid": str(rec.object_uuid), "cells": cells})
        return {"entity": sec["entity"], "rows": rows, "total": total, "see_all_tab": sec.get("see_all_tab")}

    def _zas_tabs(self, V, H, obj):
        tabs, panels, minis = [], {}, {}
        for ti, t in enumerate(V.get("tabs") or []):
            if not self._ok(t, obj):
                continue
            entry = {"code": t["code"], "count": None, "count_tone": None, "order": ti}
            if t.get("type") == "related_table":
                child = t["entity"]
                if zs.entity(child).get("access") and not access.can(child, "view", self._zas_role):
                    continue
                cb = t.get("count_badge")
                if cb:
                    qs = self._children(child, t.get("via"), obj)
                    if isinstance(cb, dict) and cb.get("ast"):
                        qs = qs.filter(zx.to_q(cb["ast"], qs.model, self._zas_ctx))
                    n = qs.count()
                    if isinstance(cb, dict) and not n:
                        n = None  # a "pending" badge hides at zero
                    entry["count"] = n
                    entry["count_tone"] = cb.get("tone") if isinstance(cb, dict) else None
                add = t.get("add")
                entry["can_add"] = bool(add) and access.can(child, "add", self._zas_role) is not False and self._ok(add, obj) \
                    and (not ((zs.entity(child).get("form") or {}).get("create") or {}).get("roles")
                         or self._zas_role in zs.entity(child)["form"]["create"]["roles"])
            if t.get("type") in ("summary", "fields"):
                secs = t.get("sections") or []
                if t.get("type") == "fields" and not secs:
                    secs = [{"type": "fields", "fields": t.get("fields") or [f["key"] for f in H["fields"]], "columns": t.get("columns", 2)}]
                plist = []
                for j, sec in enumerate(secs):
                    if not self._ok(sec, obj):
                        continue
                    key = f"{t['code']}_{j + 1}"
                    st = sec.get("type", "fields")
                    if st == "fields":
                        plist.append(self._fields_panel(H, obj, sec, key, j))
                    elif st == "mini_table":
                        minis[key] = self._mini_table(H, obj, sec)
                        plist.append({"key": key, "type": "mini_table", "title": sec.get("title"), "order": j})
                    elif st == "custom":
                        plist.append({"key": key, "type": "custom", "title": sec.get("title"), "order": j})
                    elif st == "timeline":
                        plist.append({"key": key, "type": "timeline", "title": sec.get("title") or "Activity", "order": j})
                panels[t["code"]] = plist
            tabs.append(entry)
        side = []
        for i, sec in enumerate(V.get("sidebar") or []):
            if not self._ok(sec, obj):
                continue
            key = f"sidebar_{i + 1}"
            st = sec.get("type", "fields")
            if st == "fields":
                side.append(self._fields_panel(H, obj, sec, key, i))
            elif st == "mini_table":
                minis[key] = self._mini_table(H, obj, sec)
                side.append({"key": key, "type": "mini_table", "title": sec.get("title"), "order": i})
            else:
                side.append({"key": key, "type": st, "title": sec.get("title"), "order": i})
        panels["sidebar"] = side
        return tabs, panels, minis

    def _zas_actions(self, V, H, obj, status):
        req, role = self.request, self._zas_role
        acts = (V.get("header") or {}).get("actions") or {"transitions": True, "tags": True}
        out = {"transitions": [], "tags": [], "buttons": [], "row_actions": []}
        wf_obj = None
        if H.get("workflow") and getattr(self, "crud_view_instance", None) is not None:
            try:
                wf_obj = self.crud_view_instance.get_workflow_obj(object_instance=obj)
            except Exception:
                logger.exception("zas: workflow object for %s", H["code"])
        trs, tgs = workflow_actions(H, wf_obj, status, role)
        if acts.get("transitions", True) is not False:
            out["transitions"] = trs
        if acts.get("tags", True) is not False:
            out["tags"] = tgs
        table = self.table_obj
        try:
            out["row_actions"] = [r["key"] for r in table.get_row_actions(req, obj)]
        except Exception:
            logger.exception("zas: row actions for %s", H["code"])
        for i, b in enumerate(acts.get("buttons") or []):
            if not self._ok(b, obj):
                continue
            item = {"key": b.get("key") or f"b{i + 1}", "label": b.get("label"), "icon": b.get("icon"), "order": i}
            if b.get("row_action"):
                if b["row_action"] not in out["row_actions"]:
                    continue
                ra = next((a for a in H["table"]["row_actions"] if a["key"] == b["row_action"]), {})
                item.update(type="row_action", row_action=b["row_action"], label=b.get("label") or ra.get("label"),
                            action_type=ra.get("type"), confirm=ra.get("confirm"))
            elif b.get("type") == "edit":
                if "edit" not in out["row_actions"]:
                    continue
                item.update(type="edit")
            elif b.get("type") == "create_related":
                T = b.get("entity")
                if zs.entity(T).get("access") and not access.can(T, "add", role):
                    continue
                prefill = {k: (str(obj.object_uuid) if v == "hero" else v) for k, v in (b.get("prefill") or {}).items()}
                param = next((p for p, info in (zs.entity(T).get("parents") or {}).items()
                              if info["hero"] == H["code"] and info.get("fk") in prefill), None)
                item.update(type="create_related", entity=T, prefill=prefill, param=param)
            elif b.get("type") == "navigate":
                item.update(type="navigate", to=b.get("to"))
            else:
                item.update(type=b.get("type") or "row_action")
            out["buttons"].append(item)
        return out

    def _zas_custom(self, V, H, obj):
        out = {}
        for h in zs.holes_for(f"detail_views.{self.zas_view}."):
            if h["kind"] not in ("custom_panel", "custom_tab"):
                continue
            key = h["function"].split("__custom__", 1)[-1]
            try:
                out[key] = zs.call_hook(H["module"], h["function"], self.request, obj, default=None)
            except Exception:
                logger.exception("zas: custom data hook %s failed", h["function"])
                out[key] = {"error": True}
        return out

    # ---------- timeline ----------
    def zas_timeline(self, obj, tab_code=None):
        V = zs.view(self.zas_view)
        H = zs.entity(V["hero"])
        sources = None
        for t in V.get("tabs") or []:
            if t.get("type") == "timeline" and (tab_code is None or t["code"] == tab_code):
                sources = t.get("sources")
                break
        if not sources:
            for sec in V.get("sidebar") or []:
                if sec.get("type") == "timeline":
                    sources = sec.get("sources")
        sources = sources or [{"entity": H["code"]}]
        events = []
        for s in sources:
            code = s["entity"]
            evs = set(s.get("events") or ["created", "updated", "transition", "tag"])
            if code == H["code"] and not s.get("via"):
                recs = [obj]
            else:
                recs = list(self._children(code, s.get("via"), obj).order_by("-modified_at")[:100])
            E = zs.entity(code)
            for rec in recs:
                events += self._events_for(E, rec, evs, is_self=rec is obj)
        events.sort(key=lambda e: e["t"] or "", reverse=True)
        return {"events": events[:200]}

    def _events_for(self, E, rec, evs, is_self):
        out = []
        label = zr.field_value(E, rec, E["display"])["display"] if E["display"] != "id" else f"#{rec.pk}"
        base = {"entity": E["code"], "entity_name": E["name"], "uuid": str(rec.object_uuid), "record": label, "self": is_self}
        wf = E.get("workflow") or {}
        smap = {s["code"]: s for s in wf.get("statuses", [])}
        tmap = {t["code"]: t for t in wf.get("tags", [])}
        trs = {e["name"]: t for t in wf.get("transitions", []) for e in t.get("engine", [])}
        if wf and ({"transition", "tag"} & evs):
            from ...packages.workflow.base.models import WorkflowTransaction
            for t in WorkflowTransaction.objects.filter(obj_uuid=rec.object_uuid).order_by("-id")[:100]:
                actor = getattr(t.actor, "name", None) if t.actor_id else None
                ts = t.created_at.isoformat() if t.created_at else None
                fd = (t.data or {}).get("form_data") or {}
                if t.transition_type == "status" and "transition" in evs and t.from_state != "on_create":
                    st = trs.get(t.transition_name) or {}
                    out.append({**base, "kind": "transition", "t": ts, "actor": actor, "text": st.get("label") or t.transition_name,
                                "from": {"label": (smap.get(t.from_state) or {}).get("label", t.from_state), "tone": (smap.get(t.from_state) or {}).get("color")},
                                "to": {"label": (smap.get(t.to_state) or {}).get("label", t.to_state), "tone": (smap.get(t.to_state) or {}).get("color")},
                                "note": "; ".join(f"{k.replace('_', ' ')}: {v}" for k, v in fd.items() if v not in (None, ""))[:400] or None})
                elif t.transition_type == "tag" and "tag" in evs:
                    tg = tmap.get(t.transition_name) or {}
                    out.append({**base, "kind": "tag", "t": ts, "actor": actor, "on": t.to_state == "enabled",
                                "tag": {"label": tg.get("label", t.transition_name), "tone": tg.get("color")}})
        if {"created", "updated"} & evs:
            try:
                from zango.apps.auditlogs.models import LogEntry
                for le in LogEntry.objects.get_for_object(rec).order_by("-timestamp")[:100]:
                    kind = {0: "created", 1: "updated", 2: "deleted"}.get(getattr(le, "action", None), "updated")
                    if kind not in evs:
                        continue
                    changes = getattr(le, "changes_dict", None)
                    if changes is None:
                        try:
                            changes = json.loads(le.changes) if isinstance(le.changes, str) else (le.changes or {})
                        except Exception:
                            changes = {}
                    labels = {f["key"]: f["label"] for f in E["fields"]}
                    ch = {labels.get(k, k): _readable_change(E, k, v) for k, v in (changes or {}).items()
                          if k not in ("modified_at", "modified_by", "created_at", "created_by", "object_uuid", "id")}
                    if kind == "updated" and not ch:
                        continue
                    actor = getattr(getattr(le, "actor", None), "name", None)
                    out.append({**base, "kind": kind, "t": le.timestamp.isoformat() if le.timestamp else None,
                                "actor": actor, "changes": ch if kind == "updated" else None})
            except Exception:
                logger.exception("zas: audit log read failed for %s", E["code"])
                if "created" in evs:
                    out.append({**base, "kind": "created", "t": rec.created_at.isoformat() if rec.created_at else None,
                                "actor": getattr(rec.created_by, "name", None) if getattr(rec, "created_by_id", None) else None})
        return out


# ───────────── shared by the 360 header and the record drawer (any entity) ─────────────

def workflow_actions(E, wf_obj, status, role):
    """(transitions, tags) the role may see on this record, each with `allowed` and the spec's
    `condition_msg` as `blocked_reason` (a failing condition shows disabled, not hidden)."""
    trs, tgs = [], []
    if wf_obj is None or not E.get("workflow"):
        return trs, tgs
    for t in E["workflow"]["transitions"]:
        if t.get("system") or status not in t["from"]:
            continue
        if t.get("roles") and role not in t["roles"]:
            continue
        engine = next(e["name"] for e in t["engine"] if e["from"] == status)
        try:
            allowed = wf_obj.is_transition_allowed(engine, current_status=status)
        except Exception:
            logger.exception("zas: condition %s failed", engine)
            allowed = False
        trs.append({
            "name": t["name"], "engine_name": engine, "label": t["label"], "primary": bool(t.get("primary")),
            "tone": t.get("tone"), "confirm": t.get("confirm"), "has_form": bool(t.get("form")),
            "allowed": bool(allowed), "blocked_reason": None if allowed else (t.get("condition_msg") or "Not available right now."),
        })
    try:
        details = {d["name"]: d for d in wf_obj.get_tags_details()}
    except Exception:
        details = {}
    for tg in E["workflow"].get("tags", []):
        if tg.get("system"):
            continue
        d = details.get(tg["code"], {})
        state = d.get("state", "disabled")
        side = tg.get("enable") if state == "disabled" else tg.get("disable")
        if not side or (side.get("roles") and role not in side["roles"]):
            continue
        allowed = d.get("is_enable_allowed") if state == "disabled" else d.get("is_disable_allowed")
        tgs.append({"code": tg["code"], "label": tg["label"], "tone": tg.get("color"), "state": state,
                    "allowed": bool(allowed), "has_form": bool(side.get("form")), "confirm": side.get("confirm"),
                    "blocked_reason": None if allowed else (side.get("condition_msg") or "Not available right now.")})
    return trs, tgs


def record_payload(crud_view, request, entity_code, obj):
    """Everything the record drawer shows for one row of any entity (contracts §8b):
    display fields, status/tags, allowed transitions and tag toggles, row actions, activity."""
    E = zs.entity(entity_code)
    role = access.role_name(request)
    wf = E.get("workflow") or {}
    status = zx.current_status(obj) if wf else None
    tags = sorted(zx.current_tags(obj)) if wf else []
    smap = {x["code"]: x for x in wf.get("statuses", [])}
    tmap = {x["code"]: x for x in wf.get("tags", [])}
    wf_obj = None
    if wf:
        try:
            wf_obj = crud_view.get_workflow_obj(object_instance=obj)
        except Exception:
            logger.exception("zas: workflow object for %s", entity_code)
    trs, tgs = workflow_actions(E, wf_obj, status, role)
    row_actions = []
    try:
        table = crud_view.get_table_obj()
        spec_acts = {a["key"]: a for a in (E.get("table") or {}).get("row_actions", [])}
        for r in table.get_row_actions(request, obj):
            sa = spec_acts.get(r["key"], {})
            row_actions.append({"key": r["key"], "label": r.get("name") or sa.get("label") or r["key"],
                                "type": r.get("type"), "spec_type": sa.get("type") or ("edit" if r["key"] == "edit" else None),
                                "confirm": r.get("confirmation_message") or sa.get("confirm")})
    except Exception:
        logger.exception("zas: row actions for %s", entity_code)
    events = []
    try:
        events = sorted(events_for(E, obj, {"created", "updated", "transition", "tag"}, True),
                        key=lambda e: e["t"] or "", reverse=True)[:50]
    except Exception:
        logger.exception("zas: activity for %s", entity_code)
    return {
        "entity": entity_code, "access": "ok",
        "record": {
            "uuid": str(obj.object_uuid), "pk": obj.pk, "status": status,
            "status_label": (smap.get(status) or {}).get("label"), "status_tone": (smap.get(status) or {}).get("color"),
            "tags": [{"code": c, "label": (tmap.get(c) or {}).get("label", c), "tone": (tmap.get(c) or {}).get("color")} for c in tags],
            "display": zr.field_value(E, obj, E["display"])["display"] if E["display"] != "id" else f"#{obj.pk}",
        },
        "fields": [zr.field_value(E, obj, f["key"]) for f in E["fields"]],
        "transitions": trs, "tags": tgs, "row_actions": row_actions, "events": events,
    }


def events_for(E, rec, evs, is_self):
    return ZasDetail._events_for(None, E, rec, evs, is_self)


def _readable_change(E, key, pair):
    """Audit-log change [old, new] with link ids and choice ids shown the way the UI shows them."""
    f = next((x for x in E["fields"] if x["key"] == key), None)
    if not f or not isinstance(pair, (list, tuple)):
        return pair

    def one(v):
        if v in (None, "None", ""):
            return None
        try:
            if f["type"] == "link":
                if f.get("to") == "app_user":
                    from zango.apps.appauth.models import AppUserModel
                    u = AppUserModel.objects.filter(pk=v).first()
                    return getattr(u, "name", None) or v
                rec = zs.model(f["to"]).objects.filter(pk=v).first()
                if rec is not None:
                    T = zs.entity(f["to"])
                    attr = f.get("display") or T.get("display")
                    return str(getattr(rec, attr, None) or rec)
            if f["type"] in ("choice", "multi_choice"):
                return next((c["label"] for c in f.get("choices") or [] if str(c["id"]) == str(v)), v)
        except Exception:
            return v
        return v
    return [one(x) for x in pair]
