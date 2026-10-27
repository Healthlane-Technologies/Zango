"""
Mixins the generated classes add. Each reads its configuration from spec.json
through `zas_entity`, so generated code stays declarative.

    class VendorTable(ZasTableMixin, ModelTable):         zas_entity = "vendor"
    class VendorForm(ZasFormMixin, BaseForm):             zas_entity = "vendor"; zas_form = "create"
    class VendorUpdateBankActionForm(ZasActionFormMixin, BaseForm): ...
    class VendorApproveForm(ZasActionFormMixin, BaseSimpleForm): ...
    class VendorWorkflow(ZasWorkflowMixin, WorkflowBase): zas_entity = "vendor"

Mixins go FIRST in the bases so their methods wrap the package's.
"""

import copy
import json
import logging
import re
from types import SimpleNamespace

from django import forms
from django.core.exceptions import PermissionDenied

from . import access
from . import app_user
from . import dupes
from . import expr as zx
from . import spec as zs

logger = logging.getLogger(__name__)


def _hook(entity_code, fn):
    return zs.hook(zs.entity(entity_code)["module"], fn)


def _cell_text(E, obj, path):
    """One part of a cell's second line: the field's display text, formatted like a cell."""
    from . import records as zr

    v = zr.field_value(E, obj, path)
    if v["display"] is None:
        return ""
    if v["type"] in ("money", "number", "percent", "days", "date", "datetime"):
        return zr.display(v["value"], v["type"]) or v["display"]
    return v["display"]


def _cell_icon(obj, icon):
    """`icon` normalised by spec_check: {by, map, default}."""
    if not icon:
        return None
    if not icon.get("by"):
        return icon.get("default")
    from . import records as zr

    raw = zr.value_of(obj, icon["by"])
    return (icon.get("map") or {}).get(str(raw), icon.get("default"))


class _FormRecord:
    """Lets expressions read live form values (and fall back to the instance)."""

    def __init__(self, values, instance=None):
        self._v, self._i = values or {}, instance

    def __getattr__(self, name):
        if name.startswith("_"):
            raise AttributeError(name)
        if name in self._v:
            return self._v[name]
        return getattr(self._i, name, None) if self._i is not None else None


# ───────────────────────────── tables ─────────────────────────────

