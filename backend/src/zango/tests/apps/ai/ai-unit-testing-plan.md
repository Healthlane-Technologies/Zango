# AI Module — Test Plan

## Principles

**Mock at the boundary, not inside it.**
The boundary is where our code calls an external system (LLM API, Celery, workspace
plugin loader). Everything above that boundary is tested with real logic against
deterministic mock responses. We never mock our own classes.

**Two test tiers, clearly separated.**

| Tier | Base class | DB | Workspace | Purpose |
|---|---|---|---|---|
| Unit | `SimpleTestCase` | No | No | Pure logic — math, schema gen, dataclass transforms, message building |
| Integration | `ZangoAppBaseTestCase` | Yes (tenant schema) | Yes (copied fixture) | `sync_tools`, `ToolExecutor.execute()`, tool calling real models |

**Follow the existing Zango test pattern exactly.**
- Integration tests live under `tests/apps/ai/<test_folder>/`
- Each integration test folder carries its own `workspace/` fixture and `migrations/`
- `initialize_workspace = True` + `get_test_module_path()` is the entry point
- `ws_migrate` is called to bring the tenant schema up before assertions

---

## Directory Layout

```
backend/src/zango/tests/apps/ai/
├── __init__.py
│
├── test_tool_decorator.py          ← DONE (29 tests, SimpleTestCase, no DB)
│
├── test_cost.py                    ← SimpleTestCase, no DB
├── test_llm_file.py                ← SimpleTestCase, no DB
├── test_tool_executor.py           ← SimpleTestCase, mocked DB + workspace
├── test_provider_client.py         ← SimpleTestCase, mocked DB
├── test_agent_client.py            ← SimpleTestCase, mocked DB
│
└── test_tool_sync_and_exec/        ← ZangoAppBaseTestCase, real DB + workspace
    ├── __init__.py
    ├── tests.py
    ├── migrations/
    │   ├── __init__.py
    │   └── 0001_initial.py         ← creates Patient table in tenant schema
    └── workspace/
        ├── manifest.json
        ├── settings.json
        └── ai_test_module/
            ├── models.py           ← Patient(DynamicModelBase)
            └── tools.py            ← @tool functions that query/write Patient
```

---

## Test Files

### 1. `test_cost.py` — Cost computation (SimpleTestCase)

**Covers:** `zango.ai.cost.compute_cost` and `compute_anthropic_cost`.
Pure arithmetic. No dependencies.

| # | Test | What is verified |
|---|---|---|
| 1 | Zero tokens → zero cost | `compute_cost` with `input=0, output=0` returns `0.0` |
| 2 | Standard input+output pricing | 1M input @ $3 + 1M output @ $15 = `18.0` |
| 3 | Input-only cost | Only `output_tokens=0` — only input rate applied |
| 4 | Output-only cost | Only `input_tokens=0` — only output rate applied |
| 5 | Rounding to 6 decimal places | Fractional tokens don't produce float noise beyond 6dp |
| 6 | Missing rate key defaults to zero | `model_info` without `input_cost_per_mtok` → no `KeyError`, returns partial cost |
| 7 | Anthropic cache read discount | 1M `cache_read_tokens` @ $3 × 0.1 = `0.3` |
| 8 | Anthropic cache creation surcharge | 1M `cache_creation_tokens` @ $3 × 1.25 = `3.75` |
| 9 | Anthropic all four token types combined | `input + output + cache_create + cache_read` sums correctly |
| 10 | Anthropic zero cache tokens | Cache fields default `0` → no contribution to cost |

---

### 2. `test_tool_decorator.py` — `@tool` decorator (SimpleTestCase) ✓ Done

**Covers:** Schema generation and `_tool_meta` population at decoration time. No DB.
Already implemented — 29 tests passing.

**Schema generation (15 tests):**
`int→integer`, `str→string`, `bool→boolean`, `float→number`, `list[int]→array{items:integer}`,
`dict→object`, `Optional[str]→string` (unwrapped), `required` populated for params without default,
`required` empty for params with default, mixed required/optional, `enum` propagated,
`description` on property, `schema_hash` changes on type change, changes on required→optional,
stable for identical signatures.

