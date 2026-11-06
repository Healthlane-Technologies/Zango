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
| The AI account `app-llm` (service and model from `ai.provider`, **no key**) | platform, before `zango_platform.py ai` | App → AI → Providers |
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

## Calling a helper from code (`uses_ai`)

A custom requirement that lists `uses_ai: [<code>]` gets the helper's inputs and answer in its hole
text. Call it inside that hole's function. The call is synchronous and never raises:

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

`--audit-holes` fails if the hole's file never calls `run_from_code("<code>"…)`.

## When it runs (runtime; nothing to write)

| Trigger | Runs from | Mode | Where the answer goes |
|---|---|---|---|
| `create`, `update` (`fields`), `transition`, `tag`, `delete` | the form save / workflow `done` / tag `done` / delete row action | Celery task `zas_ai_run` | `review: none` writes it; `suggest` makes a suggestion card; `show` keeps it on the run |
| `schedule` (`cron`) | `zas_ai_tick` (every minute, scheduled only when a helper has a schedule) | Celery | the same |
| `button` (`where: record`/`row`/`list`) | `POST ?action=zas_ai_run` | `run` (async by default): the screen polls `?action=zas_ai&run=<id>` | the same; a list button answers in a dialog |
| `button` with `where: form`, `form_assist` | `POST ?action=zas_ai_form` | inline | the form is reloaded with the values (`zas_prefill`); nothing is saved |
| `chat` | `POST ?action=zas_ai_chat` with `session_id` | inline | the chat panel |
| `task` | `run_from_code()` in your hole | inside your task | the return value |

- **Loop guard.** AI writes fire no triggers.
- **Who can run it and see the answer.** The helper's `roles`. A trigger's `roles` narrows that for
  clicks.
- **Unavailable runs.** A placeholder account, a missing key, an agent that is switched off, or an
  account over budget ends the run as `unavailable`. Users see "AI isn't set up for this app yet",
  and saving still works.

## Testing (fake AI)

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

## Platform step (for reference)

`zango_platform.py ai` runs after `sync` and does four things:
1. It checks that the account exists. If it doesn't, the build creates it first, through the ORM.
2. It syncs tools, and fails if a tool the spec lists is still not registered.
3. It uploads prompts, and fails if a prompt file is missing or empty.
4. It creates or updates the agents:
   - A new agent gets the provider, model, temperature, max tokens and timeout once. Those belong
     to the creator afterwards.
   - Later runs update only the description, prompts, output format and schema, tools and memory,
     and only when they changed.

`.zas/ai_state.json` records what was sent, so a re-run with no changes does nothing.