class ZasTableMixin:
    """Role row scoping, the 360 parent filter, quick filters, default sort, and
    the row-action gates/handlers named in the spec (contracts §3-§6)."""

    zas_entity = None

    def _zas_request(self):
        req = getattr(self, "request", None)
        if req is None and getattr(self, "crud_view_instance", None) is not None:
            req = getattr(self.crud_view_instance, "request", None)
        return req

    def get_table_data_queryset(self):
        qs = super().get_table_data_queryset()
        req = self._zas_request()
        if req is None:
            return qs
        qs = access.scope_queryset(self.zas_entity, qs, req)
        if access.request_action(req) in access.TABLE_ACTIONS:
            qs = access.parent_filter(self.zas_entity, qs, req)
            qs = self._zas_quick_filter(qs, req)
            sort = (zs.entity(self.zas_entity).get("table") or {}).get("default_sort")
            if sort and not req.GET.get("order[0][column]"):
                qs = qs.order_by(sort)
        return qs

    def get_table_metadata(self):
        """Adds `zas`: the viewer's role and the quick filters that role may use (React chips)."""
        meta = super().get_table_metadata()
        try:
            req = self._zas_request()
            role = access.role_name(req)
            qfs = (zs.entity(self.zas_entity).get("table") or {}).get("quick_filters", [])
            meta["zas"] = {
                "entity": self.zas_entity, "role": role,
                "quick_filters": [{"key": q["key"], "label": q["label"], "default": bool(q.get("default"))}
                                  for q in qfs if not q.get("roles") or role in q["roles"]],
                "filter_options": self._zas_filter_options(req),
            }
        except Exception:
            logger.exception("zas: table metadata for %s", self.zas_entity)
        return meta

    def post_process_data(self, data):
        """Rows as crud serializes them, plus `zas` for the React table (contracts §8b):
        `links` = object_uuid of each linked record shown in a column (so a `link_to` cell can
        open the linked 360) or that is a parent link (a `<view>#<tab>` row click opens the parent),
        `status` / `tags` = codes (the crud cells are HTML labels)."""
        rows = super().post_process_data(data)
        try:
            E = zs.entity(self.zas_entity)
            cols = set(self.get_columns()) | {p.get("fk") for p in (E.get("parents") or {}).values() if p.get("fk")}
            fks = [f for f in data[0]["obj"]._meta.fields if f.is_relation and f.name in cols] if data else []
            has_wf = bool((E.get("workflow") or {}).get("statuses"))
            hls = [(c["key"], c["highlight"]) for c in (E.get("table") or {}).get("columns", [])
                   if (c.get("highlight") or {}).get("ast")]
            cells = [c for c in (E.get("table") or {}).get("columns", []) if c.get("secondary") or c.get("icon")]
            ctx = access.expr_ctx(self._zas_request())
            for row, d in zip(rows, data):
                obj = d["obj"]
                links = {}
                for f in fks:
                    rel = getattr(obj, f.name, None)
                    if rel is not None and getattr(rel, "object_uuid", None):
                        links[f.name] = str(rel.object_uuid)
                z = {"links": links}
                if has_wf:
                    z["status"] = zx.current_status(obj)
                    z["tags"] = sorted(zx.current_tags(obj))
                hl = {}
                for key, h in hls:  # table.columns[].highlight: {when, tone} per cell
                    try:
                        if zx.evaluate(h["ast"], obj, ctx):
                            hl[key] = h.get("tone") or "red"
                    except Exception:
                        logger.exception("zas: highlight %s.%s", self.zas_entity, key)
                if hl:
                    z["hl"] = hl
                for c in cells:  # table.columns[].secondary / icon: the cell's second line and icon
                    try:
                        sub = [t for t in (_cell_text(E, obj, p) for p in c.get("secondary") or []) if t]
                        if sub:
                            z.setdefault("sub", {})[c["key"]] = " · ".join(sub)
                        icon = _cell_icon(obj, c.get("icon"))
                        if icon:
                            z.setdefault("icon", {})[c["key"]] = icon
                    except Exception:
                        logger.exception("zas: cell %s.%s", self.zas_entity, c["key"])
                row["zas"] = z
        except Exception:
            logger.exception("zas: row extras for %s", self.zas_entity)
        return rows

    def get_sorted_objects(self, objects, sort_col, sort_type):
        """Server-side sort for a column header click (crud sends order[0][column]/[dir]).
        crud 1.0.17's own version inverts the direction ("asc" → "-col", a leftover of the
        DataTables frontend) and sorts links by pk; here asc is ascending, a link sorts by
        the column's display attribute, and non-field columns (status, tags, computed) keep
        the current order instead of raising."""
        custom = getattr(type(self), f"{sort_col}_get_sorted_objects", None)
        if custom:
            return custom(self, objects, sort_type)
        try:
            field = objects.model._meta.get_field(sort_col)
        except Exception:
            return objects
        path = sort_col
        if getattr(field, "is_relation", False):
            meta = next((c for c in self.get_table_metadata().get("columns", []) if c.get("name") == sort_col), {})
            attr = meta.get("related_object_attribute")
            if attr:
                path = f"{sort_col}__{attr}"
        prefix = "-" if str(sort_type).lower() == "desc" else ""
        return objects.order_by(f"{prefix}{path}", f"{prefix}pk")

    def _zas_filter_options(self, req):
        """Options for a filterable link column: the linked records' display values among the rows
        this role can see (as the Studio preview does). Read from this entity, never from the
        linked entity's endpoint, which the role may not be allowed to open."""
        out = {}
        if req is None or access.request_action(req) != "get_table_metadata":
            return out
        E = zs.entity(self.zas_entity)
        try:
            qs = access.scope_queryset(self.zas_entity, self.Meta.model.objects.all(), req)
            qs = access.parent_filter(self.zas_entity, qs, req)  # a 360 tab: only this parent's rows
            for c in (E.get("table") or {}).get("columns", []):
                f = next((x for x in E["fields"] if x["key"] == c["key"]), None)
                if not c.get("filterable") or not f or f["type"] != "link" or f.get("to") == "app_user":
                    continue
                attr = c.get("display") or f.get("display") or zs.entity(f["to"]).get("display")
                vals = qs.exclude(**{f"{c['key']}__isnull": True}).values_list(f"{c['key']}__{attr}", flat=True).distinct()
                out[c["key"]] = sorted({str(v) for v in vals[:500] if v not in (None, "")})
        except Exception:
            logger.exception("zas: filter options for %s", self.zas_entity)
        return out

    def _zas_quick_filter(self, qs, req):
        key = req.GET.get("qf")
        if not key:
            return qs
        role = access.role_name(req)
        for q in (zs.entity(self.zas_entity).get("table") or {}).get("quick_filters", []):
            if q["key"] == key and (not q.get("roles") or role in q["roles"]) and q.get("ast"):
                return qs.filter(zx.to_q(q["ast"], qs.model, access.expr_ctx(req)))
        return qs

    # ---- row actions: can_perform_row_action_<key> / process_row_action_<key> ----
    def _zas_action(self, key):
        for a in (zs.entity(self.zas_entity).get("table") or {}).get("row_actions", []):
            if a["key"] == key:
                return a
        if key == "delete":
            return {"key": "delete", "type": "delete"}
        if key == "edit":
            # access grants edit but the spec table lists no edit row action: the generated
            # table adds one, and it must still pass editable_in / roles / row scope
            E = zs.entity(self.zas_entity)
            if any("edit" in (a.get("actions") or []) for a in (E.get("access") or {}).values()) or \
                    (E.get("form") or {}).get("edit"):
                return {"key": "edit", "type": "edit", "label": "Edit"}
        return None

    def __getattr__(self, name):
        # hasattr() only swallows AttributeError: never let a lookup raise anything else
        if name.startswith("_") or not type(self).__dict__.get("zas_entity", getattr(type(self), "zas_entity", None)):
            raise AttributeError(name)
        try:
            known = name.startswith(("can_perform_row_action_", "process_row_action_")) and \
                self._zas_action(name.split("row_action_", 1)[1]) is not None
        except Exception:
            known = False
        if not known:
            raise AttributeError(name)
        if name.startswith("can_perform_row_action_"):
            key = name[len("can_perform_row_action_"):]
            if self._zas_action(key) is not None:
                return lambda request, obj: self.zas_can_perform(key, request, obj)
        if name.startswith("process_row_action_"):
            key = name[len("process_row_action_"):]
            a = self._zas_action(key)
            if a is not None and a["type"] not in ("edit",):
                return lambda request, obj: self.zas_process(key, request, obj)
        raise AttributeError(name)

    def zas_can_perform(self, key, request, obj):
        E = zs.entity(self.zas_entity)
        a = self._zas_action(key)
        ctx = access.expr_ctx(request)
        role = access.role_name(request)
        # rows listed by get_table_data are already scoped; the action endpoints are not
        if access.request_action(request) not in access.TABLE_ACTIONS and not access.in_scope(self.zas_entity, obj, request):
            return False
        if a["type"] in ("edit",) or key == "edit":
            if E.get("access") and not access.can(self.zas_entity, "edit", role):
                return False
            ed = (E.get("form") or {}).get("edit") or {}
            if ed.get("roles") and role not in ed["roles"]:
                return False
            if ed.get("editable_in") and zx.current_status(obj) not in ed["editable_in"]:
                return False
        if a["type"] == "delete" and E.get("access") and not access.can(self.zas_entity, "delete", role):
            return False
        if a.get("show_when_ast") and not zx.evaluate(a["show_when_ast"], obj, ctx):
            return False
        return True

    def zas_process(self, key, request, obj):
        a = self._zas_action(key)
        if not self.zas_can_perform(key, request, obj) or (a.get("roles") and access.role_name(request) not in a["roles"]):
            return False, {"message": "You can't do this on this record."}
        if a["type"] == "delete":
            obj.delete()
            return True, {"message": "Deleted."}
        if a["type"] == "navigate":
            return True, {"message": "", "navigate": a.get("to")}
        data = getattr(request, "_zas_form_data", None) or {k: v for k, v in request.POST.items()}
        fn = f"{self.zas_entity}__action__{key}"
        h = _hook(self.zas_entity, fn)
        if h is None:
            return False, {"message": f"{a['label']} is not implemented yet ({fn})."}
        res = h(request, obj, data) or {}
        if hasattr(res, "status_code"):  # an HttpResponse: hand back a URL instead
            return False, {"message": f"{fn} must return a dict (e.g. {{'url': ...}}), not a response."}
        res.setdefault("message", a.get("success_message") or f"{a['label']} done.")
        return True, res


