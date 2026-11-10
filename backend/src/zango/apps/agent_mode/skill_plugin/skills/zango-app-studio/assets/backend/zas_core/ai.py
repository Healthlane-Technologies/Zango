"""
AI helpers at runtime (spec ai.agents; references/map/ai.md).

Every app gets the same behaviour from here; the build writes only the prompts
(backend/<module>/ai/<code>.*.md, uploaded to Zango by the platform), custom tools
(tools.py) and the hand-written tasks that call run_from_code().

    on_event(entity, obj, event, ...)   create / update / transition / tag / delete triggers (from mixins.py)
    run(code, obj=…, trigger=…)          queue a run (Celery task zas_ai_run); the screen polls it
    execute(run)                         call the Zango agent and deliver the answer (in the task)
    accept(s, user, values) / discard    a person decides on a suggestion
    chat(code, obj, message, session)    the "Ask AI" panel: queues one turn (with memory); polled
    form_assist(code, values, files)     fill an unsaved form from its documents: queued; polled
    run_later(code, obj, then=…)         from a hook during a save: queue the run, then call `then`
    run_from_code(code, obj, variables)  inside a task (uses_ai); returns a Result, never raises
    schedule_tick(now)                   schedule triggers (zas_ai_tick runs every minute)

An agent never runs inside a web request: every call happens in the zas_ai_run Celery task (or in
a task the app wrote), and the screen polls `?action=zas_ai&run=<id>`. run_from_code refuses to
run during a request; a hook uses run_later instead.

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
         session_id=None, triggered_by="user", obj=None):
    """One Zango agent call. Returns (answer, session_id): a dict for kind fields, text otherwise.
    obj: the record the helper works on, handed to its tools through acting()."""
    if fake_on():
        return _fake(a), session_id
    from zango.ai.exceptions import AgentDisabled, BudgetExceeded, OutputParseError, ProviderDisabled, ZangoAIError
    client = _client(a)
    token = _acting.set({"agent": a, "request": request, "role": role, "record": obj})
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
    """While an agent runs: {agent, request, role, record}. Tools read it: `record` is the model
    instance the helper works on (None for list buttons and form fill); `request.user` is the person
    who started it, None for task and schedule runs; `role` is "" when no person started it."""
    return _acting.get()


# ───────────────────────────── runs ─────────────────────────────

def _payload_role(request):
    return access.role_name(request) if request is not None else ""


def run(code, obj=None, trigger="button", request=None, rows=None, input=None, check=True, snapshot=False, extra=None):
    """Queue a run for the zas_ai_run task (sent once the transaction commits) and return it; the
    caller polls it. extra: more inputs the task reads (a chat message, a form's values and files)."""
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
                                  "record": record_text(a, obj) if snapshot and obj is not None else None,
                                  **(extra or {})}.items()
                if v is not None},
        created_by=user if getattr(user, "pk", None) and type(user).__name__ == "AppUserModel" else None)
    _enqueue(r)
    return r


def _enqueue(r):
    def go():
        try:
            from zango.core.tasks import zango_task_executor
            zango_task_executor.delay(connection.tenant.name, TASK, run_id=r.pk)
        except Exception:  # never run it here instead: an agent does not run in a request
            logger.exception("zas: could not queue AI run %s", r.pk)
            type(r).objects.filter(pk=r.pk, status="queued").update(
                status="failed", error="The background worker could not be reached. Try again in a minute.",
                finished_at=timezone.now())
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
        inp = r.inputs or {}
        by = "user" if r.trigger in ("button", "chat", "form_assist") else ("cron" if r.trigger == "schedule" else "celery")
        if r.trigger == "chat":
            sv, _ = variables(a, obj=obj, rows=rows, request=req if r.role else None, role=r.role)
            answer, sid = call(a, request=req, role=r.role, system_variables=sv, input=inp.get("message") or "",
                               session_id=inp.get("session_id") or None, triggered_by=by, obj=obj,
                               files=files_of(a, obj) if a["context"]["files"] and obj is not None else None)
            r.result, r.inputs = answer, {**inp, "session_out": sid}
        elif r.trigger == "form_assist":
            sv, uv = variables(a, values=inp.get("values") or {}, request=req if r.role else None, role=r.role)
            answer, _ = call(a, request=req, role=r.role, system_variables=sv, user_variables=uv, triggered_by=by,
                             files=files_of(a, uploads=_stored_files(inp.get("files"))) or None)
            r.result = _clean(a, answer)
        else:
            sv, uv = variables(a, obj=obj, rows=rows, request=req if r.role else None, role=r.role,
                               input=inp.get("input"), snapshot=inp.get("record"))
            answer, _ = call(a, request=req, role=r.role, system_variables=sv, user_variables=uv,
                             files=files_of(a, obj) if a["context"]["files"] and obj is not None else None,
                             triggered_by=by, obj=obj)
            r.result = _clean(a, answer)
        r.status = "done"
        if r.trigger != "form_assist":
            deliver(a, r, obj)
    except Unavailable as e:
        r.status, r.error = "unavailable", str(e)
    except Exception as e:  # noqa: BLE001 - a run never breaks the caller
        logger.exception("zas: AI run %s (%s) failed", r.pk, r.agent)
        r.status, r.error = "failed", _message(e)
    finally:
        _drop_files((r.inputs or {}).get("files"))
    r.finished_at = timezone.now()
    r.save()
    _then(a, r, obj)
    return r


