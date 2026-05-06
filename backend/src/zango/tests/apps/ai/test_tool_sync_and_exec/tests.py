"""
Integration tests for AI tool sync, execution, tool-call logging, and memory.

Uses a real tenant DB schema (via ZangoAppBaseTestCase + FastTenantTestCase).
The LLM API call is mocked — everything else (workspace, DB models, ToolExecutor,
AgentClient agentic loop, AppLLMToolCall, AppLLMMemorySession) is exercised for real.

All tests live in one class so setUpClass runs exactly once (workspace copy + ws_migrate
are expensive and must not repeat per sub-class).

Test sections:
  7a — sync_tools() creates / updates / deactivates AppLLMTool records
  7b — ToolExecutor.execute() runs real functions against real DB rows
  7c — AgentClient._log_tool_call() writes correct AppLLMToolCall records
  7d — AppLLMMemorySession + AppLLMMemoryMessage persisted across two agent runs
"""

import os
from unittest.mock import MagicMock, patch

from django.core.management import call_command
from django.test import override_settings
from django_tenants.utils import schema_context, tenant_context

from zango.apps.dynamic_models.workspace.base import Workspace
from zango.test.cases import ZangoAppBaseTestCase


# ── Mock LLM response helpers ──────────────────────────────────────────────────


def _make_final_response(content="Done"):
    """Build a minimal LLMResponse-like object that signals 'end_turn' (no tool calls)."""
    from zango.ai.providers.base import LLMResponse, LLMUsage

    resp = LLMResponse(
        content=content,
        tool_calls=[],
        stop_reason="end_turn",
        usage=LLMUsage(input_tokens=10, output_tokens=5),
        model="claude-sonnet-4-20250514",
        raw_response=None,
        latency_ms=50,
        cost_usd=0.001,
    )
    resp.invocation_id = None
    return resp


def _make_tool_use_response(tool_name, tool_input, tool_call_id="tc1"):
    """Build a mock LLMResponse that requests a single tool call."""
    from zango.ai.providers.base import LLMResponse, LLMToolCall, LLMUsage

    resp = LLMResponse(
        content=None,
        tool_calls=[LLMToolCall(id=tool_call_id, name=tool_name, input=tool_input)],
        stop_reason="tool_use",
        usage=LLMUsage(input_tokens=20, output_tokens=10),
        model="claude-sonnet-4-20250514",
        raw_response=None,
        latency_ms=80,
        cost_usd=0.002,
    )
    resp.invocation_id = None
    return resp


def _mock_raw_provider():
    """Return a minimal mock raw provider (returned by AppLLMProvider.get_client())."""
    raw = MagicMock()
    raw.complete.return_value = _make_final_response()
    raw.compute_cost.return_value = 0.001
    raw.prepare_files.return_value = []
    return raw


# ── Integration test class ────────────────────────────────────────────────────