**Meta fields (14 tests):**
`name`, `description`, `section` default + custom, `safety` default (`READ_ONLY`) + custom,
`timeout_seconds` default + custom, `rate_limit` default (`None`) + custom, `return_type` set
for annotated return, `None` for unannotated, `python_path` ends with function name, decorated
function still callable.

---

### 3. `test_llm_file.py` — `LLMFile` dataclass (SimpleTestCase)

**Covers:** All named constructors and both provider serializers. Pure Python, no I/O.

| # | Test | What is verified |
|---|---|---|
| 1 | `from_bytes` — all fields set | `data`, `media_type`, `filename` stored correctly |
| 2 | `from_bytes` — no filename | `filename=None` when omitted |
| 3 | `from_url` — media_type guessed from extension | `.jpg` → `image/jpeg` |
| 4 | `from_url` — explicit media_type wins | Explicit value not overridden by guess |
| 5 | `from_url` — unknown extension gets fallback | `application/octet-stream` when extension unrecognised |
| 6 | Anthropic block — bytes image | `type=image`, `source.type=base64`, correct b64 data, `media_type` in source |
| 7 | Anthropic block — bytes PDF | `type=document` (not image) — `is_image` gate works |
| 8 | Anthropic block — public URL image | `source.type=url`, url preserved, `type=image` |
| 9 | Anthropic block — public URL PDF | `source.type=url`, `type=document` |
| 10 | Anthropic block — `file-id://` image | `source.type=file`, `file_id` extracted, `type=image` |
| 11 | Anthropic block — `file-id://` document | `source.type=file`, `type=document` |
| 12 | OpenAI block — bytes | `type=image_url`, `url` starts with `data:<media_type>;base64,` |
| 13 | OpenAI block — public URL | `type=image_url`, url passed through unchanged |
| 14 | `build_content_for_anthropic` — files + str content | File blocks prepended, text appended as `text` block |
| 15 | `build_content_for_anthropic` — files + list content | File blocks prepended, existing blocks extended |
| 16 | `build_content_for_anthropic` — no files | Content returned unchanged |
| 17 | `build_content_for_openai` — files + str content | Same pattern, OpenAI blocks |

---

### 4. `test_tool_executor.py` — `ToolExecutor` (SimpleTestCase, mocked)

**Covers:** Each safety layer of the executor independently. DB and workspace mocked;
only our logic runs.

**4a. Input validation** (`_validate_input` — no mocking):

| # | Test | Input | Expected |
|---|---|---|---|
| 1 | Valid input passes | `{"employee_id": 42}` vs integer schema | `None` returned |
| 2 | Wrong type caught | `{"employee_id": "abc"}` | error string returned |
| 3 | Missing required field | `{}` vs required `employee_id` | error string returned |
| 4 | Extra field allowed | `{"employee_id": 1, "extra": true}` | `None` — `additionalProperties` not restricted by default |
| 5 | Broken schema handled | `schema={"type": "invalid_xyz"}` | error string, no crash |

**4b. Output serialization** (`_serialize_output` — no mocking):

| # | Test | Input | Expected output |
|---|---|---|---|
| 6 | `None` | `None` | `None` |
| 7 | `str` | `"hello"` | `"hello"` (identity) |
| 8 | `int` | `42` | `42` (identity) |
| 9 | `float` | `3.14` | `3.14` (identity) |
| 10 | `bool` | `True` | `True` (identity — not cast to int) |
| 11 | `Decimal` | `Decimal("9.99")` | `9.99` as `float` |
| 12 | `datetime` | `datetime(2024,1,15,12,0,0)` | `"2024-01-15T12:00:00"` |
| 13 | `date` | `date(2024,1,15)` | `"2024-01-15"` |
| 14 | `set` | `{1, 2, 3}` | list of same elements |
| 15 | `bytes` | `b"abc"` | base64-encoded ASCII string |
| 16 | Large output > 50 000 chars | `{"key": "x" * 60_000}` | JSON truncated to ≤ 50 000 chars |
| 17 | Non-serializable fallback | custom object with no `__json__` | `str(value)[:2000]` |

