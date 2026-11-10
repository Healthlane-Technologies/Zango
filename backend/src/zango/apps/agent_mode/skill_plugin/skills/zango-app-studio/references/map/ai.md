# AI helpers: spec `ai` → prompts, tools and Zango agents

A spec's `ai.agents` are AI helpers. The runtime (`zas_core/ai.py`, `tools.py`, `tasks.py` and the
React parts in `src/zas/ai.tsx`) does everything that is the same in every app:
- runs a helper when its trigger fires;
- sends only the fields the spec lists;
- holds a suggestion until a person accepts it;
- answers "not connected" when the app has no AI key yet.

The platform creates the Zango objects. **You write only three things:** the prompts, custom tools,
and the hand-written tasks that call a helper (`uses_ai`). Never write trigger code, polling, endpoints
or result handling.

## Who does what

| Part | Who | Where |
|---|---|---|
| The AI account `app-llm`: linked to the platform's default AI account when one is set up, otherwise a placeholder with the service and model from `ai.provider` and **no key** | platform, before `zango_platform.py ai` | App → AI → Providers |
| The instructions: one `ai_prompt` hole per helper | **you** | `backend/<module>/ai/<code>.system.md`, `.user.md` |
| Custom tools: one `ai_tool` hole per `tools[].code` | **you** | `backend/<module>/tools.py` |
| Calls from hand-written code (`uses_ai` on a custom requirement) | **you**, inside that requirement's hole | `run_from_code("<code>", …)` |
| Uploading prompts, syncing tools, creating the agents | platform: `zango_platform.py ai` | App → AI |
| Triggers, runs, suggestions, chat, form fill, the buttons and cards | runtime | `zas_core/ai.py`, `src/zas/ai.tsx` |

`spec.resolved.json` `ai.agents[]` has everything resolved:
- `zango_name`: the agent's name in Zango;
- `prompts`: name, file, and the variables each prompt may use;
- `output`: `format` and `json_schema`;
- `tools`, `roles`, `run`, `memory`;
- `sample`: the answer the preview and the fake AI give.

## Prompts (`ai_prompt` holes)

Write the files the hole names. Start the system prompt with the marker as an HTML comment. The
platform strips comments before upload, so the marker never reaches the AI:

```markdown
<!-- zas:hole H-41 -->
You screen new vendors for a procurement team in India. Rate the vendor's risk as low, medium or high
from the details below. Rate high when GSTIN or PAN is missing for a manufacturer, or when the credit
limit is unusually large for the category. Give two or three short bullets explaining why.
Use only the details given. Never invent a value; if something is missing, say so.
Today is {{today}}.
```

```markdown
Vendor:
{{record}}
```

- **Variables.** Use only the ones listed in the hole: `{{today}}`, `{{role}}`, `{{record}}`, `{{records}}`,
  `{{related}}`, `{{input}}`. `--audit-holes` fails on any other variable, and on a prompt that never uses
  its data variable (the AI would not see the record).
- **What the variables contain.**
  - `{{record}}`: one `Label: value` line per `context.fields`.
  - `{{related}}`: a block per `context.related`.
  - `{{records}}`: the rows on screen (list buttons).
  - `{{input}}`: what hand-written code passes.
  - Files are attached, not inlined.
- **Answer shape.** A `fields` answer is JSON. The runtime asks Zango for the hole's JSON schema, so
  name the keys in the prompt only to explain them; don't repeat the schema. For `text` and
  `markdown`, say how long the answer should be and in what form.
- **Tools.** When the helper has `tools`, the system prompt says when to call each one, in what
  order, and what to do with the answer: "First call find_patient with the name, date of birth and
  phone as written. Reuse a candidate only when the date of birth or phone also agrees; when you are
  not sure, call no write tool and say why in missing_info. Otherwise call open_case." Zango gives the
  AI each tool's description; the prompt gives the business rule for using them.
- **Chat helpers have only a system prompt.** The person's question is the user message. Put
  `{{record}}` and `{{related}}` in the system prompt.