# ───────────────────────────── create / edit forms ─────────────────────────────

class ZasFormMixin:
    """Spec behaviour for the entity's create/edit BaseForm:
    parent preset, show_when (server-side, re-evaluated on sync), limit_choices,
    readonly_when, validation rules, duplicate check, on_create, app_user."""

    zas_entity = None
    zas_form = "create"  # or "edit"
    CONFIRM = "zas_confirm"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._zas_req = getattr(getattr(self, "crud_view_instance", None), "request", None)
        E = self._E = zs.entity(self.zas_entity)
        self._zas_removed = set()
        inst = getattr(self, "instance", None)
        self._zas_is_edit = bool(inst is not None and getattr(inst, "pk", None))
        values = self._zas_values()
        ctx = access.expr_ctx(self._zas_req, form=values)
        rec = _FormRecord(values, inst if self._zas_is_edit else None)

        # 1. parent preset (360 tab): preset + hide the FK, on a COPY of the ModelField
        if self._zas_req is not None and not self._zas_is_edit:
            for param, info in (E.get("parents") or {}).items():
                fk = info.get("fk")
                raw = self._zas_req.GET.get(param)
                if not fk or raw is None or fk not in self.fields:
                    continue
                uid = access.clean_uuid(raw)
                parent = zs.model(info["hero"]).objects.filter(object_uuid=uid).first() if uid else None
                if parent is None:
                    continue
                self.fields[fk].initial = parent.pk
                self.initial[fk] = parent.pk
                self._zas_set_prop(fk, hidden=True)

        # 2. show_when / readonly_when / limit_choices
        for sec in E["form"].get(f"{self.zas_form}_resolved") or E["form"].get("create_resolved") or []:
            for it in sec["fields"]:
                k = it["key"]
                if it.get("show_when_ast") and k in self.fields and not zx.evaluate(it["show_when_ast"], rec, ctx):
                    del self.fields[k]
                    self._zas_removed.add(k)
        if self._zas_is_edit:
            ed = E["form"].get("edit") or {}
            for rw in ed.get("readonly_when") or []:
                if rw.get("ast") and zx.evaluate(rw["ast"], inst, ctx):
                    for k in rw.get("fields") or []:
                        if k in self.fields:
                            self.fields[k].disabled = True
                            self._zas_set_prop(k, readonly=True)
        for f in E["fields"]:
            if f.get("limit_choices") and isinstance(f["limit_choices"], dict) and f["key"] in self.fields:
                fld = self.fields[f["key"]]
                if hasattr(fld, "queryset"):
                    try:
                        fld.queryset = fld.queryset.filter(zx.to_q(f["limit_choices"], fld.queryset.model, ctx))
                    except Exception:
                        logger.exception("zas: limit_choices failed on %s.%s", self.zas_entity, f["key"])

        # 2b. a link only offers records the viewer's role may see (the FK queryset is otherwise
        #     unscoped, so a scoped role could post a record outside its rows)
        if self._zas_req is not None:
            for f in E["fields"]:
                if f["type"] != "link" or f["to"] == "app_user" or f["key"] not in self.fields:
                    continue
                fld = self.fields[f["key"]]
                if hasattr(fld, "queryset") and zs.entity(f["to"]).get("access"):
                    try:
                        fld.queryset = access.scope_queryset(f["to"], fld.queryset, self._zas_req)
                    except Exception:
                        logger.exception("zas: scoping link %s.%s failed", self.zas_entity, f["key"])

        # 3. confirm checkbox when the entity has warn-level rules
        if self._zas_has_warnings() and self.CONFIRM not in self.fields:
            from ...packages.crud.form_fields import ModelField
            self.fields[self.CONFIRM] = forms.BooleanField(required=False, label="Continue even if a warning applies")
            self.declared_fields[self.CONFIRM] = ModelField(
                label="Continue even if a warning applies",
                description="Tick this after reviewing a possible duplicate or warning.")

    # values: bound data (submit and sync) or instance/initial
    def _zas_values(self):
        out = {}
        inst = getattr(self, "instance", None)
        for f in self._E["fields"]:
            k = f["key"]
            if self.is_bound and k in self.data:
                v = self.data.get(k)
                if f["type"] == "link" and v not in (None, ""):
                    try:
                        v = zs.model(f["to"]).objects.filter(pk=v).first() if f["to"] != "app_user" else v
                    except Exception:
                        pass
                out[k] = v
            elif inst is not None and getattr(inst, "pk", None):
                out[k] = getattr(inst, k, None)
            else:
                out[k] = self.initial.get(k, f.get("default"))
        return out

    def _zas_set_prop(self, name, **props):
        df = self.declared_fields.get(name)
        if df is None:
            return
        df = copy.copy(df)  # never mutate the class-level ModelField (it would leak to other requests)
        df.properties = {**getattr(df, "properties", {}), **props}
        self.declared_fields[name] = df

    def _zas_has_warnings(self):
        v = self._E.get("validation") or {}
        return any(r.get("on_fail") == "warn" for r in v.get("rules") or []) or \
            any(r.get("on_match") == "warn" for r in (v.get("duplicate_check") or {}).get("rules") or [])

    def convert_model_form_to_json_schema(self):
        schema, ui = super().convert_model_form_to_json_schema()
        fc = self._E["form"].get(self.zas_form) or {}
        title = fc.get("title") or (f"Edit {self._E['name']}" if self._zas_is_edit else f"Add {self._E['name']}")
        schema["title"] = title
        props = set(schema.get("properties", {}))
        order = ui.get("ui:order")
        if order:
            ui["ui:order"] = self._zas_order(order, props)
        return schema, ui

    @staticmethod
    def _zas_order(order, props):
        """Drop removed fields from ui:order (rjsf rejects unknown names); keep rows."""
        out = []
        for row in order:
            if isinstance(row, (list, tuple)):
                r = [x for x in row if x in props]
                if r:
                    out.append(r)
            elif row in props or row == "*":
                out.append(row)
        flat = {x for r in out for x in (r if isinstance(r, list) else [r])}
        rest = [p for p in props if p not in flat]
        if rest:
            out.append(rest if isinstance(order[0], (list, tuple)) else "*")
        return out

    def clean(self):
        cleaned = super().clean()
        if cleaned is None:
            cleaned = self.cleaned_data
        E = self._E
        req = self._zas_req
        confirmed = bool(cleaned.get(self.CONFIRM))
        rec = _FormRecord(cleaned, self.instance if self._zas_is_edit else None)
        ctx = access.expr_ctx(req, form=cleaned)
        warnings = []
        v = E.get("validation") or {}
        for i, rule in enumerate(v.get("rules") or []):
            if rule.get("when_ast") and not zx.evaluate(rule["when_ast"], rec, ctx):
                continue
            ok = True
            if rule.get("require"):
                missing = [k for k in rule["require"] if cleaned.get(k) in (None, "", [])]
                if missing:
                    ok = False
                    for k in missing:
                        if k in self.fields:
                            self.add_error(k, rule.get("message") or "This field is required.")
                    continue
            if rule.get("require_ast"):
                ok = zx.evaluate(rule["require_ast"], rec, ctx)
            if rule.get("text"):
                h = _hook(self.zas_entity, f"{self.zas_entity}__validate__{i + 1}")
                if h is not None:
                    ok = bool(h(self, cleaned))
            if not ok:
                msg = rule.get("message") or "This record is not valid."
                if rule.get("on_fail") == "warn":
                    warnings.append(msg)
                else:
                    raise forms.ValidationError(msg)
        dc = v.get("duplicate_check") or {}
        if dc.get("rules"):
            Model = self._meta.model
            pk = self.instance.pk if self._zas_is_edit else None
            for rule in dc["rules"]:
                vals = {m: (cleaned.get(m) if "." not in m else zx._get_path(rec, m, ctx)) for m in rule.get("match", [])}
                hit = dupes.find(self.zas_entity, Model, vals, rule, dc.get("scope_ast"), pk, req)
                if hit is not None:
                    msg = rule.get("message") or "A matching record already exists."
                    if rule.get("on_match") == "warn":
                        warnings.append(msg)
                    else:
                        first = rule["match"][0].split(".")[0]
                        if first in self.fields:
                            self.add_error(first, msg)
                        else:
                            raise forms.ValidationError(msg)
        if warnings and not confirmed:
            if self.CONFIRM in self.fields:
                self.add_error(self.CONFIRM, " ".join(warnings) + " Tick the box to continue anyway.")
            else:
                raise forms.ValidationError(" ".join(warnings))
        return cleaned

    def save(self, commit=True):
        creating = not self._zas_is_edit
        obj = super().save(commit=commit)
        if commit and creating:
            req = self._zas_req
            fn = f"{self.zas_entity}__on_create"
            h = _hook(self.zas_entity, fn) if (self._E["form"].get("create") or {}).get("on_create") else None
            if h is not None:
                h(req, obj)
            app_user.maybe_provision(obj, self.zas_entity, req, on_create=True)
        return obj