**4c. Execution paths** (DB + workspace mocked via `patch`):

| # | Test | Setup | Assertion |
|---|---|---|---|
| 18 | Tool not in DB | `AppLLMTool.objects.get` raises `DoesNotExist` | `status="error"`, `"not found"` in `error_message` |
| 19 | Workspace import fails | `plugin_source.load_plugin` raises | `status="error"`, `"import failed"` in `error_message` |
| 20 | `getattr` of function fails | module loaded but attribute missing | `status="error"` |
| 21 | Input validation fails before execution | Wrong param type | `status="validation_error"`, function never called |
| 22 | Successful execution — dict return | Function returns `{"score": 95}` | `status="success"`, `output={"score": 95}` |
| 23 | Successful execution — int return | Function returns `42` | `status="success"`, `output=42` |
| 24 | Function raises `ValueError` | Function raises at runtime | `status="error"`, `error_traceback` is set |
| 25 | `execution_time_ms` always set | Any outcome | Field is a non-negative integer |

---

### 5. `test_provider_client.py` — `ProviderClient` (SimpleTestCase, mocked)

**Covers:** Every framework concern layered around the raw provider. Raw provider is mocked
via `patch`; `AppLLMInvocation` is patched to avoid DB writes.

**5a. Model resolution and access control:**

| # | Test | Setup | Assertion |
|---|---|---|---|
| 1 | `model=None` → default model used | `default_model` set on provider | Raw client called with `default_model` |
| 2 | Explicit model passed through | `model="gpt-4o"` | Raw client called with `"gpt-4o"` |
| 3 | No `enabled_models` records → any model allowed | `enabled_models.exists()=False` | No `ModelNotAvailable` raised |
| 4 | Model in `enabled_models` → allowed | `filter(...).exists()=True` | No exception |
| 5 | Model NOT in `enabled_models` → blocked | `enabled_models.exists()=True`, `filter.exists()=False` | `ModelNotAvailable` raised before raw call |

**5b. Success path:**

| # | Test | Assertion |
|---|---|---|
| 6 | `response.cost_usd` set from `compute_cost` | Value from `raw.compute_cost()`, not from raw response |
| 7 | `response.invocation_id` set from created invocation PK | `invocation.pk` attached to returned response |
| 8 | `provider.record_usage()` called | Side-effect on provider usage counters |
| 9 | Invocation log failure doesn't crash caller | `AppLLMInvocation.objects.create` raises → response still returned, `invocation_id=None` |

**5c. Error paths and status mapping:**

| # | Test | Exception raised by raw provider | `status` written to invocation log |
|---|---|---|---|
| 10 | `RateLimitExceeded` | `RateLimitExceeded` | `"rate_limited"` |
| 11 | `LLMTimeoutError` | `LLMTimeoutError` | `"timeout"` |
| 12 | `BudgetExceeded` | `BudgetExceeded` | `"budget_exceeded"` |
| 13 | Generic `Exception` | `RuntimeError("oops")` | `"error"`, re-raised as `LLMAPIError` |
| 14 | All error paths still write invocation log | Any above | `AppLLMInvocation.objects.create` called once |
| 15 | All error paths still re-raise | Any above | Exception propagates to caller |

**5d. Message + tool serialization (for logging):**

| # | Test | Input | Assertion |
|---|---|---|---|
| 16 | `LLMMessage` serialized correctly | `LLMMessage(role="user", content="hi")` | Dict with `role` + `content` |
| 17 | `LLMMessage` with `tool_calls` included | Message with `tool_calls` set | `tool_calls` key in serialized output |
| 18 | `LLMToolDef` serialized correctly | `LLMToolDef(name, description, input_schema)` | Dict with all three keys |
| 19 | `tools=None` serialized as `None` | No tools passed | `request_tools=None` in log |

---

### 6. `test_agent_client.py` — `AgentClient` (SimpleTestCase, mocked)

**Covers:** All orchestration logic. `ProviderClient` and `ToolExecutor` patched;
only `AgentClient`'s own code runs.

**6a. Guard checks:**

