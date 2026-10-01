# Zango AI Module — Claude Code Context

## Directory Structure

```
backend/src/zango/ai/               # Core library (provider-agnostic logic)
├── __init__.py                     # Public API: get_provider(), get_prompt(), get_agent(); re-exports data classes
├── client.py                       # ProviderClient: wraps BaseLLMProvider with logging, cost tracking, budget enforcement
├── agent_client.py                 # AgentClient: agentic tool loop, memory, file pre-upload, output schema validation
├── cost.py                         # compute_anthropic_cost() — handles cache pricing (1.25× creation, 0.1× read)
├── encryption.py                   # encrypt_config() / decrypt_config() / mask_config() — Fernet via FIELD_ENCRYPTION_KEY
├── exceptions.py                   # 14 typed exceptions (ZangoAIError base → ProviderNotFound, BudgetExceeded, etc.)
├── tasks.py                        # Celery tasks: async_llm_complete(), update_tool_usage_stats()
├── providers/
│   ├── __init__.py                 # Safe imports; exports all provider classes
│   ├── base.py                     # BaseLLMProvider ABC + all shared data classes
│   ├── anthropic.py                # Anthropic/Claude (Files API, prompt caching, streaming)
│   ├── openai.py                   # OpenAI GPT/o-series (JSON strict mode, type-array workaround)
│   ├── azure_openai.py             # Azure OpenAI (deployment-based, no file handling)
│   ├── bedrock.py                  # AWS Bedrock stub — complete/stream raise NotImplementedError
│   └── registry.py                 # @register_provider decorator + PROVIDER_REGISTRY dict
└── tools/
    ├── __init__.py
    ├── decorator.py                # @tool decorator — builds JSON Schema from type hints; ToolMeta dataclass
    ├── executor.py                 # ToolExecutor.execute() — import → validate → run with SIGALRM timeout → serialize
    └── registry.py                 # Stub only; tool discovery lives in Workspace.get_tools() / sync_tools()

backend/src/zango/apps/ai/          # Django app: DB models + migrations
├── apps.py
├── migrations/                     # 12 migrations (0001_initial → 0012_remove_tool_confirmation)
└── models/
    ├── provider.py                 # AppLLMProvider, AppLLMProviderModel
    ├── agent.py                    # AppLLMAgent
    ├── prompt.py                   # AppLLMPrompt, AppLLMPromptVersion
    ├── tool.py                     # AppLLMTool, AppLLMToolCall
    ├── invocation.py               # AppLLMInvocation, AppLLMInvocationFile
    └── memory.py                   # AppLLMMemorySession, AppLLMMemoryMessage

backend/src/zango/api/platform/ai/v1/   # REST API layer
├── views.py                        # ~900 lines; all CRUD + action endpoints
├── serializers.py                  # ~400 lines; DRF serializers with config masking/validation
└── urls.py                         # 97 lines; URL routing (order matters — see URL notes below)
```

---

## Core Classes

### `providers/base.py` — Data Classes & ABC

| Class / Type | Purpose |
|---|---|
| `LLMFile` | File attachment; class methods `from_django_file`, `from_bytes`, `from_url`, `from_path`; `.to_anthropic_block()` / `.to_openai_block()` |
| `LLMMessage` | `role`, `content`, `tool_call_id`, `tool_calls`, `files` |
| `LLMToolDef` | `name`, `description`, `input_schema` — passed to providers |
| `LLMToolCall` | `id`, `name`, `input` — returned by providers |
| `LLMUsage` | `input_tokens`, `output_tokens`, `cache_creation_tokens`, `cache_read_tokens` |
| `LLMResponse` | Full response: content, tool_calls, stop_reason, usage, model, latency_ms, cost_usd, invocation_id, session_id, parsed_content |
| `LLMStreamChunk` | `delta_text`, `delta_tool_call`, `is_final`, `usage`, `stop_reason` |
| `BaseLLMProvider` | ABC with abstract `complete()`, `stream()`, `validate_config()`, `get_models()` |

**Concrete methods on `BaseLLMProvider` (can override):**
- `fetch_models(config)` — live API fetch; default returns `get_models()`
- `compute_cost(usage, model)` — looks up `AppLLMProviderModel` overrides first
- `prepare_files(files)` — no-op by default; Anthropic overrides for Files API upload
- `format_tools_for_api(tools)` — Anthropic tool format by default; OpenAI/Azure override

---

### `client.py` — `ProviderClient`

Wraps `BaseLLMProvider`; constructed from `AppLLMProvider.get_client()`.