# ───────────────────────────── transition / tag / row-action forms ─────────────────────────────

class ZasActionFormMixin:
    """For transition and tag forms (BaseSimpleForm) and row-action forms (BaseForm).
    save() writes fields that share a name with an entity field onto the record
    (contracts §6), then keeps the cleaned data for the hook."""

    zas_entity = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # workflow 1.0.1 builds a transition form from request.POST only and stores the upload
        # afterwards: without the request's files a required file field always fails validation.
        req = getattr(getattr(self, "crud_view_instance", None), "request", None)
        if not self.files and getattr(req, "FILES", None):
            self.files = req.FILES

    def save(self, *args, **kwargs):
        obj = (getattr(self, "initial", {}) or {}).get("object_instance") or getattr(self, "instance", None)
        req = getattr(getattr(self, "crud_view_instance", None), "request", None)
        data = dict(self.cleaned_data)
        if obj is not None and self.zas_entity:
            keys = {f["key"] for f in zs.entity(self.zas_entity)["fields"]}
            changed = [k for k in data if k in keys]
            for k in changed:
                setattr(obj, k, data[k])
            if changed:
                obj.save()
        if req is not None:
            req._zas_form_data = {k: (v.pk if hasattr(v, "_meta") else v) for k, v in data.items()}
        return obj