| # | Test | Setup | Assertion |
|---|---|---|---|
| 1 | `is_enabled=False` → `AgentDisabled` | Before any provider call | Exception raised immediately |
| 2 | `provider=None` → `ValueError` | Before any provider call | Exception raised immediately |
| 3 | No input + empty prompt + no messages → `ValueError` | `get_user_prompt_content=""`, no `input=`, no `messages=` | Clear error, no silent no-op |

**6b. Input resolution (priority: `messages` > `input` > `variables`):**

| # | Test | Call | Expected message content |
|---|---|---|---|
| 4 | `input=` used directly | `run(input="hello")` | Single user message, content=`"hello"` |
| 5 | `input=` wins over `variables=` | `run(input="hi", variables={"x":1})` | Content=`"hi"`, `get_user_prompt_content` NOT called |
| 6 | `variables=` renders template | `run(variables={"x":1})` | `get_user_prompt_content(x=1)` called |
| 7 | `messages=` passed directly | `run(messages=[LLMMessage(...)])` | Used as-is, no template rendering |
| 8 | `files=` only (no text) | `run(variables={})` with empty prompt + files | User message with `content=""` and files attached |
| 9 | `files=` + `messages=` — attached to last user message | Explicit messages + files | Files appended to last `role=user` message |
| 10 | `files=` + `messages=` — no user message → new one appended | All messages are `role=assistant` | New user message with files created |

**6c. System prompt rendering:**

| # | Test | Setup | Assertion |
|---|---|---|---|
| 11 | `system_prompt=None` → no system arg | Agent without system prompt | `system=None` passed to `ProviderClient.complete` |
| 12 | `system_prompt` set → rendered and forwarded | `get_system_prompt_content` returns text | That text passed as `system=` |

**6d. Output format:**

| # | Test | Setup | Assertion |
|---|---|---|---|
| 13 | `output_schema=None` → no `response_format` kwarg | Default agent | `response_format` not in kwargs to `complete` |
| 14 | `output_schema="JSON"` + no schema → `response_format="json"` | Agent with JSON mode, no schema | `response_format="json"` passed |
| 15 | `output_schema="JSON"` + schema dict → dict forwarded | Agent with `output_json_schema` set | That dict passed as `response_format` |

**6e. Agentic loop:**

| # | Test | Setup | Assertion |
|---|---|---|---|
| 16 | No tools → single LLM call | `stop_reason="end_turn"` | `complete()` called exactly once |
| 17 | One tool call → execute → second LLM call | Round 1: `tool_use`; round 2: `end_turn` | `complete()` × 2; `executor.execute()` × 1 |
| 18 | Two tool calls in one round | Round 1: two tool_calls | `executor.execute()` called twice |
| 19 | Two sequential rounds of tools | Rounds 1→2: `tool_use`; round 3: `end_turn` | `complete()` × 3 |
| 20 | Max rounds safety | LLM always returns `tool_use` | `complete()` count ≤ `max_tool_rounds + 1` |
| 21 | Tool result fed back into next round | Round 1 tool call | Round 2 messages include the tool result |
| 22 | Tool error result fed back | Tool returns `status="error"` | Error message forwarded to LLM, loop continues |
| 23 | Total cost = sum across all rounds | 2 rounds @ $0.001 | `agent.record_usage(0.002)` called |
| 24 | `run_id` is UUID, same across all rounds | Multi-round run | Same `run_id` kwarg on every `complete()` call |
| 25 | `round_number` increments per round | Multi-round run | Round 1 → 1, round 2 → 2, etc. |
| 26 | `_resolve_tools` returns `None` when `agent.tools=[]` | No tools configured | `tools=None` passed to `complete()` |
| 27 | `_resolve_tools` filters inactive tools | One active, one inactive in DB | Only active tool returned |

**6f. Message format routing** (`_build_tool_round_messages` — pure, no I/O):