```python
client = AppLLMProvider.objects.get(name="my-provider").get_client()
response = client.complete(messages, system=..., tools=..., agent=agent_obj, ...)
```

**Responsibilities:**
- Calls `provider.check_budget()` before every invocation → raises `BudgetExceeded`
- Calls `provider.check_rate_limits()` → raises `RateLimitExceeded`
- Writes `AppLLMInvocation` row (full request + response snapshot)
- Updates `AppLLMProvider.record_usage()` atomically via `F()` expressions
- Normalises provider exceptions into `ZangoAIError` subclasses

---

### `agent_client.py` — `AgentClient`

Runs the agentic tool loop. Constructed by `get_agent()` public API.

```python
from zango.ai import get_agent
agent_client = get_agent("my-agent")
response = agent_client.run(
    user_message="...",
    session_id="abc",          # enables short-term memory
    variables={"key": "val"},  # for prompt templates
    files=[LLMFile(...)],
)
```

**Loop mechanics:**
1. Load memory session messages (filtered by `memory_policy`)
2. Pre-upload `LLMFile` objects once via `provider.prepare_files()`; reuse file refs across rounds
3. Call `ProviderClient.complete()` with current messages + tools
4. If `stop_reason == "tool_use"`: execute tools via `ToolExecutor`, append tool results, loop
5. Exit when `stop_reason == "end_turn"` or max rounds reached
6. Validate output against `output_json_schema` if agent has one → raises `OutputValidationError`
7. Save new messages to `AppLLMMemorySession` (exclude `memory_policy="exclude"` tool calls)

**Tool result formatting:**
- Anthropic: `{"type": "tool_result", "tool_use_id": ..., "content": ...}`
- OpenAI/Azure: `{"role": "tool", "tool_call_id": ..., "content": ...}`
- Format is chosen based on `provider.provider_slug`

---

## Provider Abstraction Pattern

### Registration

```python
# providers/registry.py
@register_provider(slug="anthropic", display_name="Anthropic", icon="...")
class AnthropicProvider(BaseLLMProvider):
    ...
```

`PROVIDER_REGISTRY: dict[str, type[BaseLLMProvider]]` — slug → class.

### Config Schema

Each provider class defines:
```python
CONFIG_FIELDS = [
    {"name": "api_key", "type": "secret", "required": True, "label": "API Key"},
    {"name": "default_model", "type": "select", "required": True, "choices_from": "models"},
    ...
]
SUPPORTED_MODELS = [
    {"model_id": "claude-opus-4-7-...", "display_name": "...", "context_window": 128000,
     "input_cost_per_mtok": 15.0, "output_cost_per_mtok": 75.0},
    ...
]
```

`get_available_providers()` returns UI metadata (slug, display_name, icon, supported_models, config_fields) without instantiation.

### Adding a New Provider

1. Create `providers/<slug>.py` inheriting `BaseLLMProvider`
2. Decorate with `@register_provider(slug=..., display_name=..., icon=...)`
3. Define `CONFIG_FIELDS` and `SUPPORTED_MODELS`
4. Implement `complete()`, `stream()`, `validate_config()`, `get_models()`
5. Override `fetch_models()`, `prepare_files()`, `format_tools_for_api()`, `compute_cost()` as needed
6. Import in `providers/__init__.py`

---

## Configuration Storage

### `AppLLMProvider` (tenant-scoped)

| Field | Notes |
|---|---|
| `provider_slug` | FK to `PROVIDER_REGISTRY` key |
| `config_encrypted` | `BinaryField`; Fernet-encrypted JSON; never stored plain |
| `default_model` | model_id string |
| `rate_limit_rpm/tpm` | 0 = unlimited |
| `monthly_budget_usd` | 0 = unlimited; resets on `budget_reset_day` |
| `current_month_spend_usd` | running total; updated atomically |
| `is_validated` | set True after `validate_config()` succeeds |

**Config lifecycle:**
```
POST /providers/     → AppLLMProviderCreateSerializer
                       → calls provider.validate_config()
                       → encrypt_config() before save
GET  /providers/<id> → AppLLMProviderListSerializer
                       → mask_config() (shows "ABCDEF...****XYZ")
PUT  /providers/<id> → AppLLMProviderUpdateSerializer
                       → if field is masked sentinel, preserve existing encrypted value
```

**Getting a live provider instance:**
```python
provider_obj = AppLLMProvider.objects.get(name="...", is_enabled=True)
client = provider_obj.get_client()  # decrypts, instantiates, checks budget
```