# ───────────────────────────── workflow ─────────────────────────────

def fake_request(user=None):
    """For system transitions run from tasks: the engine reads FILES/POST/user."""
    return SimpleNamespace(GET={}, POST={}, FILES={}, user=user, _zas_role_name=None, tenant=None)


class ZasWorkflowMixin:
    """Supplies <engine name>_condition / _done and tag hooks from the spec."""

    zas_entity = None

    def get_object_instance(self, request, object_instance):
        """The engine loads ?object_uuid= unscoped; refuse records outside the role's rows.
        Records handed in directly (table columns, the detail view, tasks) are trusted."""
        obj = super().get_object_instance(request, object_instance)
        if object_instance is None and request is not None and obj is not None \
                and not access.in_scope(self.zas_entity, obj, request):
            raise PermissionDenied("This record is not available to your role.")
        return obj

    def _zas_spec_transition(self, engine_name):
        wf = zs.entity(self.zas_entity).get("workflow") or {}
        for t in wf.get("transitions", []):
            for e in t.get("engine", []):
                if e["name"] == engine_name:
                    return t
        return None

    def _zas_tag(self, code):
        wf = zs.entity(self.zas_entity).get("workflow") or {}
        return next((t for t in wf.get("tags", []) if t["code"] == code), None)

    def __getattr__(self, name):
        if name.startswith("_") or name in ("zas_entity", "Meta", "status_transitions", "tag_transitions"):
            raise AttributeError(name)
        try:
            return self._zas_lookup(name)
        except AttributeError:
            raise
        except Exception:  # getattr(obj, x, None) only swallows AttributeError
            logger.exception("zas: workflow hook lookup failed for %s", name)
            raise AttributeError(name)

    def _zas_lookup(self, name):
        m = re.fullmatch(r"(.+)_(condition|done)", name)
        if not m:
            raise AttributeError(name)
        base, kind = m.group(1), m.group(2)
        t = self._zas_spec_transition(base)
        if t is not None:
            if kind == "condition" and t.get("condition_ast") is not None:
                return self._zas_condition_fn(t)
            if kind == "done":
                return self._zas_done_fn(t)
            raise AttributeError(name)
        tm = re.fullmatch(r"(.+)_(enabled|disabled)", base)
        if tm and self._zas_tag(tm.group(1)):
            tag, state = self._zas_tag(tm.group(1)), tm.group(2)
            side = tag.get("enable" if state == "enabled" else "disable")
            if kind == "condition" and (side is None or tag.get("system")):
                # the engine treats empty roles as "everyone": a side the spec leaves out must be blocked here
                return lambda *a, **k: False
            side = side or {}
            if kind == "condition" and side.get("condition_ast") is not None:
                fn = f"{self.zas_entity}__tag_{tag['code']}_{'enable' if state == 'enabled' else 'disable'}__condition"
                return self._zas_cond_from(side["condition_ast"], fn)
            if kind == "done":
                return lambda request, obj, txn: app_user.maybe_provision(obj, self.zas_entity, request)
            raise AttributeError(name)
        # on-create: engine calls <initial status>_done
        wf = zs.entity(self.zas_entity).get("workflow") or {}
        if kind == "done" and base in {s["code"] for s in wf.get("statuses", [])}:
            return lambda request, obj, txn: app_user.maybe_provision(obj, self.zas_entity, request)
        raise AttributeError(name)

    def _zas_cond_from(self, ast, hook_fn):
        entity = self.zas_entity

        def cond(request=None, object_instance=None, *args, **kwargs):
            obj = object_instance if object_instance is not None else (args[0] if args else None)
            h = _hook(entity, hook_fn)
            ctx = access.expr_ctx(request, text=(lambda node: h(request, obj) if h else True))
            return zx.evaluate(ast, obj, ctx)
        return cond

    def _zas_condition_fn(self, t):
        return self._zas_cond_from(t["condition_ast"], f"{self.zas_entity}__{t['name']}__condition")

    def _zas_done_fn(self, t):
        entity = self.zas_entity

        def done(request, obj, transaction_obj):
            form_data = ((getattr(transaction_obj, "data", None) or {}).get("form_data")) or {}
            if t.get("on_done"):
                h = _hook(entity, f"{entity}__{t['name']}__done")
                if h is not None:
                    h(request, obj, form_data)
            app_user.maybe_provision(obj, entity, request)
        return done


