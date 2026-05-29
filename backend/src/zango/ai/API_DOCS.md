# Zango AI Framework — Platform API Documentation

Base URL: `/api/v1/apps/<app_uuid>/ai/`

All endpoints require platform admin session authentication (CSRF token via `X-CSRFToken` header).

All responses follow the standard Zango format:

```json
{
  "success": true | false,
  "response": { ... }
}
```

---

## 1. Available Providers (Registry)

### GET `/providers/available/`

Returns metadata about all registered LLM provider classes from the platform registry. This is read from code, not the database. Use this to populate the "Add Provider" form.

**Response:**

```json
{
  "success": true,
  "response": {
    "providers": [
      {
        "slug": "anthropic",
        "display_name": "Anthropic",
        "icon": "anthropic.svg",
        "supported_models": [
          {
            "id": "claude-opus-4-20250514",
            "name": "Claude Opus 4",
            "context_window": 200000,
            "max_output_tokens": 32000,
            "input_cost_per_mtok": 15.0,
            "output_cost_per_mtok": 75.0,
            "supports_tools": true,
            "supports_vision": true,
            "supports_streaming": true
          },
          {
            "id": "claude-sonnet-4-20250514",
            "name": "Claude Sonnet 4",
            "context_window": 200000,
            "max_output_tokens": 16000,
            "input_cost_per_mtok": 3.0,
            "output_cost_per_mtok": 15.0,
            "supports_tools": true,
            "supports_vision": true,
            "supports_streaming": true
          }
        ],
        "config_fields": [
          {
            "name": "api_key",
            "type": "secret",
            "required": true,
            "label": "API Key",
            "help_text": "Your Anthropic API key (starts with sk-ant-)"
          },
          {
            "name": "default_model",
            "type": "select",
            "required": true,
            "label": "Default Model",
            "options_from": "supported_models"
          },
          {
            "name": "max_retries",
            "type": "integer",
            "required": false,
            "label": "Max Retries",
            "default": 2
          },
          {
            "name": "timeout_seconds",
            "type": "integer",
            "required": false,
            "label": "Timeout (seconds)",
            "default": 120
          }
        ]
      },
      {
        "slug": "openai",
        "display_name": "OpenAI",
        "icon": "openai.svg",
        "supported_models": [ ... ],
        "config_fields": [ ... ]
      },
      {
        "slug": "azure_openai",
        "display_name": "Azure OpenAI",
        "icon": "azure.svg",
        "supported_models": [],
        "config_fields": [ ... ]
      },
      {
        "slug": "bedrock",
        "display_name": "AWS Bedrock",
        "icon": "aws.svg",
        "supported_models": [],
        "config_fields": [ ... ]
      }
    ]
  }
}
```