| # | Test | Provider slug | Expected output |
|---|---|---|---|
| 28 | Anthropic format — success result | `anthropic` | `assistant` with content blocks; `user` with `tool_result` blocks |
| 29 | Anthropic format — error result | `anthropic` | `is_error=True`, error message in `content` |
| 30 | Anthropic format — text + tool call in same response | `anthropic` | Text block + `tool_use` block in assistant content |
| 31 | OpenAI format — success result | `openai` | `assistant` with `tool_calls` list; separate `role=tool` messages |
| 32 | OpenAI format — error result | `openai` | `role=tool` message content is `"Error: ..."` string |
| 33 | Azure OpenAI format same as OpenAI | `azure_openai` | Same structure as OpenAI |
| 34 | Multiple tool calls in one round — Anthropic | `anthropic` | One `user` message with multiple `tool_result` blocks |
| 35 | Multiple tool calls in one round — OpenAI | `openai` | One `assistant` + multiple `role=tool` messages |

**6g. Memory sanitization** (`_sanitize_content_for_memory` — pure, no I/O):

| # | Test | Input | Expected |
|---|---|---|---|
| 36 | Plain string | `"hello"` | Unchanged |
| 37 | Non-list, non-string (dict) | `{"type": "text"}` | Unchanged (not a content list) |
| 38 | Anthropic base64 image block | `type=image, source.type=base64` | Replaced with `{"type":"text","text":"[file: attachment]"}` |
| 39 | Anthropic base64 document block | `type=document, source.type=base64` | Replaced with `[file: attachment]` |
| 40 | Anthropic URL image block | `type=image, source.type=url` | Replaced with `[file: <url>]` |
| 41 | OpenAI `data:` URL block | `type=image_url, url=data:image/png;base64,...` | Replaced with `[file: attachment]` |
| 42 | OpenAI public URL block | `type=image_url, url=https://...` | Replaced with `[file: <url>]` |
| 43 | `type=text` block preserved | `{"type":"text","text":"hello"}` | Unchanged |
| 44 | Mixed list (file block + text block) | Both types in one list | File sanitized; text block unchanged |
| 45 | Empty list | `[]` | Empty list returned |

**6h. Memory flow** (load/save, mocked DB):

| # | Test | Setup | Assertion |
|---|---|---|---|
| 46 | `memory_enabled=False` → no session generated | Default agent | `session_id=None` throughout |
| 47 | `memory_enabled=True`, no `session_id` → UUID auto-generated | Memory-on agent | `response.session_id` is a valid UUID string |
| 48 | `memory_enabled=True`, explicit `session_id` → preserved | `session_id="abc"` passed | `response.session_id == "abc"` |
| 49 | History prepended to messages | `_load_session_messages` returns 2 history messages | 3 total messages sent to `complete` (2 history + 1 new) |
| 50 | Memory load failure → fail-open | `AppLLMMemorySession.objects.filter` raises | `complete()` still called with just the new message |
| 51 | Memory save failure → fail-open | `AppLLMMemoryMessage.objects.bulk_create` raises | Response still returned to caller |

---

### 7. `test_tool_sync_and_exec/` — Integration (ZangoAppBaseTestCase)

**Covers:** End-to-end pipeline: `@tool` decoration → `sync_tools()` → `AppLLMTool`
DB record → `ToolExecutor.execute()` → Django ORM inside the tool function.
Uses a real tenant schema and real `DynamicModelBase` models inside the tool — the
same pattern as `test_foreign_key`.

**Workspace fixture (`ai_test_module`):**
- `models.py` — `Patient(DynamicModelBase)` with `name: CharField`, `age: IntegerField`
- `tools.py` — three `@tool` functions:
  - `get_patient_count()` — queries `Patient.objects.count()`
  - `create_patient(name, age)` — creates and returns a `Patient`
  - `get_patient_by_id(patient_id)` — fetches or raises `Patient.DoesNotExist`

**7a. Tool sync (`sync_tools`):**

| # | Test | Assertion |
|---|---|---|
| 1 | First sync creates records | `AppLLMTool.objects.count() == 3` |
| 2 | All tools have correct `section` | `section="patients"` on all three |
| 3 | `parameters_schema` matches `_tool_meta` | DB field equals decorator-generated schema |
| 4 | `python_path` stored correctly | `"ai_test_module.tools.<func_name>"` |
| 5 | `schema_hash` stored | Non-empty string on DB record |
| 6 | `is_active=True` after first sync | All records active |
| 7 | Re-sync is idempotent | Second `sync_tools()` → count still 3, `stats["created"]==0` |
| 8 | Unchanged tool → not updated | `stats["updated"]==0` on identical re-sync |
| 9 | `sync_tools()` returns correct stats dict | `{"created": 3, "updated": 0, "deactivated": 0}` on first run |
| 10 | Previously active unrelated tool deactivated | Manually create extra `AppLLMTool` before sync → `is_active=False` after |