def run_system_transition(entity_code, obj, spec_name, user=None):
    """Move one record through a system transition (from tasks.py). Returns (ok, message)."""
    WF = zs.workflow_class(entity_code)
    if WF is None:
        return False, "no workflow"
    t = None
    for x in zs.entity(entity_code)["workflow"]["transitions"]:
        if x["name"] == spec_name:
            t = x
    if t is None:
        return False, f"unknown transition {spec_name}"
    req = fake_request(user)
    wf = WF(request=req, object_instance=obj)
    status = zx.current_status(obj)
    engine = next((e["name"] for e in t["engine"] if e["from"] == status), None)
    if engine is None:
        return False, f"{spec_name} does not start from {status}"
    return wf.execute_transition(engine, allow_system=True)


def set_system_tag(entity_code, obj, tag, enabled, user=None):
    """Set or clear a system tag (from tasks.py). No-op if already in that state."""
    from ...packages.workflow.base.models import WorkflowTransaction
    want = "enabled" if enabled else "disabled"
    on = tag in zx.current_tags(obj)
    if on == enabled:
        return False
    WorkflowTransaction.objects.create(
        obj_uuid=obj.object_uuid, transition_name=tag, transition_type="tag",
        from_state="disabled" if enabled else "enabled", to_state=want, actor=user, data={"system": True})
    return True


