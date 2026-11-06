"""
AI helpers at runtime (spec ai.agents; references/map/ai.md).

Every app gets the same behaviour from here; the build writes only the prompts
(backend/<module>/ai/<code>.*.md, uploaded to Zango by the platform), custom tools
(tools.py) and the hand-written tasks that call run_from_code().

    on_event(entity, obj, event, ...)   create / update / transition / tag / delete triggers (from mixins.py)
    run(code, obj=…, trigger=…)          start a run: background (Celery task zas_ai_run) or inline
    execute(run)                         call the Zango agent and deliver the answer
    accept(s, user, values) / discard    a person decides on a suggestion
    chat(code, obj, message, session)    the "Ask AI" panel (inline, with memory)
    form_assist(code, values, files)     fill an unsaved form from its documents (inline)
    run_from_code(code, obj, variables)  for hand-written tasks (uses_ai); returns a Result, never raises
    schedule_tick(now)                   schedule triggers (zas_ai_tick runs every minute)

What the AI sees: only the agent's context fields, related rows and files, and only
records the acting person can see (built-in tools are scoped the same way).
Where the answer goes: review none → written to the record; suggest → a
ZasAiSuggestion a person accepts or discards; show → only displayed.
No AI account yet (placeholder provider, no key, agent missing or off): the run ends
"unavailable" and the app carries on. Saving a record never waits for or fails on AI.

Fake mode for tests: ZAS_AI_FAKE=1 (or settings.ZAS_AI_FAKE) answers with the spec's
preview.sample, or what set_fake(code, answer) registered. Scenario tests talk to the running
server, so with DEBUG on the file <ws>/.zas/ai_fake.json does the same ({"*": true} = every helper
answers with its sample; {"<code>": answer} overrides one); zas_test's ctx.ai_fake() writes it.
"""

import contextvars
import datetime
import decimal
import json
import logging
import mimetypes
import os
from dataclasses import dataclass, field

from django.db import connection, transaction
from django.utils import timezone

from . import access
from . import expr as zx
from . import records as zr
from . import spec as zs

logger = logging.getLogger(__name__)

TASK = "backend.zas_core.tasks.zas_ai_run"
ACTIVE = ("queued", "running")
UNAVAILABLE = "AI isn't set up for this app yet."
_acting = contextvars.ContextVar("zas_ai_acting", default=None)  # {agent, request} while an agent runs
_applying = contextvars.ContextVar("zas_ai_applying", default=False)  # loop guard: AI writes fire no triggers
_fakes = {}


class Unavailable(Exception):
    """The app has no working AI account (placeholder, no key, agent missing or switched off)."""


class Denied(Exception):
    pass


@dataclass
class Result:
    """What run_from_code returns: status done | failed | unavailable, the parsed answer, and the run id."""

    status: str
    result: object = None
    error: str = ""
    run_id: int = None
    raw: dict = field(default_factory=dict)

    @property
    def ok(self):
        return self.status == "done"


# ───────────────────────────── spec ─────────────────────────────

def agents():
    return (zs.load().get("ai") or {}).get("agents") or []


def agent(code):
    a = next((x for x in agents() if x["code"] == code), None)
    if a is None:
        raise KeyError(f"zas: AI helper {code!r} is not in spec.json ai.agents")
    return a


def agents_for(entity_code):
    return [a for a in agents() if a.get("entity") == entity_code]


def _models():
    from .models import ZasAiRun, ZasAiSuggestion
    return ZasAiRun, ZasAiSuggestion


_FAKE_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), ".zas", "ai_fake.json")