- **Domain voice.** Write what an expert in this business would tell a new colleague: what counts as
  high risk, which wording is allowed, what to do when unsure ("say unknown"). Write it from
  `purpose`, `instructions` and the acceptance lines. No "As an AI", and no prompt tricks.
- **Re-runs.** The platform uploads a prompt again only when its file changed, and makes that version
  live. Edits the creator made in the console stay until the file changes.

## Custom tools (`ai_tool` holes)

```python
from zango.ai.tools.decorator import ToolParam, ToolSafety, tool
from ..zas_core import ai as zai


# zas:hole H-44
@tool(name="gst_lookup", description="Look up a GSTIN: legal name, status and state. Use it to check the vendor's GSTIN.",
      section="vendors", safety=ToolSafety.EXTERNAL)
def gst_lookup(gstin: str = ToolParam(description="The 15-character GSTIN")) -> dict:
    """Spec: ai.agents.vendor_screening.tools.gst_lookup: Look up a GSTIN on the GST portal."""
    act = zai.acting()          # {agent, request, role} while a helper runs; None otherwise
    ...
    return {"legal_name": ..., "status": ...}
```

- **Naming.** `name=` is the tool code from the spec. The `description` is written for the AI.
- **Safety.** Use the safety the hole gives.
- **Return value.** Return a small dict. Never return files, passwords or other people's records.
- **Scoping.** Read records through the acting person's scope:
  `access.scope_queryset("<entity>", qs, zai.acting()["request"])`. The built-in `zas_search_records`
  and `zas_read_record` already do this (`zas_core/tools.py`), so never rewrite them.

### A tool is plain app code

The body is ordinary Django code in the app: it can query, create or update records, move a record
through its workflow, set a tag, or call an outside service. The AI only chooses when to call it and
with which arguments; what happens is your code. Write it the way the app's own screens would do it,
so a record a tool makes is the same as one a person makes: right status, right owner, on the timeline.

**Who it runs as.** `zai.acting()` is `{agent, request, role, record}` while a helper runs (None
otherwise: answer `{"error": ...}`).

| Run started by | `request.user` | `role` | Rules to apply |
|---|---|---|---|
| a person (button, chat, form fill) | that person | their role | that role's access, rows and transition roles |
| a trigger after a person's save or move (`create`, `transition`, ...) | that person | their role | the same |
| code (`task`, `uses_ai`) or `schedule` | None | `""` | none: it acts as the system, like the hook that called it |

`record` is the model instance the helper is working on (the prescription it reads, the vendor it
screens); None for list buttons and form fill. Use it instead of asking the AI for an id.

**Starter for a tool file:**

```python
from zango.ai.tools.decorator import ToolParam, ToolSafety, tool

from ..zas_core import access, demo
from ..zas_core import ai as zai
from ..zas_core import expr as zx
from ..zas_core import spec as zs
from ..zas_core.mixins import fake_request, run_system_transition
from .models import Patient, PatientCase   # this module's models (custom-code.md, Imports)
# another module's model: import it inside the function (`from ..masters.models import City`) or
# skip the import with zs.model("<entity code>") — any entity, by its spec code


def _ctx():
    """(act, user, role) of the running helper, or raise ToolError for the AI to read."""
    act = zai.acting()
    if not act:
        raise ToolError("This tool only works inside one of the app's AI helpers.")
    return act, getattr(act["request"], "user", None), act["role"]


class ToolError(Exception):
    pass
```

Catch `ToolError` (and any other failure) in each tool and return `{"error": "<what went wrong, in
plain words>"}`: the AI reads it and can say so or try again. A tool never raises.

**Read records** (as the person, or every row for a system run):