**7b. Tool execution via `ToolExecutor` (real workspace import, real DB):**

| # | Test | Setup | Assertion |
|---|---|---|---|
| 11 | `get_patient_count` on empty DB | No patients created | `result.status="success"`, `result.output==0` |
| 12 | `create_patient` creates DB row | Execute with `{"name":"Alice","age":30}` | `Patient.objects.count()==1`, returned dict has `name` and `age` |
| 13 | `get_patient_by_id` returns correct data | Patient created first, then fetched by id | `result.output["name"] == "Alice"` |
| 14 | `get_patient_count` after create | Create one patient, then count | `result.output == 1` |
| 15 | Missing required param → `validation_error` | `{}` against `create_patient` | `result.status=="validation_error"` |
| 16 | Wrong param type → `validation_error` | `{"name": 123, "age": "old"}` | `result.status=="validation_error"` |
| 17 | Non-existent `patient_id` → tool raises | `get_patient_by_id(patient_id=9999)` | `result.status=="error"`, `result.error_traceback` set |
| 18 | `execution_time_ms` is non-negative int | Any successful call | Field set and ≥ 0 |
| 19 | `total_calls` incremented after success | Execute once | `AppLLMTool.total_calls == 1` |
| 20 | `total_errors` incremented after error | Trigger error (bad id) | `AppLLMTool.total_errors == 1` |
| 21 | `total_timeouts` incremented on timeout | Tool record `timeout_seconds=0`, execute | `AppLLMTool.total_timeouts == 1` |
| 22 | `last_called_at` set after execution | Execute once | `AppLLMTool.last_called_at` is not `None` |

**7c. `AppLLMToolCall` record verification (written by `AgentClient._log_tool_call`):**

These tests call `AgentClient._log_tool_call` directly with a real `AppLLMInvocation`
PK (created in setup) and verify the DB row it produces.

| # | Test | Setup | Assertion on `AppLLMToolCall` row |
|---|---|---|---|
| 23 | Row created on success | `result.status="success"`, `output={"score":95}` | `AppLLMToolCall.objects.count()==1` |
| 24 | `tool_name` stored | Any call | `tool_name == "get_patient_count"` |
| 25 | `tool_input` stored | `input={"patient_id": 1}` | `tool_input == {"patient_id": 1}` |
| 26 | `tool_output` stored on success | `result.output={"score":95}` | `tool_output == {"score": 95}` |
| 27 | `status` stored correctly — success | `result.status="success"` | `AppLLMToolCall.status == "success"` |
| 28 | `status` stored correctly — error | `result.status="error"` | `AppLLMToolCall.status == "error"` |
| 29 | `error_message` stored on error | `result.error_message="DB failed"` | `error_message == "DB failed"` |
| 30 | `error_traceback` stored on error | `result.error_traceback="Traceback..."` | `error_traceback` non-empty |
| 31 | `round_number` stored | `round_number=2` | `AppLLMToolCall.round_number == 2` |
| 32 | `execution_time_ms` stored | `result.execution_time_ms=120` | `execution_time_ms == 120` |
| 33 | `tool` FK linked to `AppLLMTool` | Tool synced before call | `tool_call.tool == tool_record` |
| 34 | `tool` FK is `None` when tool not in DB | No sync before call | `tool_call.tool is None` (SET_NULL) |

**7d. `AppLLMMemorySession` and `AppLLMMemoryMessage` — memory enabled/disabled:**

These tests call `AgentClient._save_session_messages` and `_load_session_messages`
directly against the real DB using real `AppLLMAgent` and `AppLLMMemorySession` model
instances. A mock `AppLLMAgent` model instance is created in the tenant schema setup.

*Memory disabled (default):*