def _then(a, r, obj):
    """run_later's continuation: <module>/hooks.py::<then>(obj, Result), after the run, whatever its status."""
    name = (r.inputs or {}).get("then")
    if not name:
        return
    fn = zs.hook(zs.entity(a["entity"])["module"], name) if a.get("entity") else None
    if fn is None:
        r.error = (r.error + "\n" if r.error else "") + f"then: {name} is not in hooks.py"
        r.save(update_fields=["error", "modified_at"])
        return
    try:
        fn(obj, Result(r.status, r.result, r.error, r.pk, run_payload(r)))
    except Exception as e:  # noqa: BLE001
        logger.exception("zas: %s after AI run %s failed", name, r.pk)
        r.error = (r.error + "\n" if r.error else "") + f"then: {_message(e)}"
        r.save(update_fields=["error", "modified_at"])


# Form fill uploads wait in storage for the task, which removes them after the run.
def _store_files(uploads):
    import uuid
    from django.core.files.storage import default_storage
    out = []
    for f in uploads or []:
        name = default_storage.save(f"zas_ai_uploads/{uuid.uuid4().hex}/{os.path.basename(f.name)}", f)
        out.append({"path": name, "name": os.path.basename(f.name), "type": getattr(f, "content_type", None) or _mime(f.name)})
    return out


class _Stored:
    def __init__(self, d):
        from django.core.files.storage import default_storage
        self.name, self.content_type, self._path, self._st = d["name"], d.get("type"), d["path"], default_storage

    def read(self):
        with self._st.open(self._path, "rb") as fh:
            return fh.read()


def _stored_files(files):
    return [_Stored(d) for d in files or []]


def _drop_files(files):
    if not files:
        return
    from django.core.files.storage import default_storage
    for d in files:
        try:
            default_storage.delete(d["path"])
        except Exception:  # noqa: BLE001
            logger.warning("zas: could not remove AI upload %s", d.get("path"))


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


# ───────────────────────────── chat and form fill (queued; the screen polls) ─────────────────────────────

def chat(code, obj, message, request, session_id=None, rows=None):
    """Queue one chat turn. Returns the run payload; when it is done its `result` is the answer and
    `session_id` the conversation to send with the next message."""
    a = agent(code)
    role = _payload_role(request)
    if not can_run(a, role):
        raise Denied(f"{role} may not use {a['name']}")
    r = run(code, obj=obj, trigger="chat", request=request, rows=rows, check=False,
            extra={"message": (message or "")[:2000], "session_id": session_id or None})
    return run_payload(r)


def form_assist(code, values, uploads, request):
    """Queue filling an unsaved form from its documents (kept in storage until the run is over).
    Returns the run payload; when it is done its `values` are {form field: value}. Nothing is saved."""
    a = agent(code)
    role = _payload_role(request)
    if not can_run(a, role):
        raise Denied(f"{role} may not use {a['name']}")
    r = run(code, trigger="form_assist", request=request, check=False,
            extra={"values": {k: _jsonable(v) for k, v in (values or {}).items()}, "files": _store_files(uploads) or None})
    return run_payload(r)