```python
# zas:hole H-51
@tool(name="find_patient", description="Find existing patients by name; also give date of birth and phone when "
      "the prescription shows them. Returns candidates with an id and how well each matches.",
      section="intake", safety=ToolSafety.READ_ONLY)
def find_patient(name: str = ToolParam(description="Patient name as written"),
                 dob: str = ToolParam(description="Date of birth YYYY-MM-DD, or empty", default=""),
                 phone: str = ToolParam(description="Phone as written, or empty", default="")) -> dict:
    try:
        act, user, role = _ctx()
        qs = Patient.objects.all()
        if role:
            qs = access.scope_queryset("patient", qs, act["request"])
        from ..zas_core import dupes
        out = []
        for p in qs.order_by("-id")[:500]:
            score = dupes.dice(name, p.full_name)
            if score >= 0.75:
                out.append({"id": str(p.object_uuid), "code": p.patient_code, "name": p.full_name,
                            "dob": str(p.date_of_birth or ""), "phone": str(p.phone or ""), "name_match": round(score, 2)})
        return {"candidates": sorted(out, key=lambda x: -x["name_match"])[:5]}
    except Exception as e:  # noqa: BLE001
        return {"error": str(e)[:300]}
```

**Create a record.** Check the role may add it, save, give it its first workflow status, then set
the owner (zango's `pre_save` writes `created_by` from the request, and there is none here, so it
comes out empty unless you set it after the last save):

```python
def _create(entity, values, user, role, owner=None):
    """owner: who the record belongs to; defaults to the person running the helper."""
    if role and not access.can(entity, "add", role=role):
        raise ToolError(f"{role} may not add a {zs.entity(entity)['name']}.")
    obj = zs.model(entity)(**values)
    obj.save()                                   # sequences (CS-00012) and computed fields happen here
    WF = zs.workflow_class(entity)
    if WF is not None:                           # the first status; the crud view does this for a person
        WF(request=fake_request(user), object_instance=obj).execute_transition(WF.Meta.on_create_status)
    demo.stamp(obj, created_by=owner or user)    # the owner; after the last save()
    return obj
```

For a system run (`user` None) pass the owner the screens expect, usually the owner of the record
the helper works on: `_create("patient_case", {...}, None, "", owner=act["record"].created_by)`
(a case opened from a prescription belongs to whoever uploaded it).

**Change fields.** Check the role may edit and can see the record, then save:

```python
def _update(entity, obj, values, role, request):
    if role and not (access.can(entity, "edit", role=role) and access.in_scope(entity, obj, request)):
        raise ToolError("Not allowed to change this record.")
    for k, v in values.items():
        setattr(obj, k, v)
    obj.save()
```

**Move it through the workflow.** For a person, only a transition their role has and whose
condition holds, exactly as the button would; for a system run, `run_system_transition` (it also
runs `system: true` transitions). Both put the move on the timeline with the actor:

```python
def _move(entity, obj, name, user, role):
    if not role:
        ok, msg = run_system_transition(entity, obj, name, user=user)
    else:
        t = next((x for x in zs.entity(entity)["workflow"]["transitions"] if x["name"] == name), None)
        status = zx.current_status(obj)
        if t is None or t.get("system") or status not in t["from"] or (t.get("roles") and role not in t["roles"]):
            raise ToolError(f"{role} cannot {name} a record that is {status}.")
        engine = next(e["name"] for e in t["engine"] if e["from"] == status)
        wf = zs.workflow_class(entity)(request=fake_request(user), object_instance=obj)
        if not wf.is_transition_allowed(engine, current_status=status):
            raise ToolError(t.get("condition_msg") or "Not available right now.")
        ok, msg = wf.execute_transition(engine, allow_system=False)
    if not ok:
        raise ToolError(msg)
```

A transition with a `form` needs its fields: set them on the record before the move (or pass them as
the form data your `on_done` hook reads).

**Call an outside service** (`safety: external`): a timeout (10 s), no secrets in the answer, and
`{"error": ...}` when the service is down.

**Also:**
- **Call twice, act once.** The AI may repeat a call. Before creating, look for what an earlier call
  made (`PatientCase.objects.filter(prescription=act["record"]).first()`) and return it instead.
- **Say what happened.** Return the id and the code/name the screens show (`{"id": ..., "code":
  "CS-00012", "created": true}`), so the AI can report it and pass the id to the next tool.
- **No side effects a person's save would have.** A tool's save does not run the entity's
  triggers, custom-requirement hooks or notifications (they run from the crud view). Call the one you
  need explicitly, or leave it to the code that called the helper.