def _fake_file():
    from django.conf import settings
    if not settings.DEBUG or not os.path.exists(_FAKE_FILE):
        return None
    try:
        with open(_FAKE_FILE, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return None


def fake_on():
    from django.conf import settings
    return os.environ.get("ZAS_AI_FAKE") in ("1", "true") or bool(getattr(settings, "ZAS_AI_FAKE", False)) \
        or _fake_file() is not None


def set_fake(code, answer):
    """Tests: answer `code` with this (dict for kind fields, text otherwise); None clears it."""
    if answer is None:
        _fakes.pop(code, None)
    else:
        _fakes[code] = answer


def can_run(a, role, trigger=None):
    """The role may run this helper (and, for a person's click, this particular trigger)."""
    if role not in (a.get("roles") or []):
        return False
    if trigger and trigger.get("roles"):
        return role in trigger["roles"]
    return True


def triggers(a, event, where=None):
    return [t for t in a.get("triggers") or [] if t.get("event") == event and (where is None or t.get("where") == where)]


# ───────────────────────────── what the AI reads ─────────────────────────────

def _line(E, obj, path):
    fv = zr.field_value(E, obj, path)
    return f"{fv['label']}: {fv['display'] if fv['display'] not in (None, '') else '(empty)'}"


def record_text(a, obj):
    """The record as the AI sees it: one 'Label: value' line per context field."""
    if obj is None:
        return ""
    E = zs.entity(a["entity"])
    paths = a["context"]["fields"] or [E["display"]]
    return "\n".join(_line(E, obj, p) for p in paths)


def values_text(a, values):
    """An unsaved form's values (form assist), as 'Label: value' lines."""
    E = zs.entity(a["entity"]) if a.get("entity") else {"fields": []}
    labels = {f["key"]: f.get("label") or f["key"] for f in E["fields"]}
    return "\n".join(f"{labels.get(k, k)}: {v}" for k, v in (values or {}).items() if v not in (None, "", []))


def related_text(a, obj, request=None):
    if obj is None:
        return ""
    out = []
    for r in a["context"]["related"]:
        T = zs.entity(r["entity"])
        qs = zs.model(r["entity"]).objects.filter(**{r["via"]: obj}) if r.get("via") else zs.model(r["entity"]).objects.none()
        if request is not None:
            qs = access.scope_queryset(r["entity"], qs, request)
        if r.get("where_ast"):
            qs = qs.filter(zx.to_q(r["where_ast"], qs.model, access.expr_ctx(request)))
        rows = list(qs.order_by("-id")[: r["limit"]])
        out.append(f"{r['label']} ({len(rows)}{'+' if len(rows) == r['limit'] else ''}):")
        out += ["- " + "; ".join(_line(T, row, p) for p in r["fields"]) for row in rows]
    return "\n".join(out)


def rows_text(a, rows):
    E = zs.entity(a["entity"])
    paths = a["context"]["fields"] or [E["display"]]
    return f"{len(rows)} {E['plural'].lower()}:\n" + "\n".join("- " + "; ".join(_line(E, r, p) for p in paths) for r in rows)


def files_of(a, obj=None, uploads=None):
    """LLMFile attachments: the record's context.files, or the uploads of a form being filled."""
    from zango.ai import LLMFile
    out = []
    for f in uploads or []:
        data = f.read()
        out.append(LLMFile.from_bytes(data, media_type=getattr(f, "content_type", None) or _mime(f.name), filename=f.name))
    for key in a["context"]["files"] if obj is not None else []:
        ff = getattr(obj, key, None)
        if not ff or not getattr(ff, "name", None):
            continue
        try:
            ff.open("rb")
            data = ff.read()
        finally:
            try:
                ff.close()
            except Exception:
                pass
        out.append(LLMFile.from_bytes(data, media_type=_mime(ff.name), filename=ff.name.rsplit("/", 1)[-1]))
    return out


def _mime(name):
    return mimetypes.guess_type(name or "")[0] or "application/octet-stream"


def variables(a, obj=None, rows=None, values=None, request=None, role=None, input=None, snapshot=None):
    """Every {{variable}} the agent's prompts declare (Zango refuses a prompt with one missing)."""
    rec = values_text(a, values) if values is not None else snapshot if obj is None and snapshot else record_text(a, obj)
    have = {"today": timezone.localdate().isoformat(), "role": role or "", "record": rec,
            "records": rows_text(a, rows) if rows is not None else "",
            "related": related_text(a, obj, request) if a["context"]["related"] else "",
            "input": input if isinstance(input, str) else json.dumps(input, default=str) if input is not None else ""}
    out = {}
    for k, p in a["prompts"].items():
        out[k] = {v: have.get(v, "") for v in p["variables"]}
    return out.get("system", {}), out.get("user", {})


# ───────────────────────────── calling Zango ─────────────────────────────

def _client(a):
    from zango.ai import get_agent
    from zango.ai.exceptions import AgentNotFound
    try:
        client = get_agent(a["zango_name"])
    except AgentNotFound:
        raise Unavailable(UNAVAILABLE)
    ag = client._agent
    p = ag.provider
    if not ag.is_enabled or p is None or not p.is_enabled:
        raise Unavailable(UNAVAILABLE)
    connected = getattr(p, "is_connected", None)  # Zango with platform AI accounts
    if connected is False or (connected is None and not p.is_validated):
        raise Unavailable(UNAVAILABLE)
    return client


def _fake(a):
    ans = _fakes.get(a["code"], (_fake_file() or {}).get(a["code"], a.get("sample")))
    if a["output"]["kind"] == "fields":
        return dict(ans or {})
    return ans if isinstance(ans, str) else ("" if ans is None else json.dumps(ans))


def call(a, request=None, role=None, system_variables=None, user_variables=None, input=None, files=None,
         session_id=None, triggered_by="user"):
    """One Zango agent call. Returns (answer, session_id): a dict for kind fields, text otherwise."""
    if fake_on():
        return _fake(a), session_id
    from zango.ai.exceptions import AgentDisabled, BudgetExceeded, OutputParseError, ProviderDisabled, ZangoAIError
    client = _client(a)
    token = _acting.set({"agent": a, "request": request, "role": role})
    try:
        kw = {"system_variables": system_variables or None, "triggered_by": triggered_by, "files": files or None}
        if input is not None:
            kw["input"] = input
        else:
            kw["variables"] = user_variables or {}
        if session_id or a.get("memory"):
            kw["session_id"] = session_id
            kw["user_ref"] = str(getattr(getattr(request, "user", None), "pk", "") or "")
        resp = client.run(**kw)
    except (AgentDisabled, ProviderDisabled):
        raise Unavailable(UNAVAILABLE)
    except BudgetExceeded:
        raise Unavailable("The AI account is over its monthly budget.")
    except OutputParseError as e:
        raise RuntimeError(f"The AI's answer was not in the expected shape: {e}")
    except ZangoAIError as e:
        if type(e).__name__ == "ProviderNotConnected":  # Zango with placeholder support (P3)
            raise Unavailable(UNAVAILABLE)
        raise
    finally:
        _acting.reset(token)
    if a["output"]["kind"] == "fields":
        return dict(getattr(resp, "parsed_content", None) or json.loads(resp.content or "{}")), getattr(resp, "session_id", session_id)
    return resp.content or "", getattr(resp, "session_id", session_id)


def acting():
    """While an agent runs: {agent, request, role}. The built-in tools read it."""
    return _acting.get()


# ───────────────────────────── runs ─────────────────────────────

def _payload_role(request):
    return access.role_name(request) if request is not None else ""


def run(code, obj=None, trigger="button", request=None, rows=None, input=None, inline=None, check=True, snapshot=False):
    """Start a run. inline (default: the agent's run setting, async for background triggers)
    executes it now; otherwise it is queued for the zas_ai_run task once the transaction commits."""
    a = agent(code)
    role = _payload_role(request)
    if check and request is not None and not can_run(a, role):
        raise Denied(f"{role} may not run {a['name']}")
    ZasAiRun, _ = _models()
    user = getattr(request, "user", None) if request is not None else None
    r = ZasAiRun.objects.create(
        agent=code, entity=a.get("entity") or "", record_uuid=str(getattr(obj, "object_uuid", "") or ""),
        trigger=trigger, role=role or "",
        inputs={k: v for k, v in {"rows": [str(x.object_uuid) for x in rows] if rows is not None else None,
                                  "input": input,
                                  # a deleted record is gone by the time a background run starts
                                  "record": record_text(a, obj) if snapshot and obj is not None else None}.items()
                if v is not None},
        created_by=user if getattr(user, "pk", None) and type(user).__name__ == "AppUserModel" else None)
    inline = (a["run"] == "inline") if inline is None else inline
    if inline:
        return execute(r, request=request, obj=obj, rows=rows)
    _enqueue(r)
    return r


def _enqueue(r):
    def go():
        try:
            from zango.core.tasks import zango_task_executor
            zango_task_executor.delay(connection.tenant.name, TASK, run_id=r.pk)
        except Exception:
            logger.exception("zas: could not queue AI run %s; running it now", r.pk)
            execute(r)
    transaction.on_commit(go)


class _RunRequest:
    """For background runs: the role the run was started as, so scoping and tools match it."""

    def __init__(self, user, role):
        self.user, self._zas_role_name = user, role or None
        self.GET, self.POST, self.FILES = {}, {}, {}


def execute(r, request=None, obj=None, rows=None):
    """Run it now: call the agent, then deliver the answer. Never raises."""
    ZasAiRun, _ = _models()
    if r.status not in ACTIVE:
        return r
    a = agent(r.agent)
    r.status = "running"
    r.save(update_fields=["status", "modified_at"])
    req = request or _RunRequest(r.created_by, r.role)
    try:
        if obj is None and r.record_uuid and a.get("entity"):
            obj = zs.model(a["entity"]).objects.filter(object_uuid=r.record_uuid).first()
            if obj is None and "record" not in (r.inputs or {}):
                raise RuntimeError("The record is gone.")
        if rows is None and "rows" in (r.inputs or {}):
            qs = zs.model(a["entity"]).objects.filter(object_uuid__in=r.inputs["rows"])
            rows = list(access.scope_queryset(a["entity"], qs, req) if r.role else qs)
        sv, uv = variables(a, obj=obj, rows=rows, request=req if r.role else None, role=r.role,
                           input=(r.inputs or {}).get("input"), snapshot=(r.inputs or {}).get("record"))
        answer, _ = call(a, request=req, role=r.role, system_variables=sv, user_variables=uv,
                         files=files_of(a, obj) if a["context"]["files"] and obj is not None else None,
                         triggered_by="user" if r.trigger in ("button", "chat", "form_assist") else
                         ("cron" if r.trigger == "schedule" else "celery"))
        r.result = _clean(a, answer)
        r.status = "done"
        deliver(a, r, obj)
    except Unavailable as e:
        r.status, r.error = "unavailable", str(e)
    except Exception as e:  # noqa: BLE001 - a run never breaks the caller
        logger.exception("zas: AI run %s (%s) failed", r.pk, r.agent)
        r.status, r.error = "failed", _message(e)
    r.finished_at = timezone.now()
    r.save()
    return r


def _message(e):
    text = str(e) or type(e).__name__
    return text[:500]


def _clean(a, answer):
    """Keep only the declared keys of a fields answer; text stays text."""
    if a["output"]["kind"] != "fields":
        return answer if isinstance(answer, str) else json.dumps(answer, default=str)
    keys = {f["key"] for f in a["output"]["fields"]}
    return {k: v for k, v in (answer or {}).items() if k in keys}


def writes(a, answer):
    """{entity field: value} the answer would write (fields with `to`, or output.to for text)."""
    o = a["output"]
    if o["kind"] == "fields":
        return {f["to"]: (answer or {}).get(f["key"]) for f in o["fields"] if f.get("to") and (answer or {}).get(f["key"]) not in (None, "")}
    return {o["to"]: answer} if o.get("to") and answer else {}


def deliver(a, r, obj):
    if obj is None:
        return
    w = writes(a, r.result)
    if not w:
        return
    if a["review"] == "none":
        apply(a["entity"], obj, w)
        r.applied = True
    elif a["review"] == "suggest":
        _, ZasAiSuggestion = _models()
        ZasAiSuggestion.objects.filter(agent=a["code"], record_uuid=r.record_uuid, status="pending").update(status="stale")
        ZasAiSuggestion.objects.create(run=r, agent=a["code"], entity=a["entity"], record_uuid=r.record_uuid,
                                       values={k: _jsonable(v) for k, v in w.items()})


def _jsonable(v):
    return float(v) if isinstance(v, decimal.Decimal) else v


def _coerce(f, v):
    t = (f or {}).get("type")
    if v in (None, ""):
        return None
    if t in ("integer",):
        return int(float(v))
    if t in ("decimal", "money", "percent"):
        return decimal.Decimal(str(v))
    if t == "boolean":
        return v in (True, "true", "True", 1, "1", "yes")
    if t == "date":
        return datetime.date.fromisoformat(str(v)[:10])
    if t == "multi_choice":
        return [str(x) for x in (v if isinstance(v, list) else [v])]
    if t == "choice":
        return str(v)
    return str(v)


def apply(entity_code, obj, values):
    """Write AI values onto the record. No triggers fire from this save (loop guard)."""
    E = zs.entity(entity_code)
    fmap = {f["key"]: f for f in E["fields"]}
    token = _applying.set(True)
    try:
        for k, v in values.items():
            if k in fmap:
                setattr(obj, k, _coerce(fmap[k], v))
        obj.save()
    finally:
        _applying.reset(token)


def accept(s, request, values=None):
    """A person accepts a suggestion, optionally with their edits ({field: value}). Returns the record."""
    if s.status != "pending":
        raise Denied("This suggestion was already handled.")
    a = agent(s.agent)
    if not can_run(a, _payload_role(request)):
        raise Denied("You can't accept this suggestion.")
    obj = access.scope_queryset(s.entity, zs.model(s.entity).objects.filter(object_uuid=s.record_uuid), request).first()
    if obj is None:
        raise Denied("The record is not visible to you.")
    vals = {k: v for k, v in (values if values is not None else s.values).items() if k in s.values}
    apply(s.entity, obj, vals)
    s.status, s.decided_at = "accepted", timezone.now()
    s.modified_by = request.user if type(getattr(request, "user", None)).__name__ == "AppUserModel" else None
    s.save()
    s.run.applied = True
    s.run.save(update_fields=["applied", "modified_at"])
    return obj


def discard(s, request):
    if s.status != "pending":
        raise Denied("This suggestion was already handled.")
    if not can_run(agent(s.agent), _payload_role(request)):
        raise Denied("You can't discard this suggestion.")
    s.status, s.decided_at = "discarded", timezone.now()
    s.save()


# ───────────────────────────── inline helpers ─────────────────────────────

def chat(code, obj, message, request, session_id=None, rows=None):
    """One chat turn. Returns {answer, session_id, run}."""
    a = agent(code)
    role = _payload_role(request)
    if not can_run(a, role):
        raise Denied(f"{role} may not use {a['name']}")
    ZasAiRun, _ = _models()
    user = getattr(request, "user", None)
    r = ZasAiRun.objects.create(agent=code, entity=a.get("entity") or "", record_uuid=str(getattr(obj, "object_uuid", "") or ""),
                                trigger="chat", role=role or "", status="running", inputs={"message": message[:2000]},
                                created_by=user if type(user).__name__ == "AppUserModel" else None)
    sv, _ = variables(a, obj=obj, rows=rows, request=request, role=role)
    try:
        answer, session_id = call(a, request=request, role=role, system_variables=sv, input=message, session_id=session_id)
        r.status, r.result = "done", answer
    except Unavailable as e:
        r.status, r.error, answer = "unavailable", str(e), None
    except Exception as e:  # noqa: BLE001
        logger.exception("zas: AI chat %s failed", code)
        r.status, r.error, answer = "failed", _message(e), None
    r.finished_at = timezone.now()
    r.save()
    return {"answer": answer, "session_id": session_id, "run": run_payload(r)}


def form_assist(code, values, uploads, request):
    """Fill an unsaved form from its documents. Returns {form field: value} (nothing is saved)."""
    a = agent(code)
    role = _payload_role(request)
    if not can_run(a, role):
        raise Denied(f"{role} may not use {a['name']}")
    ZasAiRun, _ = _models()
    user = getattr(request, "user", None)
    r = ZasAiRun.objects.create(agent=code, entity=a.get("entity") or "", trigger="form_assist", role=role or "",
                                status="running", created_by=user if type(user).__name__ == "AppUserModel" else None)
    sv, uv = variables(a, values=values or {}, request=request, role=role)
    try:
        answer, _ = call(a, request=request, role=role, system_variables=sv, user_variables=uv,
                         files=files_of(a, uploads=uploads) or None)
        r.status, r.result = "done", _clean(a, answer)
    except Unavailable as e:
        r.status, r.error = "unavailable", str(e)
    except Exception as e:  # noqa: BLE001
        logger.exception("zas: AI form fill %s failed", code)
        r.status, r.error = "failed", _message(e)
    r.finished_at = timezone.now()
    r.save()
    return {"values": {k: _jsonable(v) for k, v in writes(a, r.result).items()} if r.status == "done" else {},
            "run": run_payload(r)}


def run_from_code(code, obj=None, variables=None, triggered_by="celery"):
    """For hand-written tasks and hooks (custom requirements with uses_ai). Synchronous; never raises.

        res = run_from_code("invoice_triage", obj=invoice, variables={"input": email_text})
        if res.ok: ...res.result...        # dict for kind fields, text otherwise
        elif res.status == "unavailable":  # no AI account yet: carry on without it
    """
    try:
        a = agent(code)
    except KeyError as e:
        return Result("failed", error=str(e))
    ZasAiRun, _ = _models()
    inp = (variables or {}).get("input") if isinstance(variables, dict) else variables
    r = ZasAiRun.objects.create(agent=code, entity=a.get("entity") or "", record_uuid=str(getattr(obj, "object_uuid", "") or ""),
                                trigger="schedule" if triggered_by == "cron" else "task", status="queued",
                                inputs={"input": inp} if inp is not None else {})
    execute(r, obj=obj)
    return Result(r.status, r.result, r.error, r.pk, run_payload(r))


# ───────────────────────────── triggers ─────────────────────────────

def on_event(entity_code, obj, event, request=None, transition=None, tag=None, changed=None):
    """Background triggers. Called after the record is saved; never raises, never blocks."""
    if _applying.get() or obj is None:
        return
    try:
        for a in agents_for(entity_code):
            for t in triggers(a, event):
                if event == "transition" and t.get("transition") != transition:
                    continue
                if event == "tag" and t.get("tag") != tag:
                    continue
                if event == "update" and t.get("fields") and changed is not None and not set(t["fields"]) & set(changed):
                    continue
                if t.get("when_ast") is not None and not zx.evaluate(t["when_ast"], obj, access.expr_ctx(request)):
                    continue
                run(a["code"], obj=obj, trigger=event, request=request, inline=False, check=False,
                    snapshot=event == "delete")
                break  # one run per helper per event
    except Exception:  # noqa: BLE001
        logger.exception("zas: AI triggers for %s %s", entity_code, event)


def _cron_match(expr, now):
    """Five-field cron (*, */n, a-b, a-b/n, lists). Day of week: 0 or 7 = Sunday."""
    parts = str(expr or "").split()
    if len(parts) != 5:
        return False
    vals = (now.minute, now.hour, now.day, now.month, (now.isoweekday() % 7))
    ranges = ((0, 59), (0, 23), (1, 31), (1, 12), (0, 7))
    for part, v, (lo, hi) in zip(parts, vals, ranges):
        ok = False
        for p in part.split(","):
            base, _, step = p.partition("/")
            step = int(step) if step else 1
            if base == "*":
                a, b = lo, hi
            elif "-" in base:
                a, b = (int(x) for x in base.split("-", 1))
            else:
                a = int(base)
                b = hi if step > 1 else a
            rng = range(a, b + 1, step)
            if v in rng or (hi == 7 and v == 0 and 7 in rng):
                ok = True
        if not ok:
            return False
    return True


def any_schedule():
    return any(triggers(a, "schedule") for a in agents())


def schedule_tick(now=None, limit=200):
    """Run every schedule trigger due this minute: once per matching record (entity helpers,
    filtered by `when`), or once for a helper with no entity. Returns the number of runs queued."""
    now = timezone.localtime(now or timezone.now())
    n = 0
    for a in agents():
        for t in triggers(a, "schedule"):
            if not _cron_match(t.get("cron"), now):
                continue
            if not a.get("entity"):
                run(a["code"], trigger="schedule", inline=False, check=False)
                n += 1
                continue
            qs = zs.model(a["entity"]).objects.all()
            if t.get("when_ast") is not None:
                qs = qs.filter(zx.to_q(t["when_ast"], qs.model, {}))
            for obj in qs.order_by("id")[:limit]:
                run(a["code"], obj=obj, trigger="schedule", inline=False, check=False)
                n += 1
    return n


# ───────────────────────────── payloads ─────────────────────────────

def suggestion_payload(s, obj=None):
    a = agent(s.agent)
    E = zs.entity(s.entity)
    fmap = {f["key"]: f for f in E["fields"]}
    out = []
    for k, v in s.values.items():
        f = fmap.get(k) or {}
        cur = zr.field_value(E, obj, k)["display"] if obj is not None else None
        disp = v
        if f.get("type") in ("choice", "multi_choice"):
            ch = {str(c["id"]): c.get("label") for c in f.get("choices") or []}
            disp = ", ".join(ch.get(str(x), str(x)) for x in (v if isinstance(v, list) else [v]))
        out.append({"key": k, "label": f.get("label") or k, "type": f.get("type") or "text", "value": v,
                    "display": disp, "current": cur})
    return {"id": s.pk, "agent": s.agent, "name": a["name"], "status": s.status, "fields": out,
            "created_at": s.created_at.isoformat() if s.created_at else None}


def run_payload(r):
    a = next((x for x in agents() if x["code"] == r.agent), None) or {"name": r.agent, "output": {"kind": "text", "fields": []}}
    sugg = None
    if r.status == "done" and a.get("review") == "suggest":
        s = r.suggestions.filter(status="pending").first() if r.pk else None
        sugg = suggestion_payload(s) if s else None
    labels = {f["key"]: f.get("label") or f["key"] for f in a["output"].get("fields") or []}
    result = r.result
    if a["output"]["kind"] == "fields" and isinstance(result, dict):
        result = [{"key": k, "label": labels.get(k, k), "value": v} for k, v in result.items()]
    return {"id": r.pk, "agent": r.agent, "name": a["name"], "status": r.status, "trigger": r.trigger,
            "kind": a["output"]["kind"], "result": result, "error": r.error, "applied": r.applied,
            "suggestion": sugg, "record_uuid": r.record_uuid or None}


def clicks(entity_code, role, where):
    """The buttons and chats a role sees in one place (record | row | list | form):
    [{agent, name, event, label, icon}] — the same rule as zas-render.js aiClicks()."""
    out = []
    for a in agents_for(entity_code):
        for t in a.get("triggers") or []:
            ev = t.get("event")
            here = (ev in ("button", "chat") and t.get("where", "record") == where) or (ev == "form_assist" and where == "form")
            if here and can_run(a, role, t):
                out.append({"agent": a["code"], "name": a["name"], "event": ev, "kind": a["output"]["kind"],
                            "label": t.get("label") or ("Ask AI" if ev == "chat" else a["name"]),
                            "icon": t.get("icon") or ("message-circle" if ev == "chat" else "sparkles"),
                            **({"from": t.get("from") or []} if ev == "form_assist" else {})})
    return out


def record_ai(entity_code, obj, request):
    """The 360 payload's `ai`: the record's AI buttons and chats for this role, open suggestions and
    runs still working. Empty when the entity has no AI helpers."""
    if not agents_for(entity_code):
        return None
    role = _payload_role(request)
    return {"clicks": clicks(entity_code, role, "record"), **pending_for(entity_code, obj, request)}


def pending_for(entity_code, obj, request):
    """What the record page shows on load: open suggestions and runs still working, for this role."""
    ZasAiRun, ZasAiSuggestion = _models()
    role = _payload_role(request)
    codes = [a["code"] for a in agents_for(entity_code) if can_run(a, role)]
    uid = str(obj.object_uuid)
    sugg = [suggestion_payload(s, obj) for s in ZasAiSuggestion.objects.filter(
        record_uuid=uid, agent__in=codes, status="pending").order_by("-id")]
    runs = [run_payload(r) for r in ZasAiRun.objects.filter(
        record_uuid=uid, agent__in=codes, status__in=ACTIVE).order_by("-id")[:10]]
    return {"suggestions": sugg, "runs": runs}