class AIToolSyncAndExecTest(ZangoAppBaseTestCase):
    """
    All AI integration tests in a single class so workspace setup runs once.

    Covers:
      - 7a sync_tools()
      - 7b ToolExecutor.execute() against real DB
      - 7c AppLLMToolCall records written by AgentClient
      - 7d AppLLMMemorySession / AppLLMMemoryMessage persistence

    Uses schema "ai_test_app" (not "testapp") to avoid polluting the shared
    testapp schema / migration state used by all other ZangoAppBaseTestCase
    subclasses.
    """

    initialize_workspace = True

    # ── Isolate this test class from the shared "testapp" schema ─────────────
    _TENANT_NAME = "ai_test_app"

    @classmethod
    def get_test_schema_name(cls):
        return cls._TENANT_NAME

    @classmethod
    def get_test_tenant_domain(cls):
        return f"{cls._TENANT_NAME}.testserver.com"

    @classmethod
    def setup_tenant(cls, tenant):
        from zango.apps.shared.tenancy.schema import DEFAULT_AUTH_CONFIG
        tenant.name = cls._TENANT_NAME
        tenant.tenant_type = "app"
        tenant.auth_config = DEFAULT_AUTH_CONFIG
        return tenant

    @classmethod
    def get_test_module_path(cls):
        return os.path.join("apps/ai/test_tool_sync_and_exec")

    @classmethod
    def setUpTestModule(cls):
        """
        Override base class to copy fixtures into workspaces/ai_test_app
        instead of the hardcoded workspaces/testapp used by the base class.
        """
        import shutil
        from pathlib import Path
        from django.conf import settings

        test_module_dir = os.path.join(
            Path(__file__).resolve().parent.parent.parent.parent.parent,
            "tests",
            cls.get_test_module_path(),
        )
        workspace_src_dir = os.path.join(test_module_dir, "workspace")
        migrations_dir = os.path.join(test_module_dir, "migrations")
        base_dir = os.path.join(settings.BASE_DIR, "workspaces")
        os.makedirs(base_dir, exist_ok=True)

        # Ensure workspaces/ and workspaces/ai_test_app/ are Python packages
        # so that Django can import workspaces.ai_test_app.migrations.
        for pkg_dir in [base_dir, os.path.join(base_dir, cls._TENANT_NAME)]:
            init = os.path.join(pkg_dir, "__init__.py")
            if not os.path.exists(init):
                open(init, "w").close()

        if os.path.exists(workspace_src_dir):
            for item in os.listdir(workspace_src_dir):
                src = os.path.join(workspace_src_dir, item)
                dst = os.path.join(base_dir, cls._TENANT_NAME, item)
                if os.path.isdir(src):
                    shutil.copytree(src, dst, dirs_exist_ok=True)
                else:
                    shutil.copy2(src, dst)

        if os.path.exists(migrations_dir):
            shutil.copytree(
                migrations_dir,
                os.path.join(base_dir, cls._TENANT_NAME, "migrations"),
                dirs_exist_ok=True,
            )

    @classmethod
    def clean_workspaces(cls):
        """Remove only our tenant's workspace directory."""
        import shutil
        from django.conf import settings

        ws_path = os.path.join(settings.BASE_DIR, "workspaces", cls._TENANT_NAME)
        if os.path.exists(ws_path):
            shutil.rmtree(ws_path)
            print(f"test workspaces have been deleted.")

    @classmethod
    def setUpClass(cls):
        # Guard: if a previous run left the workspace behind (e.g. setUpClass
        # crashed after initialize_workspace but before tearDownClass could
        # clean it), cookiecutter will refuse to create it again. Pre-clean
        # here so every run starts fresh.
        import shutil
        from django.conf import settings
        ws_path = os.path.join(settings.BASE_DIR, "workspaces", cls._TENANT_NAME)
        if os.path.exists(ws_path):
            shutil.rmtree(ws_path)

        super().setUpClass()
        cls.syn_db()
        # ws_migrate (migrate_schemas) resets connection.tenant to the public schema.
        # Re-set it to the real tenant before using Workspace or any tenant-scoped DB.
        from django.db import connection
        connection.set_tenant(cls.tenant)
        cls.ws = Workspace(cls.tenant, request=None, as_systemuser=True)
        cls.ws.ready()
        mod = cls.ws.plugin_source.load_plugin("ai_test_module.models")
        cls.Patient = mod.Patient

        # Run sync_tools() once — sections 7b, 7c, 7d all depend on AppLLMTool rows
        with tenant_context(cls.tenant):
            cls.ws.sync_tools()

    def setUp(self):
        """
        FastTenantTestCase resets connection.tenant to a FakeTenant between tests.
        Re-set to the real tenant before each test so Workspace() and DB queries
        that use connection.tenant (e.g. ToolExecutor) work correctly.
        """
        from django.db import connection
        connection.set_tenant(self.tenant)

    @classmethod
    @override_settings(TEST_MIGRATION_RUNNING=True)
    def syn_db(cls):
        from django.conf import settings
        original = getattr(settings, "MIGRATION_MODULES", {})
        try:
            call_command("ws_migrate", cls._TENANT_NAME)
        finally:
            settings.MIGRATION_MODULES = original

    # ─── helpers ────────────────────────────────────────────────────────────

    def _make_provider(self, name="test-anthropic"):
        """Create a real AppLLMProvider DB record."""
        from zango.ai.encryption import encrypt_config
        from zango.apps.ai.models.provider import AppLLMProvider

        return AppLLMProvider.objects.create(
            name=name,
            provider_slug="anthropic",
            config_encrypted=encrypt_config({"api_key": "sk-test"}),
            default_model="claude-sonnet-4-20250514",
        )

    def _make_agent(self, name, provider, tools=None, memory_enabled=False):
        """Create a real AppLLMAgent DB record."""
        from zango.apps.ai.models.agent import AppLLMAgent

        return AppLLMAgent.objects.create(
            name=name,
            provider=provider,
            model="claude-sonnet-4-20250514",
            is_enabled=True,
            tools=tools or [],
            memory_enabled=memory_enabled,
            memory_max_messages=20,
        )

    # ─── 7a: sync_tools() ───────────────────────────────────────────────────

    def test_7a_01_sync_creates_expected_tool_count(self):
        """sync_tools() creates exactly 3 AppLLMTool rows for tools.py."""
        from zango.apps.ai.models.tool import AppLLMTool

        with tenant_context(self.tenant):
            # Tools were synced in setUpClass; verify count
            self.assertEqual(AppLLMTool.objects.filter(is_active=True).count(), 3)

    def test_7a_02_expected_tool_names_present(self):
        """The three tool names from tools.py are in the DB after sync."""
        from zango.apps.ai.models.tool import AppLLMTool

        with tenant_context(self.tenant):
            names = set(AppLLMTool.objects.values_list("name", flat=True))
        self.assertIn("get_patient_count", names)
        self.assertIn("create_patient", names)
        self.assertIn("get_patient_by_id", names)

    def test_7a_03_tool_metadata_stored_correctly(self):
        """Tool description, section, timeout_seconds match the @tool decorator."""
        from zango.apps.ai.models.tool import AppLLMTool

        with tenant_context(self.tenant):
            tool = AppLLMTool.objects.get(name="get_patient_count")
        self.assertEqual(tool.section, "patients")
        self.assertEqual(tool.timeout_seconds, 10)
        self.assertIn("patient", tool.description.lower())

    def test_7a_04_create_patient_schema_has_required_params(self):
        """create_patient tool's parameters_schema has 'name' and 'age' properties."""
        from zango.apps.ai.models.tool import AppLLMTool

        with tenant_context(self.tenant):
            tool = AppLLMTool.objects.get(name="create_patient")
        props = tool.parameters_schema.get("properties", {})
        self.assertIn("name", props)
        self.assertIn("age", props)

    def test_7a_05_second_sync_is_idempotent(self):
        """Running sync_tools() a second time creates no new rows (already up to date)."""
        from zango.apps.ai.models.tool import AppLLMTool

        with tenant_context(self.tenant):
            stats = self.ws.sync_tools()
        self.assertEqual(stats["created"], 0)

    def test_7a_06_schema_hash_populated(self):
        """All synced tools have a non-empty schema_hash."""
        from zango.apps.ai.models.tool import AppLLMTool

        with tenant_context(self.tenant):
            tools = list(AppLLMTool.objects.all())
        for tool in tools:
            self.assertTrue(tool.schema_hash, f"{tool.name} has empty schema_hash")

    def test_7a_07_python_path_contains_module_and_function(self):
        """python_path on the DB record contains both the module and function name."""
        from zango.apps.ai.models.tool import AppLLMTool

        with tenant_context(self.tenant):
            tool = AppLLMTool.objects.get(name="create_patient")
        self.assertIn("create_patient", tool.python_path)
        self.assertIn("ai_test_module", tool.python_path)

    # ─── 7b: ToolExecutor real execution ────────────────────────────────────

    def test_7b_01_get_patient_count_returns_zero_when_table_empty(self):
        """get_patient_count returns 0 on an empty Patient table."""
        from zango.ai.tools.executor import ToolExecutor

        with tenant_context(self.tenant):
            self.Patient.objects.all().delete()
            result = ToolExecutor().execute("get_patient_count", {})
        self.assertEqual(result.status, "success")
        self.assertEqual(result.output, 0)

    def test_7b_02_create_patient_inserts_row_and_returns_id(self):
        """create_patient writes a DB row and returns the new record's id, name, age."""
        from zango.ai.tools.executor import ToolExecutor

        with tenant_context(self.tenant):
            result = ToolExecutor().execute(
                "create_patient", {"name": "Alice", "age": 30}
            )
            self.assertEqual(result.status, "success")
            self.assertIn("id", result.output)
            patient = self.Patient.objects.get(pk=result.output["id"])
            self.assertEqual(patient.name, "Alice")
            self.assertEqual(patient.age, 30)

    def test_7b_03_get_patient_count_reflects_created_rows(self):
        """get_patient_count reflects rows created by create_patient."""
        from zango.ai.tools.executor import ToolExecutor

        with tenant_context(self.tenant):
            self.Patient.objects.all().delete()
            self.Patient.objects.create(name="Bob", age=25)
            result = ToolExecutor().execute("get_patient_count", {})
        self.assertEqual(result.status, "success")
        self.assertEqual(result.output, 1)

    def test_7b_04_get_patient_by_id_returns_correct_row(self):
        """get_patient_by_id returns the correct name and age for an existing patient."""
        from zango.ai.tools.executor import ToolExecutor

        with tenant_context(self.tenant):
            p = self.Patient.objects.create(name="Carol", age=45)
            result = ToolExecutor().execute("get_patient_by_id", {"patient_id": p.pk})
        self.assertEqual(result.status, "success")
        self.assertEqual(result.output["name"], "Carol")
        self.assertEqual(result.output["age"], 45)

    def test_7b_05_get_patient_by_id_missing_returns_success_with_error_key(self):
        """get_patient_by_id with a non-existent ID returns status='success', output has 'error'."""
        from zango.ai.tools.executor import ToolExecutor

        with tenant_context(self.tenant):
            result = ToolExecutor().execute("get_patient_by_id", {"patient_id": 9_999_999})
        self.assertEqual(result.status, "success")
        self.assertIn("error", result.output)

    def test_7b_06_execution_time_ms_always_populated(self):
        """execution_time_ms is always set (even for trivial functions)."""
        from zango.ai.tools.executor import ToolExecutor

        with tenant_context(self.tenant):
            result = ToolExecutor().execute("get_patient_count", {})
        self.assertIsNotNone(result.execution_time_ms)
        self.assertGreaterEqual(result.execution_time_ms, 0)

    def test_7b_07_validation_error_on_wrong_type(self):
        """Passing a string for an integer parameter returns validation_error status."""
        from zango.ai.tools.executor import ToolExecutor

        with tenant_context(self.tenant):
            result = ToolExecutor().execute(
                "get_patient_by_id", {"patient_id": "not-an-int"}
            )
        self.assertEqual(result.status, "validation_error")

    def test_7b_08_unknown_tool_returns_error(self):
        """Executing a tool name not in the DB returns status='error'."""
        from zango.ai.tools.executor import ToolExecutor

        with tenant_context(self.tenant):
            result = ToolExecutor().execute("nonexistent_tool", {})
        self.assertEqual(result.status, "error")
        self.assertIn("not found", result.error_message)

    # ─── 7c: AppLLMToolCall records ─────────────────────────────────────────

    @patch("zango.apps.ai.models.provider.AppLLMProvider.get_client")
    def test_7c_01_tool_call_record_created(self, mock_get_client):
        """A single tool-call round writes one AppLLMToolCall record to the DB."""
        from zango.ai.agent_client import AgentClient
        from zango.apps.ai.models.tool import AppLLMToolCall

        raw = _mock_raw_provider()
        raw.complete.side_effect = [
            _make_tool_use_response("create_patient", {"name": "Dave", "age": 22}),
            _make_final_response("Patient created."),
        ]
        mock_get_client.return_value = raw

        with tenant_context(self.tenant):
            provider = self._make_provider("tc01-provider")
            agent = self._make_agent("tc01-agent", provider, tools=["create_patient"])
            AgentClient(agent).run(input="Create patient Dave")
            count = AppLLMToolCall.objects.filter(tool_name="create_patient").count()
        self.assertEqual(count, 1)

    @patch("zango.apps.ai.models.provider.AppLLMProvider.get_client")
    def test_7c_02_tool_call_record_fields_correct(self, mock_get_client):
        """AppLLMToolCall stores correct tool_name, tool_input, status, round_number."""
        from zango.ai.agent_client import AgentClient
        from zango.apps.ai.models.tool import AppLLMToolCall

        raw = _mock_raw_provider()
        raw.complete.side_effect = [
            _make_tool_use_response("create_patient", {"name": "Eve", "age": 35}),
            _make_final_response("Done."),
        ]
        mock_get_client.return_value = raw

        with tenant_context(self.tenant):
            provider = self._make_provider("tc02-provider")
            agent = self._make_agent("tc02-agent", provider, tools=["create_patient"])
            AgentClient(agent).run(input="Create patient Eve")
            call_record = AppLLMToolCall.objects.get(
                tool_name="create_patient",
                tool_input={"name": "Eve", "age": 35},
            )

        self.assertEqual(call_record.status, "success")
        self.assertEqual(call_record.round_number, 1)
        self.assertIsNotNone(call_record.execution_time_ms)

    @patch("zango.apps.ai.models.provider.AppLLMProvider.get_client")
    def test_7c_03_tool_call_output_stored(self, mock_get_client):
        """AppLLMToolCall.tool_output contains the dict returned by the tool function."""
        from zango.ai.agent_client import AgentClient
        from zango.apps.ai.models.tool import AppLLMToolCall

        raw = _mock_raw_provider()
        raw.complete.side_effect = [
            _make_tool_use_response("create_patient", {"name": "Frank", "age": 50}),
            _make_final_response("Done."),
        ]
        mock_get_client.return_value = raw

        with tenant_context(self.tenant):
            provider = self._make_provider("tc03-provider")
            agent = self._make_agent("tc03-agent", provider, tools=["create_patient"])
            AgentClient(agent).run(input="Create Frank")
            call_record = AppLLMToolCall.objects.get(
                tool_name="create_patient",
                tool_input={"name": "Frank", "age": 50},
            )

        self.assertIsNotNone(call_record.tool_output)
        self.assertIn("id", call_record.tool_output)
        self.assertEqual(call_record.tool_output["name"], "Frank")

    @patch("zango.apps.ai.models.provider.AppLLMProvider.get_client")
    def test_7c_04_tool_fk_linked_to_appllmtool(self, mock_get_client):
        """AppLLMToolCall.tool FK points to the correct AppLLMTool row."""
        from zango.ai.agent_client import AgentClient
        from zango.apps.ai.models.tool import AppLLMTool, AppLLMToolCall

        raw = _mock_raw_provider()
        raw.complete.side_effect = [
            _make_tool_use_response("get_patient_count", {}),
            _make_final_response("Count retrieved."),
        ]
        mock_get_client.return_value = raw

        with tenant_context(self.tenant):
            provider = self._make_provider("tc04-provider")
            agent = self._make_agent("tc04-agent", provider, tools=["get_patient_count"])
            AgentClient(agent).run(input="How many?")
            call_record = AppLLMToolCall.objects.filter(tool_name="get_patient_count").last()
            db_tool = AppLLMTool.objects.get(name="get_patient_count")

        self.assertEqual(call_record.tool_id, db_tool.pk)

    @patch("zango.apps.ai.models.provider.AppLLMProvider.get_client")
    def test_7c_05_tool_total_calls_incremented(self, mock_get_client):
        """AppLLMTool.total_calls is incremented after a successful execution."""
        from zango.ai.agent_client import AgentClient
        from zango.apps.ai.models.tool import AppLLMTool

        raw = _mock_raw_provider()
        raw.complete.side_effect = [
            _make_tool_use_response("get_patient_count", {}),
            _make_final_response("Done."),
        ]
        mock_get_client.return_value = raw

        with tenant_context(self.tenant):
            provider = self._make_provider("tc05-provider")
            agent = self._make_agent("tc05-agent", provider, tools=["get_patient_count"])
            before = AppLLMTool.objects.get(name="get_patient_count").total_calls
            AgentClient(agent).run(input="Count")
            after = AppLLMTool.objects.get(name="get_patient_count").total_calls

        self.assertEqual(after, before + 1)

    # ─── 7d: AppLLMMemorySession + AppLLMMemoryMessage ───────────────────────

    @patch("zango.apps.ai.models.provider.AppLLMProvider.get_client")
    def test_7d_01_first_run_creates_session(self, mock_get_client):
        """The first agent.run() with memory_enabled creates an AppLLMMemorySession."""
        from zango.ai.agent_client import AgentClient
        from zango.apps.ai.models.memory import AppLLMMemorySession

        raw = _mock_raw_provider()
        mock_get_client.return_value = raw

        with tenant_context(self.tenant):
            provider = self._make_provider("mem01-provider")
            agent = self._make_agent("mem01-agent", provider, memory_enabled=True)
            response = AgentClient(agent).run(input="Hello")
            session_id = response.session_id
            self.assertIsNotNone(session_id)
            session = AppLLMMemorySession.objects.filter(
                agent=agent, session_id=session_id
            ).first()
        self.assertIsNotNone(session)
        self.assertTrue(session.is_active)

    @patch("zango.apps.ai.models.provider.AppLLMProvider.get_client")
    def test_7d_02_first_run_stores_user_and_assistant_messages(self, mock_get_client):
        """After first run, user input and assistant response are stored in order."""
        from zango.ai.agent_client import AgentClient
        from zango.apps.ai.models.memory import AppLLMMemorySession

        raw = _mock_raw_provider()
        raw.complete.return_value = _make_final_response("Hi, I can help!")
        mock_get_client.return_value = raw

        with tenant_context(self.tenant):
            provider = self._make_provider("mem02-provider")
            agent = self._make_agent("mem02-agent", provider, memory_enabled=True)
            response = AgentClient(agent).run(input="Hi there")
            session = AppLLMMemorySession.objects.get(
                agent=agent, session_id=response.session_id
            )
            messages = list(session.messages.order_by("sequence"))

        self.assertEqual(len(messages), 2)
        self.assertEqual(messages[0].role, "user")
        self.assertEqual(messages[0].content, "Hi there")
        self.assertEqual(messages[1].role, "assistant")
        self.assertEqual(messages[1].content, "Hi, I can help!")

    @patch("zango.apps.ai.models.provider.AppLLMProvider.get_client")
    def test_7d_03_second_run_same_session_appends_messages(self, mock_get_client):
        """A second run with the same session_id appends two more messages (user+assistant)."""
        from zango.ai.agent_client import AgentClient
        from zango.apps.ai.models.memory import AppLLMMemorySession

        raw = _mock_raw_provider()
        raw.complete.side_effect = [
            _make_final_response("Reply one."),
            _make_final_response("Reply two."),
        ]
        mock_get_client.return_value = raw

        with tenant_context(self.tenant):
            provider = self._make_provider("mem03-provider")
            agent = self._make_agent("mem03-agent", provider, memory_enabled=True)
            r1 = AgentClient(agent).run(input="Turn one")
            AgentClient(agent).run(input="Turn two", session_id=r1.session_id)
            session = AppLLMMemorySession.objects.get(
                agent=agent, session_id=r1.session_id
            )
            messages = list(session.messages.order_by("sequence"))

        self.assertEqual(len(messages), 4)
        self.assertEqual([m.role for m in messages], ["user", "assistant", "user", "assistant"])

    @patch("zango.apps.ai.models.provider.AppLLMProvider.get_client")
    def test_7d_04_explicit_session_id_reuses_single_session_row(self, mock_get_client):
        """Passing an explicit session_id twice reuses the same AppLLMMemorySession row."""
        from zango.ai.agent_client import AgentClient
        from zango.apps.ai.models.memory import AppLLMMemorySession

        raw = _mock_raw_provider()
        mock_get_client.return_value = raw
        session_id = "explicit-session-99"

        with tenant_context(self.tenant):
            provider = self._make_provider("mem04-provider")
            agent = self._make_agent("mem04-agent", provider, memory_enabled=True)
            AgentClient(agent).run(input="First", session_id=session_id)
            AgentClient(agent).run(input="Second", session_id=session_id)
            count = AppLLMMemorySession.objects.filter(
                agent=agent, session_id=session_id
            ).count()
        self.assertEqual(count, 1)

    @patch("zango.apps.ai.models.provider.AppLLMProvider.get_client")
    def test_7d_05_memory_disabled_no_session_created(self, mock_get_client):
        """Agents with memory_enabled=False create no AppLLMMemorySession records."""
        from zango.ai.agent_client import AgentClient
        from zango.apps.ai.models.memory import AppLLMMemorySession

        raw = _mock_raw_provider()
        mock_get_client.return_value = raw

        with tenant_context(self.tenant):
            provider = self._make_provider("mem05-provider")
            agent = self._make_agent("mem05-agent", provider, memory_enabled=False)
            response = AgentClient(agent).run(input="Hello")
            count = AppLLMMemorySession.objects.filter(agent=agent).count()

        self.assertIsNone(response.session_id)
        self.assertEqual(count, 0)

    @patch("zango.apps.ai.models.provider.AppLLMProvider.get_client")
    def test_7d_06_sequence_numbers_monotonically_increasing(self, mock_get_client):
        """Message sequence numbers in a session are monotonically increasing."""
        from zango.ai.agent_client import AgentClient
        from zango.apps.ai.models.memory import AppLLMMemorySession

        raw = _mock_raw_provider()
        raw.complete.side_effect = [
            _make_final_response("A"),
            _make_final_response("B"),
            _make_final_response("C"),
        ]
        mock_get_client.return_value = raw

        with tenant_context(self.tenant):
            provider = self._make_provider("mem06-provider")
            agent = self._make_agent("mem06-agent", provider, memory_enabled=True)
            r1 = AgentClient(agent).run(input="Q1")
            sid = r1.session_id
            AgentClient(agent).run(input="Q2", session_id=sid)
            AgentClient(agent).run(input="Q3", session_id=sid)
            session = AppLLMMemorySession.objects.get(agent=agent, session_id=sid)
            seqs = list(
                session.messages.order_by("sequence").values_list("sequence", flat=True)
            )

        for i in range(1, len(seqs)):
            self.assertGreater(seqs[i], seqs[i - 1], f"seq[{i}]={seqs[i]} <= seq[{i-1}]={seqs[i-1]}")