- **Keep the AI's notes.** When the record has an AI log field, append what the tool did there too.
- **Write in one place.** When a hook and a tool do the same work (open a case), put it in one
  function in the module and call it from both.

## Calling a helper from code (`uses_ai`)

**An agent never runs inside a web request.** Every call happens in a Celery task and the screen
polls the run. The runtime enforces it: `run_from_code` returns a failed Result during a request, and
`--audit-holes` checks that a hole fired by a save uses `run_later`. The hole text says which one.

**From a hook that runs during a save** (`create`, `update`, `transition`, `tag` triggers): queue the
helper with `run_later` and finish the work in a `then` function. The save returns at once; the task
calls the agent, then `then(obj, res)` with the Result (whatever its status):

```python
from ..zas_core.ai import run_later, run_from_code


# zas:hole H-05
def prescription__req__1(request, obj):
    """Runs on upload: show "AI reading" and let the background task do the rest."""
    run_system_transition("prescription", obj, "start_reading")
    run_later("prescription_reader", obj=obj, then="prescription__req__1__after_ai",
              variables={"input": "..."}, user=request.user)


def prescription__req__1__after_ai(obj, res):
    """In the task, after the reader: open the case, or send the prescription to review."""
    if res.status == "unavailable":            # no AI account yet: leave it for a person
        return
    if res.ok:
        ...res.result["drug"]...
```

- `then` is a function name in the same module's `hooks.py`. It runs in the worker, so it may take its
  time and may call `run_from_code` for a second helper.
- `user` is who the run is for: tools see them, and records it makes can belong to them.
- The record shows its progress: a status like "AI reading" and the record page's running-AI strip
  (it polls `?action=zas_ai`) until the run is done; then the page reloads.

**Inside a task** (a `schedule` requirement, a sweep in `tasks.py`, a `then` function): the work is
already in the background, so call the helper directly. The call is synchronous and never raises:

```python
from ..zas_core.ai import run_from_code


# zas:hole H-17
@shared_task
def app__req__1():
    n = 0
    for inv in Invoice.objects.filter(...):
        res = run_from_code("invoice_triage", obj=inv, variables={"input": inv.email_body})
        if res.status == "unavailable":      # no AI account yet: leave it for a person
            continue
        if res.ok:
            ...res.result["queue"]...        # dict for kind fields, text otherwise
            n += 1
    return n
```

`--audit-holes` fails if the hole's file never calls the function its text names (`run_later(...)` for
a hole fired by a save, `run_from_code(...)` for a scheduled one).

## When it runs (runtime; nothing to write)

| Trigger | Runs from | Mode | Where the answer goes |
|---|---|---|---|
| `create`, `update` (`fields`), `transition`, `tag`, `delete` | the form save / workflow `done` / tag `done` / delete row action | Celery task `zas_ai_run` | `review: none` writes it; `suggest` makes a suggestion card; `show` keeps it on the run |
| `schedule` (`cron`) | `zas_ai_tick` (every minute, scheduled only when a helper has a schedule) | Celery | the same |
| `button` (`where: record`/`row`/`list`) | `POST ?action=zas_ai_run` | Celery; the screen polls `?action=zas_ai&run=<id>` | the same; a list button answers in a dialog |
| `button` with `where: form`, `form_assist` | `POST ?action=zas_ai_form` (the files wait in storage for the task) | Celery; the form polls | the form is reloaded with the run's `values` (`zas_prefill`); nothing is saved |
| `chat` | `POST ?action=zas_ai_chat` with `session_id` | Celery; the chat polls | the chat panel; the run's `session_id` goes with the next message |
| `task` | `run_later()` in a hook, or `run_from_code()` in a task | Celery (`run_later`), or inside your task | `then(obj, res)`, or the return value |

Nothing runs inside the request: a request only creates the run (`ZasAiRun`, `queued`) and returns it.
If the worker cannot be reached the run ends `failed` ("Try again in a minute"); it is never run in
the request instead. So Celery must be running for any AI to answer.