# ───────────────────────────── crud view ─────────────────────────────

class ZasCrudViewMixin:
    """Adds the role check for `add` from form.create.roles on top of the policy feature."""

    zas_entity = None

    def display_add_button_check(self, request):
        ok = super().display_add_button_check(request)
        roles = ((zs.entity(self.zas_entity).get("form") or {}).get("create") or {}).get("roles")
        if ok and roles:
            ok = access.role_name(request) in roles
        return ok

    def get(self, request, *args, **kwargs):
        # ?action=zas_record&object_uuid=… → the record drawer payload (any entity; row-scoped)
        if request.GET.get("action") == "zas_record":
            from zango.core.api import get_api_response
            from .detail import record_payload
            role = access.role_name(request)
            E = zs.entity(self.zas_entity)
            if E.get("access") and not access.can(self.zas_entity, "view", role):
                return get_api_response(True, {"access": "no_access"}, 200)
            uid = access.clean_uuid(request.GET.get("object_uuid"))
            qs = access.scope_queryset(self.zas_entity, self.model.objects.all(), request)
            obj = qs.filter(object_uuid=uid).first() if uid else None
            if obj is None:
                return get_api_response(True, {"access": "not_found"}, 200)
            try:
                return get_api_response(True, record_payload(self, request, self.zas_entity, obj), 200)
            except Exception:
                logger.exception("zas: record payload for %s", self.zas_entity)
                return get_api_response(False, {"message": "The record could not be loaded."}, 500)
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        if request.GET.get("form_type") == "create_form" and not request.GET.get("form_action"):
            if not self.display_add_button_check(request):
                raise PermissionDenied("You can't add records here.")
        return super().post(request, *args, **kwargs)