**Notes:**
- Only providers whose SDK is installed appear in the list (e.g., if `anthropic` pip package is missing, Anthropic won't show).
- `config_fields[].type` values: `"secret"` (encrypted, never returned in responses), `"string"`, `"url"`, `"select"`, `"integer"`, `"boolean"`.
- For `"select"` type fields, `options_from: "supported_models"` means the dropdown should be populated from the provider's `supported_models` list.

---

## 2. Configured Providers (CRUD)

### GET `/providers/`

List all configured provider instances for this app.

**Query Parameters:**

| Param    | Type   | Description                              |
|----------|--------|------------------------------------------|
| `search` | string | Search by name, description, or slug     |
| `status` | string | Filter: `"active"` or `"inactive"`       |
| `page`   | int    | Page number (default: 1)                 |

**Response:**

```json
{
  "success": true,
  "response": {
    "providers": {
      "total_records": 2,
      "total_pages": 1,
      "next": null,
      "previous": null,
      "records": [
        {
          "id": 1,
          "name": "claude-primary",
          "description": "Primary Anthropic provider for production",
          "provider_slug": "anthropic",
          "default_model": "claude-sonnet-4-20250514",
          "is_enabled": true,
          "is_validated": true,
          "last_validated_at": "2025-06-01T10:30:00Z",
          "validation_error": null,
          "rate_limit_rpm": 1000,
          "rate_limit_tpm": null,
          "monthly_budget_usd": "500.00",
          "budget_alert_threshold": "80.00",
          "current_month_spend_usd": "142.35",
          "total_invocations": 12450,
          "total_input_tokens": 45000000,
          "total_output_tokens": 12000000,
          "total_cost_usd": "892.450000",
          "created_at": "2025-05-15T08:00:00Z",
          "modified_at": "2025-06-01T10:30:00Z",
          "status": "active",
          "models_count": 3,
          "masked_config": {
            "api_key": "sk-ant...****7f3a",
            "default_model": "claude-sonnet-4-20250514",
            "max_retries": 2,
            "timeout_seconds": 120
          },
          "budget_status": {
            "within_budget": true,
            "used": "142.35",
            "limit": "500.00",
            "pct": 28.47
          },
          "enabled_models": [
            {
              "id": 1,
              "model_id": "claude-opus-4-20250514",
              "display_name": "Claude Opus 4",
              "input_cost_per_mtok_override": null,
              "output_cost_per_mtok_override": null,
              "is_enabled": true,
              "rate_limit_rpm": null
            },
            {
              "id": 2,
              "model_id": "claude-sonnet-4-20250514",
              "display_name": "Claude Sonnet 4",
              "input_cost_per_mtok_override": null,
              "output_cost_per_mtok_override": null,
              "is_enabled": true,
              "rate_limit_rpm": null
            }
          ]
        }
      ]
    },
    "message": "Providers fetched successfully"
  }
}
```

**Notes:**
- `masked_config` never contains plaintext secrets. Secret fields show masked values like `"sk-ant...****7f3a"`.
- `status` is a computed field: `"active"` when `is_enabled` is true, `"inactive"` otherwise.
- `models_count` counts only enabled models.
- `enabled_models` are auto-created from the provider's `supported_models` when the provider is first configured.

---

### POST `/providers/`

Create a new provider configuration.

**Request Body:**

```json
{
  "name": "claude-primary",
  "description": "Primary Anthropic provider",
  "provider_slug": "anthropic",
  "config": {
    "api_key": "sk-ant-api03-xxxxxxxxx",
    "default_model": "claude-sonnet-4-20250514",
    "max_retries": 2,
    "timeout_seconds": 120
  },
  "default_model": "claude-sonnet-4-20250514",
  "rate_limit_rpm": 1000,
  "rate_limit_tpm": null,
  "monthly_budget_usd": "500.00",
  "budget_alert_threshold": "80.00"
}
```

| Field                    | Type    | Required | Description                                      |
|--------------------------|---------|----------|--------------------------------------------------|
| `name`                   | string  | yes      | Unique name for this config (e.g., `claude-prod`) |
| `description`            | string  | no       | Description                                       |
| `provider_slug`          | string  | yes      | Must match a registered provider (`anthropic`, `openai`, `azure_openai`, `bedrock`) |
| `config`                 | object  | yes      | Provider-specific config. Must include all `required` fields from `config_fields`. Secret fields are encrypted before storage. |
| `default_model`          | string  | yes      | Default model ID to use                           |
| `rate_limit_rpm`         | int     | no       | Max requests per minute (null = unlimited)        |
| `rate_limit_tpm`         | int     | no       | Max tokens per minute (null = unlimited)          |
| `monthly_budget_usd`     | decimal | no       | Monthly spending cap in USD (null = unlimited)    |
| `budget_alert_threshold` | decimal | no       | Alert at this % of budget consumed (default: 80)  |

**Success Response (200):**

```json
{
  "success": true,
  "response": {
    "message": "Provider created successfully",
    "provider_id": 1
  }
}
```

**Validation Error (400):**

```json
{
  "success": false,
  "response": {
    "message": "provider_slug: Provider 'unknown' is not available. Available: ['anthropic', 'openai', 'azure_openai', 'bedrock']"
  }
}
```

**Notes:**
- On creation, `AppLLMProviderModel` records are automatically created for each model in the provider's `supported_models` list, all enabled by default.
- The `config` dict is encrypted as a single blob before storage. Individual secret fields are identified by the provider's `config_fields` spec.

---

### GET `/providers/<provider_id>/`

Get a single provider's full details.

**Response:** Same shape as a single record in the list endpoint.

---

### PUT `/providers/<provider_id>/`

Update a provider configuration. All fields are optional — only send fields you want to change.

**Request Body:**

```json
{
  "name": "claude-primary-v2",
  "description": "Updated description",
  "config": {
    "api_key": "sk-ant...****7f3a",
    "default_model": "claude-sonnet-4-20250514",
    "max_retries": 3,
    "timeout_seconds": 180
  },
  "default_model": "claude-sonnet-4-20250514",
  "monthly_budget_usd": "1000.00"
}
```

**Secret Preservation:** When the `config` object contains masked secret values (containing `****`), the existing encrypted value is preserved. Only plaintext values trigger re-encryption. This means the frontend can safely round-trip the `masked_config` from GET — secrets won't be overwritten.

**Success Response (200):**

```json
{
  "success": true,
  "response": {
    "message": "Provider updated successfully",
    "provider": { ... }
  }
}
```

---

### DELETE `/providers/<provider_id>/`

Delete a provider configuration.

**Behavior:**
- If the provider has **zero** invocations: hard delete (removed from database).
- If the provider has invocations: soft delete — `is_enabled` set to `false`, name appended with `" [deleted]"`. This preserves the audit trail.

**Success Response (200):**

```json
{
  "success": true,
  "response": {
    "message": "Provider deleted successfully"
  }
}
```

Or for soft delete:

```json
{
  "success": true,
  "response": {
    "message": "Provider disabled (has invocation history)"
  }
}
```

---

## 3. Provider Actions

### POST `/providers/<provider_id>/validate/`

Test the provider's credentials by making a minimal API call.

**Request Body:** None required.

**Success Response (200):**

```json
{
  "success": true,
  "response": {
    "message": "Provider credentials validated successfully"
  }
}
```

**Validation Failure (400):**

```json
{
  "success": false,
  "response": {
    "message": "Validation failed: Invalid API key provided"
  }
}
```

**Side effects:**
- Updates `is_validated`, `last_validated_at`, and `validation_error` on the provider record.
- For Anthropic: sends a 1-token completion request using the configured default model.
- For OpenAI/Azure: sends a 1-token chat completion request.
- For Bedrock: calls `list_foundation_models` with the configured credentials.

---

### POST `/providers/<provider_id>/toggle/`

Enable or disable a provider.

**Request Body:**

```json
{
  "is_enabled": false
}
```

| Field        | Type | Required | Description                |
|--------------|------|----------|----------------------------|
| `is_enabled` | bool | yes      | `true` to enable, `false` to disable |

**Success Response (200):**

```json
{
  "success": true,
  "response": {
    "message": "Provider disabled successfully"
  }
}
```

**Note:** When a provider is disabled, any attempt to use it via `get_provider()` will raise `ProviderDisabled`.

---

### GET `/providers/<provider_id>/usage/`

Get usage statistics and cost breakdown for a provider.

**Response:**

```json
{
  "success": true,
  "response": {
    "provider_id": 1,
    "total_invocations": 12450,
    "total_input_tokens": 45000000,
    "total_output_tokens": 12000000,
    "total_cost_usd": "892.450000",
    "budget_status": {
      "within_budget": true,
      "used": "142.35",
      "limit": "500.00",
      "pct": 28.47
    },
    "model_breakdown": [
      {
        "model": "claude-sonnet-4-20250514",
        "invocations": 10200,
        "input_tokens": 38000000,
        "output_tokens": 9500000,
        "cost": "654.320000"
      },
      {
        "model": "claude-haiku-4-5-20251001",
        "invocations": 2250,
        "input_tokens": 7000000,
        "output_tokens": 2500000,
        "cost": "238.130000"
      }
    ]
  }
}
```

---

### POST `/providers/<provider_id>/reset-budget/`

Manually reset the current month's spending counter to $0.

**Request Body:** None required.

**Success Response (200):**

```json
{
  "success": true,
  "response": {
    "message": "Budget reset successfully"
  }
}
```

**Note:** This also updates `last_budget_reset` to the current timestamp. Normally, the budget resets automatically on `budget_reset_day` of each month.

---

## 4. Invocation Logs

### GET `/invocations/`

Paginated list of LLM invocation logs (audit trail).

**Query Parameters:**

| Param          | Type   | Description                                    |
|----------------|--------|------------------------------------------------|
| `provider_id`  | int    | Filter by provider ID                          |
| `status`       | string | Filter: `success`, `error`, `timeout`, `rate_limited`, `budget_exceeded` |
| `triggered_by` | string | Filter: `user`, `celery`, `cron`, `system`     |
| `model`        | string | Filter by model ID                             |
| `page`         | int    | Page number (default: 1)                       |

**Response:**

```json
{
  "success": true,
  "response": {
    "invocations": {
      "total_records": 12450,
      "total_pages": 125,
      "next": "/api/v1/apps/<uuid>/ai/invocations/?page=2",
      "previous": null,
      "records": [
        {
          "id": 12450,
          "provider_name": "claude-primary",
          "provider_slug": "anthropic",
          "model": "claude-sonnet-4-20250514",
          "input_tokens": 1250,
          "output_tokens": 340,
          "cost_usd": "0.008850",
          "latency_ms": 1823,
          "triggered_by": "user",
          "status": "success",
          "error_type": null,
          "created_at": "2025-06-01T14:23:12Z"
        }
      ]
    },
    "message": "Invocations fetched successfully"
  }
}
```

**Notes:**
- The list view intentionally excludes `request_messages` and `response_content` to keep payloads small. Use the detail endpoint for full audit data.
- Results are ordered by `-created_at` (newest first).

---

### GET `/invocations/<invocation_id>/`

Full invocation detail — the audit drill-down view.

**Response:**

```json
{
  "success": true,
  "response": {
    "invocation": {
      "id": 12450,
      "provider": 1,
      "provider_name": "claude-primary",
      "provider_slug": "anthropic",
      "model": "claude-sonnet-4-20250514",
      "request_messages": [
        {"role": "user", "content": "Summarize this document..."}
      ],
      "request_system": "You are a helpful document summarizer.",
      "request_tools": null,
      "request_params": {
        "temperature": 0.7,
        "max_tokens": 4096
      },
      "response_content": "Here is a summary of the document...",
      "response_tool_calls": null,
      "stop_reason": "end_turn",
      "input_tokens": 1250,
      "output_tokens": 340,
      "cache_creation_tokens": 0,
      "cache_read_tokens": 0,
      "cost_usd": "0.008850",
      "latency_ms": 1823,
      "time_to_first_token_ms": null,
      "triggered_by": "user",
      "user_id_ref": "42",
      "celery_task_id": null,
      "status": "success",
      "error_message": null,
      "error_type": null,
      "created_at": "2025-06-01T14:23:12Z",
      "created_by": "",
      "modified_at": "2025-06-01T14:23:12Z",
      "modified_by": ""
    }
  }
}
```

---

## Error Responses

All endpoints return errors in this format:

```json
{
  "success": false,
  "response": {
    "message": "Human-readable error description"
  }
}
```

Common HTTP status codes:

| Code | Meaning                                |
|------|----------------------------------------|
| 200  | Success                                |
| 400  | Validation error / bad request         |
| 404  | Provider or invocation not found       |
| 500  | Internal server error                  |

---

## Developer API (Python)

For app developers using the AI framework in their code:

```python
from zango.ai import get_provider, LLMMessage

# Get a configured provider client
provider = get_provider("claude-primary")

# Synchronous completion
response = provider.complete(
    messages=[LLMMessage(role="user", content="Hello, summarize this text...")],
    model="claude-sonnet-4-20250514",   # optional, uses default_model if omitted
    temperature=0.7,
    max_tokens=4096,
    system="You are a helpful assistant.",
)

print(response.content)          # "Here is the summary..."
print(response.usage.input_tokens)   # 1250
print(response.usage.output_tokens)  # 340
print(response.cost_usd)        # 0.00885
print(response.latency_ms)      # 1823
print(response.stop_reason)     # "end_turn"

# Streaming completion
for chunk in provider.stream(
    messages=[LLMMessage(role="user", content="Tell me a story")],
):
    if chunk.delta_text:
        print(chunk.delta_text, end="", flush=True)
    if chunk.is_final:
        print(f"\nTokens: {chunk.usage.input_tokens} in / {chunk.usage.output_tokens} out")

# Async completion (via Celery)
task_id = provider.complete_async(
    messages=[LLMMessage(role="user", content="Analyze this data...")],
    model="claude-sonnet-4-20250514",
)
# Result stored in AppLLMInvocation, retrievable via Celery task_id
```

### Available Imports

```python
from zango.ai import (
    get_provider,    # Main entry point
    LLMMessage,      # Message dataclass (role, content)
    LLMResponse,     # Completion response (content, tool_calls, usage, cost_usd, ...)
    LLMStreamChunk,  # Streaming chunk (delta_text, is_final, usage, ...)
    LLMToolDef,      # Tool definition (name, description, input_schema)
    LLMToolCall,     # Tool call from LLM (id, name, input)
    LLMUsage,        # Token usage (input_tokens, output_tokens, cache_*)
)
```

### Exception Handling

```python
from zango.ai.exceptions import (
    ZangoAIError,          # Base — catch-all for AI errors
    ProviderNotFound,      # Provider name not found in database
    ProviderDisabled,      # Provider is disabled by admin
    BudgetExceeded,        # Monthly budget exceeded
    RateLimitExceeded,     # Rate limit hit (has .retry_after_seconds)
    LLMAPIError,           # Provider API error (has .status_code, .original_error)
    LLMTimeoutError,       # Request timed out
    ModelNotAvailable,     # Model not enabled for this provider
    ProviderConfigInvalid, # Config validation failed
)

try:
    response = provider.complete(messages=[...])
except BudgetExceeded as e:
    print(f"Budget of ${e.budget_limit} exceeded for {e.provider_name}")
except RateLimitExceeded as e:
    if e.retry_after_seconds:
        print(f"Rate limited, retry after {e.retry_after_seconds}s")
except LLMAPIError as e:
    print(f"API error {e.status_code}: {e}")
```