def call_tool(code, tool_name, tool_input, request=None, obj=None):
    """Test-only (POST ?action=zas_ai_tool, DEBUG): run one of a helper's tools the way a run of that
    helper would — through Zango's tool executor (input checked against the tool's schema, timeout),
    with acting() set: as `request`'s person and role, or as the system (request None: a task run).
    The fake AI never calls tools, so this is how tests reach them. Returns {status, output, error}."""
    a = agent(code)
    if tool_name not in (a.get("tools") or []):
        raise ValueError(f"{tool_name!r} is not one of {a['name']}'s tools ({', '.join(a.get('tools') or []) or 'none'})")
    from zango.ai.tools.executor import ToolExecutor
    role = _payload_role(request) if request is not None else ""
    req = request if request is not None else _RunRequest(None, "")
    token = _acting.set({"agent": a, "request": req, "role": role, "record": obj})
    try:
        res = ToolExecutor().execute(tool_name, dict(tool_input or {}))
    finally:
        _acting.reset(token)
    return {"status": res.status, "output": res.output, "error": res.error_message}


IN_REQUEST = ("{code} was called during a web request: an agent runs only in a background task. "
              "From a hook use run_later(\"{code}\", obj=…, then=\"<hooks.py function>\") (references/map/ai.md).")


def in_request():
    """True while Django is answering a web request (zango's middleware keeps the current request)."""
    try:
        from zango.core.utils import get_current_request
        return get_current_request() is not None
    except Exception:  # noqa: BLE001
        return False


def run_later(code, obj=None, then=None, variables=None, user=None):
    """From a hook that runs during a save: queue the helper and return the run at once. In the task,
    after the run, <module>/hooks.py::<then>(obj, res) gets the Result (any status) and does the
    rest (open the case, flag the record). user: who it is for (tools see them; the run is a system
    run, as from a task). Never raises."""
    try:
        agent(code)
    except KeyError as e:
        logger.error("zas: run_later: %s", e)
        return None
    inp = (variables or {}).get("input") if isinstance(variables, dict) else variables
    ZasAiRun, _ = _models()
    a = agent(code)
    r = ZasAiRun.objects.create(agent=code, entity=a.get("entity") or "", record_uuid=str(getattr(obj, "object_uuid", "") or ""),
                                trigger="task", status="queued",
                                inputs={k: v for k, v in {"input": inp, "then": then}.items() if v is not None},
                                created_by=user if getattr(user, "pk", None) and type(user).__name__ == "AppUserModel" else None)
    _enqueue(r)
    return r


def run_from_code(code, obj=None, variables=None, triggered_by="celery"):
    """For hand-written tasks (custom requirements with uses_ai): runs the helper now, in the task that
    calls it. Never inside a web request: there it returns a failed Result (use run_later). Never raises.

        res = run_from_code("invoice_triage", obj=invoice, variables={"input": email_text})
        if res.ok: ...res.result...        # dict for kind fields, text otherwise
        elif res.status == "unavailable":  # no AI account yet: carry on without it
    """
    if in_request():
        logger.error("zas: " + IN_REQUEST.format(code=code))
        return Result("failed", error=IN_REQUEST.format(code=code))
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
                run(a["code"], obj=obj, trigger=event, request=request, check=False,
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
                run(a["code"], trigger="schedule", check=False)
                n += 1
                continue
            qs = zs.model(a["entity"]).objects.all()
            if t.get("when_ast") is not None:
                qs = qs.filter(zx.to_q(t["when_ast"], qs.model, {}))
            for obj in qs.order_by("id")[:limit]:
                run(a["code"], obj=obj, trigger="schedule", check=False)
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
        # query the model, not r.suggestions: Zango reloads app models, so the reverse accessor may be missing
        s = _models()[1].objects.filter(run_id=r.pk, status="pending").first() if r.pk else None
        sugg = suggestion_payload(s) if s else None
    labels = {f["key"]: f.get("label") or f["key"] for f in a["output"].get("fields") or []}
    result = r.result
    if a["output"]["kind"] == "fields" and isinstance(result, dict):
        result = [{"key": k, "label": labels.get(k, k), "value": v} for k, v in result.items()]
    out = {"id": r.pk, "agent": r.agent, "name": a["name"], "status": r.status, "trigger": r.trigger,
           "kind": a["output"]["kind"], "result": result, "error": r.error, "applied": r.applied,
           "suggestion": sugg, "record_uuid": r.record_uuid or None}
    if r.trigger == "chat":
        out["session_id"] = (r.inputs or {}).get("session_out") or (r.inputs or {}).get("session_id")
    if r.trigger == "form_assist":
        out["values"] = ({k: _jsonable(v) for k, v in writes(a, r.result).items()}
                         if r.status == "done" and a.get("output", {}).get("kind") else {})
    return out


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