### `AppLLMAgent`

Links `AppLLMProvider` (FK) + `AppLLMPrompt` FKs for system/user prompts + `tools` (JSONField list of `AppLLMTool.name` strings).

### `AppLLMPromptVersion`

`content` is a `{{variable}}` template. `render(**kwargs)` does simple string replace; raises `PromptRenderError` on missing vars. `variables` (JSONField) auto-extracted on save.

---

## Entry Points — API

Base prefix: `/api/v1/ai/` (set in platform URL config)

### Provider Endpoints
| Method | Path | View |
|---|---|---|
| GET | `/available/` | Registry metadata (no auth needed for slugs/icons) |
| POST | `/fetch-models/` | Live model fetch without creating a provider |
| GET/POST | `/providers/` | List / create |
| GET/PUT/DELETE | `/providers/<id>/` | Detail; DELETE blocked if invocations exist (soft-delete) |
| POST | `/providers/<id>/validate/` | Calls `validate_config()`, updates `is_validated` |
| POST | `/providers/<id>/toggle/` | Enable/disable; disable blocked if active agents depend on it |
| POST | `/providers/<id>/models/<mid>/toggle/` | Per-model enable/disable |

### Agent Endpoints
| Method | Path | Notes |
|---|---|---|
| GET/POST | `/agents/` | |
| GET/PUT/DELETE | `/agents/<id>/` | |
| POST | `/agents/<id>/test/` | Runs `AgentClient.run()` synchronously; returns full response |
| POST | `/agents/<id>/duplicate/` | Clones agent + no memory sessions |
| GET | `/agents/<id>/sessions/` | Memory sessions |
| GET/DELETE | `/agents/<id>/sessions/<sid>/` | Session detail / clear messages |

### Tool Endpoints
| Method | Path | Notes |
|---|---|---|
| POST | `/tools/sync/` | Calls `Workspace.sync_tools()` — discovers `@tool` decorated functions in workspace |
| GET | `/tools/sections/` | Returns tools grouped by `section` field |

### Invocation Endpoints
| Method | Path | Notes |
|---|---|---|
| GET | `/invocations/stats/` | Aggregate counts + cost for header display |
| GET | `/invocations/` | Paginated; filters: provider, agent, status, date range |
| GET | `/invocations/<id>/` | Full audit: request, response, tool calls, files |

---

## Tool System

### Defining a Tool (in workspace code)

```python
from zango.ai.tools.decorator import tool, ToolSafety, ToolParam

@tool(
    name="search_records",
    description="Search database records by query string",
    section="Database",
    safety=ToolSafety.READ_ONLY,
    timeout_seconds=30,
    memory_policy="include",   # or "exclude" to suppress from memory history
)
def search_records(
    query: str = ToolParam(description="Search query"),
    limit: int = ToolParam(description="Max results", default=10),
) -> list[dict]:
    ...
```

`@tool` auto-generates `parameters_schema` (JSON Schema) from type hints. Supported types: `str`, `int`, `float`, `bool`, `list`, `dict`, `Optional[T]`, `Union[T1, T2]`.

### Syncing Tools

`POST /tools/sync/` → `Workspace.sync_tools()` walks workspace code, finds `@tool` decorated functions, upserts `AppLLMTool` rows. Uses `schema_hash` to detect changes.

### Execution

`ToolExecutor.execute(tool_name, tool_input)` — never raises:
1. Load `AppLLMTool` from DB by name
2. `importlib.import_module(tool.python_path)` + `getattr(module, func_name)`
3. `jsonschema.validate(tool_input, tool.parameters_schema)`
4. Call with `signal.SIGALRM` timeout (main thread only; worker threads skip timeout)
5. Serialize output; truncate if > 50 KB
6. Return `ToolResult(output, status, execution_time_ms, error_message)`

---

## Streaming

Both `ProviderClient.stream()` and provider `.stream()` return `Generator[LLMStreamChunk, None, None]`.

- `delta_text`: incremental text
- `delta_tool_call`: partial tool call accumulation (provider-specific format)
- `is_final=True`: last chunk; `usage` and `stop_reason` populated here
- `ProviderClient` does **not** log invocations for streaming calls (only `complete()` logs)

Anthropic streams JSON tool call inputs as partial strings; fully assembled only on `input_json_delta` events. OpenAI streams `delta.tool_calls` with index-based accumulation.

---

## Invocation Logging

