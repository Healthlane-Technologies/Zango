# Platform Logs

Read-only view of application, Celery worker and Celery beat logs from
whatever store each component logs to. **CloudWatch** is the only
supported backend in v1; DynamoDB / OpenTelemetry / Elasticsearch
connectors can be added later by implementing the same Protocol.

Design and mockup: [`backend/docs/platform-logs-design.html`](../../../../docs/platform-logs-design.html)
Live implementation progress: [`backend/docs/platform-logs-progress.md`](../../../../docs/platform-logs-progress.md)

## What lives where

| Concern | Path |
|---|---|
| App scaffold (SHARED_APP) | `zango.apps.shared.platform_logs` |
| Config model | `models.py` → `LogConnectorConfig` (public schema, one row per env × component) |
| Connector abstraction | `connectors/base.py` |
| Connector registry (lazy) | `connectors/__init__.py` |
| CloudWatch connector | `connectors/cloudwatch.py` |
| API views | `zango.api.platform.platform_logs.v1` |
| Frontend · Settings | `frontend/src/pages/platformLogConnectors/` |
| Frontend · in-app tab | `frontend/src/pages/appLogs/components/RuntimeLogs/` |
| Producer-side fix (LOGGING) | `zango.config.settings.base` (console handler + tenant_filter) |
| Celery `setup_logging` | `apps/platform_logs/celery_logging.py` |
| IAM policy template | `backend/docs/iam/platform-logs.json` |

## Operating notes

- **Restart Celery worker** after merging. The `setup_logging` signal
  handler is installed at app `ready()` and only takes effect at worker
  boot — without a restart the worker keeps its old logger config and
  CloudWatch lines won't carry the tenant prefix.
- **Attach the IAM policy** at `docs/iam/platform-logs.json` to the ECS
  task role (and to any local IAM user used for development). Without
  it, the connector's first `DescribeLogStreams` call will 403.
- **Seed connector rows** by opening `/platform/log-connectors/` as a
  superadmin. One row per `(environment × component)`. Click **Test
  connection** before saving.

## Local dev story

Local dev has no CloudWatch. The Runtime Logs tab will show a friendly
empty state ("No connectors configured") unless you explicitly seed a
row pointing at a staging CloudWatch group from a local
`platform.logs.admin` user with access to that IAM role.

The producer-side fix is env-conditional — `ENV=local` keeps the
shorter `console` formatter so your terminal stays readable.

## Tenant filtering

The CloudWatch connector translates the active app's `tenant.schema_name`
into a CloudWatch filter pattern:

| Format (configured per connector row) | Filter pattern added |
|---|---|
| `verbose` (default in staging/prod) | `"[<schema>:"` — matches the bracketed prefix the existing `TenantContextFilter` writes |
| `json` (future) | `{ $.app_name = "<schema>" }` |
| `plain` | none — viewer sees all tenants' lines (legacy behaviour) |

Plain format should only be used for environments where the producer-side
fix hasn't shipped yet. Once `verbose` is in place across staging/prod,
flip the connector row's `format` to `verbose` to enable tenant scoping.

## Adding a new connector type

1. Add an entry to `ConnectorType` in `models.py`.
2. Implement a class in `connectors/<your_type>.py` conforming to
   `LogConnector` Protocol from `connectors/base.py`.
3. Register a lazy factory in `connectors/__init__.py:_REGISTRY`.
4. Add a JSON schema for its `config` blob in `serializers.py` if you
   want field-level validation (otherwise the connector's own
   `__init__` raises `ConnectorConfigError` on bad input).
5. The admin UI's connector-type dropdown will pick it up
   automatically.

## Future / deferred

- Per-app override of the platform-level config (currently every app in
  an env reads from the same connector).
- JSON formatter producer-side fix (verbose works today; JSON is
  cleaner for Logs Insights).
- Tenant-side permission policies (`platform.logs.view` /
  `.admin`) — gated by platform-user classes in v1.
- Connector test fixtures (`tests/test_cloudwatch_connector.py` with
  `botocore.stub.Stubber`).