| # | Test | Setup | Assertion |
|---|---|---|---|
| 35 | `memory_enabled=False` → no session created | Run agent with no `session_id` | `AppLLMMemorySession.objects.count() == 0` |
| 36 | `memory_enabled=False` + explicit `session_id` → no session | `session_id="abc"` passed | `AppLLMMemorySession.objects.count() == 0` |

*Session creation:*

| # | Test | Setup | Assertion |
|---|---|---|---|
| 37 | First save creates `AppLLMMemorySession` | Call `_save_session_messages` | `AppLLMMemorySession.objects.count() == 1` |
| 38 | `session_id` stored on session | `session_id="sess-001"` | `session.session_id == "sess-001"` |
| 39 | `user_ref` stored on session | `user_ref="user-42"` | `session.user_ref == "user-42"` |
| 40 | `is_active=True` on new session | First save | `session.is_active == True` |
| 41 | Second save reuses existing session (get_or_create) | Call `_save_session_messages` twice same `session_id` | `AppLLMMemorySession.objects.count() == 1` |
| 42 | `last_active_at` updated on second call | Call twice | `last_active_at` of second call > first call |

*Message persistence:*

| # | Test | Setup | Assertion on `AppLLMMemoryMessage` |
|---|---|---|---|
| 43 | User message saved | User message in `input_messages` | `AppLLMMemoryMessage` with `role="user"` created |
| 44 | Assistant response saved | `response.content="Final answer"` | `AppLLMMemoryMessage` with `role="assistant"` created |
| 45 | Non-user messages in `input_messages` skipped | `role="assistant"` in input list | Only `role="user"` rows written |
| 46 | Empty `response.content` → no assistant row | `response.content=""` | Only user message written, no assistant row |
| 47 | `sequence` is monotonically increasing | Two saves to same session | Second batch starts at `max(sequence)+1` |
| 48 | `invocation_id` linked on messages | Real invocation PK in response | `memory_message.invocation_id == invocation.pk` |
| 49 | File blocks sanitized before save | User message with base64 image block | Stored content has `[file: attachment]`, not raw bytes |

*Message loading:*

| # | Test | Setup | Assertion |
|---|---|---|---|
| 50 | Load returns messages in oldest-first order | Save 3 messages with sequences 1,2,3 | Returned list ordered 1→2→3 |
| 51 | `memory_max_messages` cap respected | Save 10 message pairs, `max_messages=3` | Only 6 messages (3 pairs) returned |
| 52 | No session → empty list returned | Load with unknown `session_id` | `[]` returned, no exception |
| 53 | Inactive session → empty list | `session.is_active=False` | `[]` returned |
| 54 | `role`, `content` restored correctly | Save and load a user message | Loaded `LLMMessage.role == "user"`, `content` matches |

*Session lifecycle:*

| # | Test | Setup | Assertion |
|---|---|---|---|
| 55 | `clear_session` deactivates and deletes messages | Active session with 3 messages | `is_active=False`, `messages.count()==0`, returns `True` |
| 56 | `clear_session` on unknown session_id returns `False` | No session exists | Returns `False`, no crash |

---

## Test Count Summary

| File | Tier | Tests | DB |
|---|---|---|---|
| `test_tool_decorator.py` | Unit | 29 ✓ | No |
| `test_cost.py` | Unit | 10 | No |
| `test_llm_file.py` | Unit | 17 | No |
| `test_tool_executor.py` | Unit | 25 | Mocked |
| `test_provider_client.py` | Unit | 19 | Mocked |
| `test_agent_client.py` | Unit | 51 | Mocked |
| `test_tool_sync_and_exec/` | Integration | 56 | Real tenant schema |
| **Total** | | **~207** | |

---

## Implementation Order

1. `test_cost.py` — fastest, validates billing logic
2. `test_llm_file.py` — pure dataclass, no surprises
3. `test_tool_executor.py` — validation and serialization sub-groups before execution
4. `test_provider_client.py` — framework concerns around provider
5. `test_agent_client.py` — largest; write guard checks → input resolution → loop → format → memory
6. `test_tool_sync_and_exec/` — integration last; needs workspace fixture + migration generated by `ws_makemigration`