Every `ProviderClient.complete()` call writes one `AppLLMInvocation` row:
- Full request snapshot: `request_messages`, `request_system`, `request_tools`, `request_params`
- Full response snapshot: `request_content`, `response_tool_calls`
- Timing: `latency_ms`, `time_to_first_token_ms`
- Cost: `cost_usd`, token breakdown
- Agent tracking: `run_id` (UUID grouping all rounds), `round_number`, `session_id`
- Trigger context: `triggered_by` ("user"/"celery"/"cron"/"system"), `user_id_ref`

`AppLLMInvocationFile` mirrors file blobs into tenant storage (ZFileField); de-duplicated by `sha256`.

---

## Non-Obvious Constraints

- **Bedrock is fully implemented** via the Converse API (`converse` / `converse_stream`). Requires `boto3>=1.43.23`. Auth uses static AWS access keys (no STS/SSO).
- **Bedrock model IDs are region-agnostic bare IDs** in `supported_models`. At call time `_resolve_model_id()` resolves them to the real cross-region profile ID for models with `requires_inference_profile=True`. It consults the **live** `list_inference_profiles` result (cached per-instance via `_live_profile_map()`, on a lazily-built control-plane `bedrock` client) and uses the exact profile ID AWS returns — preferring a geo-specific profile (`us.`/`eu.`/`apac.`) over `global.`. If AWS offers no profile for that model in the configured geography, it raises a clear `LLMAPIError` ("not available … in the … geography") instead of fabricating an ID that fails with a `ValidationException`. Only when the live list is unavailable (permissions/SDK/region) does it fall back to deriving the prefix from `aws_region`. IDs already starting with `us.` / `eu.` / `apac.` / `global.` pass through unchanged.
- **Bedrock structured outputs** use `outputConfig.textFormat` on the Converse API (boto3 >= 1.43.23). JSON schema is serialized to a string. Type arrays (`["string", "null"]`) are not supported by Bedrock — `_normalize_schema_for_bedrock()` rewrites them to `anyOf: [{type: X}, {type: "null"}]` automatically. Grammar compilation on first use can be slow; subsequent calls with the same schema hit a 24h cache.
- **Bedrock structured outputs + `global.` inference profiles** — grammar compilation does not work with `global.` prefixed model IDs (worldwide routing layer). Use geo-specific profiles (`us.`, `eu.`, `au.`, `jp.`) for structured output. From regions with no geo profile (e.g. `ap-south-1`), only `global.` is available and structured outputs will time out.
- **Bedrock boto3 timeout** is baked into the client at `__init__` time (botocore `read_timeout`). The same `timeout_seconds` provider config applies to both normal and structured output calls. `_schema_client` is an alias for `_client`.
- **Azure uses deployment names as model IDs.** There is no hardcoded `SUPPORTED_MODELS`; models come from `GET /openai/deployments`. Azure config uses `default_deployment` not `default_model`.
- **Config masking is one-way at serialization.** `AppLLMProviderUpdateSerializer` checks if each secret field equals the masked sentinel; if so, the existing encrypted value is preserved. Partial updates work correctly.
- **Tool timeout uses `SIGALRM`.** This only works on Unix and only in the main thread. In Celery worker threads, the timeout is silently skipped.
- **Provider delete is soft when invocations exist.** The view disables the provider and appends `_deleted_<timestamp>` to its name instead of hard-deleting.
- **Agent `tools` is a JSONField list of tool names** (strings), not FKs. `ToolExecutor` does the DB lookup at call time.
- **Memory filtering:** Tool calls with `memory_policy="exclude"` on the `AppLLMTool` row are not persisted to `AppLLMMemoryMessage`. Use this for side-effectful tools (e.g. send email) whose results shouldn't be replayed.
- **`run_id` groups agentic rounds.** All `AppLLMInvocation` rows from a single `AgentClient.run()` share the same `run_id` UUID; `round_number` increments per LLM call.
- **URL ordering in `urls.py` is load-bearing.** `/tools/sync/` and `/tools/sections/` must come before `<int:tool_id>`; `/invocations/stats/` must come before `<int:invocation_id>`.
- **`AppLLMProvider` is tenant-scoped** (set_app_schema_path decorator on all views). `AppLLMAzureOpenAI` conceptually lives in the shared schema but currently follows the same pattern.
- **Prompt variables use `{{double_braces}}`**, not Jinja2 `{single}`. `render()` does `str.replace("{{key}}", value)` after extracting variables with `re.findall(r'\{\{(\w+)\}\}', content)`.