- **Loop guard.** AI writes fire no triggers.
- **Who can run it and see the answer.** The helper's `roles`. A trigger's `roles` narrows that for
  clicks.
- **Unavailable runs.** A placeholder account, a platform account that is off or failing, a missing key, an agent that is switched off, or an
  account over budget ends the run as `unavailable`. Users see "AI isn't set up for this app yet",
  and saving still works.

## Testing (fake AI)

On a local Claude subscription account the AI does call the agent's tools, and they run for real (through the platform's tool runner, as with an API key), so keep scenario data disposable.

The scenarios must never call the real AI. Use the spec's `preview.sample`, or your own answer:

```python
@scenario("H-41", "submitting a vendor suggests a risk rating the manager can accept")
def screening(ctx):
    with ctx.ai_fake({"vendor_screening": {"risk_rating": "high", "reasons": "- GSTIN missing"}}):
        v = ctx.record_in("vendor", "draft")
        ctx.run("vendor", v, "Procurement Executive", "submit")
        ...  # the background run needs Celery; or click: ctx.ai_run("vendor", v, "Procurement Manager", "vendor_screening")
        p = ctx.ai_pending("vendor", v, "Procurement Manager")
        ctx.expect(p["suggestions"], "no suggestion")
```

- **How the fake works.** `ctx.ai_fake` writes `.zas/ai_fake.json`, which the running server honours
  under DEBUG only, and removes it afterwards.
- **What to cover.** Test each acceptance line and the roles: a role outside `roles` gets 403 on
  `zas_ai_run`, and a suggestion changes nothing until it is accepted.

**Tools (`ai_tool` holes).** The fake AI answers at once and never calls a tool, so call each tool
yourself with `ctx.ai_tool(agent, tool, args, role=None, record=None)`. It runs the tool through
Zango's tool executor, exactly as a run of that helper would: the input is checked against the tool's
schema, and `acting()` is set.
- `role="Intake Associate"` runs it as that person (their access and rows); `role=None` runs it as
  the system, like a `task` or `schedule` run.
- `record=<uuid>` of the helper's entity becomes `acting()["record"]`.
- It returns the tool's dict. A tool that is not on the helper, a refused role, or input that does not
  fit the schema raises `AssertionError`.

```python
@scenario("H-51", "find_patient finds a spelling variant, and only the associate's own patients")
def find_patient(ctx):
    rx = ctx.record_in("prescription", "case_created")
    name = ctx.field("prescription", rx, "patient_name")
    got = ctx.ai_tool("prescription_reader", "find_patient", {"name": name.replace(" ", "  ") + "."}, record=rx)
    ctx.expect(got["candidates"] and got["candidates"][0]["name_match"] >= 0.9, f"no close match: {got}")
    mine = ctx.ai_tool("prescription_reader", "find_patient", {"name": name}, role="Intake Associate")
    ctx.expect("error" not in mine, mine)
```

For a write tool, assert what it changed through the API as a person would see it: the record exists
for its owner (`ctx.record`), its status (`ctx.status_of`), and that calling it twice made one record.
Needs DEBUG on the server, like the fake AI; the action (`?action=zas_ai_tool`) answers 404 otherwise.

## Platform step (for reference)

`zango_platform.py ai` runs after `sync` and does four things:
1. It checks that the account exists. If it doesn't, the build creates it first, through the ORM:
   linked to the platform's default AI account (Platform → Settings → AI accounts) when there is a
   working one, so the AI works from the first build; otherwise a placeholder that waits for a key.
   A placeholder from an earlier build is linked as soon as a platform default exists. The model
   the agents get is the account's `default_model`, so never assume the spec's model in a prompt.
2. It syncs tools, and fails if a tool the spec lists is still not registered.
3. It uploads prompts, and fails if a prompt file is missing or empty.
4. It creates or updates the agents:
   - A new agent gets the provider, model, temperature, max tokens and timeout once. Those belong
     to the creator afterwards.
   - Later runs update only the description, prompts, output format and schema, tools and memory,
     and only when they changed.

`.zas/ai_state.json` records what was sent, so a re-run with no changes does nothing.
