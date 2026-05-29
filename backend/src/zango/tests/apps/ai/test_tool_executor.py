"""
Unit tests for ToolExecutor (zango.ai.tools.executor).

Three sub-groups:
  a) _validate_input  — pure jsonschema, no mocking
  b) _serialize_output — pure type conversion, no mocking
  c) execute()        — DB (AppLLMTool) and workspace (Workspace/plugin_source) mocked

The executor never raises — all outcomes land in ToolResult.
"""

import datetime
from decimal import Decimal
from unittest.mock import MagicMock, patch

from django.test import SimpleTestCase

from zango.ai.tools.executor import ToolExecutor

SCHEMA_INT_ID = {
    "type": "object",
    "properties": {"employee_id": {"type": "integer"}},
    "required": ["employee_id"],
}

SCHEMA_TWO_PARAMS = {
    "type": "object",
    "properties": {
        "name": {"type": "string"},
        "age": {"type": "integer"},
    },
    "required": ["name", "age"],
}


def _make_tool_record(schema=None, timeout=30, python_path="myapp.tools.my_func"):
    record = MagicMock()
    record.parameters_schema = schema or SCHEMA_INT_ID
    record.timeout_seconds = timeout
    record.python_path = python_path
    return record


# ─── a) Input validation ──────────────────────────────────────────────────────

class ValidateInputTest(SimpleTestCase):

    def _validate(self, tool_input, schema=None):
        return ToolExecutor()._validate_input(tool_input, schema or SCHEMA_INT_ID)

    def test_valid_input_returns_none(self):
        self.assertIsNone(self._validate({"employee_id": 42}))

    def test_wrong_type_returns_error_string(self):
        result = self._validate({"employee_id": "not-an-int"})
        self.assertIsNotNone(result)
        self.assertIsInstance(result, str)

    def test_missing_required_field_returns_error(self):
        result = self._validate({})
        self.assertIsNotNone(result)

    def test_extra_field_is_allowed(self):
        # additionalProperties not restricted — extra field must not cause failure
        self.assertIsNone(self._validate({"employee_id": 1, "extra": True}))

    def test_broken_schema_returns_error_string_not_exception(self):
        result = ToolExecutor()._validate_input({"x": 1}, {"type": "not_a_real_type"})
        self.assertIsNotNone(result)
        self.assertIsInstance(result, str)


# ─── b) Output serialization ──────────────────────────────────────────────────

class SerializeOutputTest(SimpleTestCase):

    def _serialize(self, value):
        return ToolExecutor()._serialize_output(value)

    def test_none_returns_none(self):
        self.assertIsNone(self._serialize(None))

    def test_string_identity(self):
        self.assertEqual(self._serialize("hello"), "hello")

    def test_int_identity(self):
        self.assertEqual(self._serialize(42), 42)

    def test_float_identity(self):
        self.assertAlmostEqual(self._serialize(3.14), 3.14)

    def test_bool_identity_not_cast_to_int(self):
        result = self._serialize(True)
        self.assertIs(result, True)

    def test_decimal_converted_to_float(self):
        result = self._serialize(Decimal("9.99"))
        self.assertAlmostEqual(result, 9.99)
        self.assertIsInstance(result, float)

    def test_datetime_converted_to_iso_string(self):
        dt = datetime.datetime(2024, 1, 15, 12, 0, 0)
        self.assertEqual(self._serialize(dt), "2024-01-15T12:00:00")

    def test_date_converted_to_iso_string(self):
        d = datetime.date(2024, 1, 15)
        self.assertEqual(self._serialize(d), "2024-01-15")

    def test_set_converted_to_list(self):
        result = self._serialize({1, 2, 3})
        self.assertIsInstance(result, list)
        self.assertEqual(sorted(result), [1, 2, 3])

    def test_bytes_converted_to_base64_string(self):
        import base64 as b64
        result = self._serialize(b"hello")
        self.assertEqual(result, b64.b64encode(b"hello").decode("ascii"))

    def test_large_output_truncated(self):
        # dict whose JSON representation exceeds 50 000 chars
        large = {"key": "x" * 60_000}
        result = self._serialize(large)
        # Result must be JSON-parseable and ≤ 50 000 chars when re-serialised
        import json
        self.assertLessEqual(len(json.dumps(result)), 50_000)

    def test_non_serializable_falls_back_to_str(self):
        class Unserializable:
            def __repr__(self):
                return "Unserializable()"
        result = self._serialize(Unserializable())
        self.assertIsInstance(result, str)


# ─── c) Execution paths ───────────────────────────────────────────────────────

class ExecuteTest(SimpleTestCase):

    # All three are lazy-imported inside execute() — patch at canonical paths.
    _TOOL_MODEL = "zango.apps.ai.models.tool.AppLLMTool"
    _WORKSPACE = "zango.apps.dynamic_models.workspace.base.Workspace"
    _CONNECTION = "zango.db.connection"  # patched via django.db.connection

    def _run(self, tool_name, tool_input, tool_record, mock_func=None):
        """Helper: patch DB + workspace and call execute()."""
        with patch(self._TOOL_MODEL) as mock_model:
            mock_model.objects.get.return_value = tool_record
            with patch(self._WORKSPACE) as mock_ws_cls:
                with patch("django.db.connection") as mock_conn:
                    mock_conn.tenant = MagicMock()
                    mock_ws = MagicMock()
                    mock_ws_cls.return_value = mock_ws

                    if mock_func is not None:
                        module_mock = MagicMock()
                        func_name = tool_record.python_path.rsplit(".", 1)[1]
                        setattr(module_mock, func_name, mock_func)
                        mock_ws.plugin_source.load_plugin.return_value = module_mock

                    return ToolExecutor().execute(tool_name, tool_input)

    def test_tool_not_in_db_returns_error(self):
        with patch(self._TOOL_MODEL) as mock_model:
            mock_model.objects.get.side_effect = Exception("DoesNotExist")
            result = ToolExecutor().execute("nonexistent_tool", {})

        self.assertEqual(result.status, "error")
        self.assertIn("not found", result.error_message)

    def test_workspace_import_failure_returns_error(self):
        tool_record = _make_tool_record()
        with patch(self._TOOL_MODEL) as mock_model:
            mock_model.objects.get.return_value = tool_record
            with patch(self._WORKSPACE) as mock_ws_cls:
                with patch("django.db.connection") as mock_conn:
                    mock_conn.tenant = MagicMock()
                    mock_ws_cls.return_value.plugin_source.load_plugin.side_effect = (
                        ImportError("module not found")
                    )
                    result = ToolExecutor().execute("my_func", {"employee_id": 1})

        self.assertEqual(result.status, "error")
        self.assertIn("import failed", result.error_message)

    def test_validation_failure_returns_validation_error(self):
        tool_record = _make_tool_record(schema=SCHEMA_INT_ID)
        # Pass string where integer is required — validation fires before execution
        result = self._run("my_func", {"employee_id": "bad"}, tool_record,
                           mock_func=MagicMock(return_value={}))
        self.assertEqual(result.status, "validation_error")

    def test_validation_failure_does_not_call_function(self):
        tool_record = _make_tool_record(schema=SCHEMA_INT_ID)
        mock_func = MagicMock(return_value={})
        self._run("my_func", {"employee_id": "bad"}, tool_record, mock_func=mock_func)
        mock_func.assert_not_called()

    def test_successful_execution_dict_return(self):
        tool_record = _make_tool_record()
        result = self._run(
            "my_func", {"employee_id": 42}, tool_record,
            mock_func=MagicMock(return_value={"score": 95})
        )
        self.assertEqual(result.status, "success")
        self.assertEqual(result.output, {"score": 95})

    def test_successful_execution_int_return(self):
        tool_record = _make_tool_record()
        result = self._run(
            "my_func", {"employee_id": 42}, tool_record,
            mock_func=MagicMock(return_value=7)
        )
        self.assertEqual(result.status, "success")
        self.assertEqual(result.output, 7)

    def test_function_raises_returns_error_with_traceback(self):
        tool_record = _make_tool_record()
        mock_func = MagicMock(side_effect=ValueError("something went wrong"))
        result = self._run("my_func", {"employee_id": 1}, tool_record, mock_func=mock_func)
        self.assertEqual(result.status, "error")
        self.assertIsNotNone(result.error_traceback)
        self.assertIn("ValueError", result.error_traceback)

    def test_execution_time_ms_always_set(self):
        tool_record = _make_tool_record()
        result = self._run(
            "my_func", {"employee_id": 1}, tool_record,
            mock_func=MagicMock(return_value={})
        )
        self.assertIsNotNone(result.execution_time_ms)
        self.assertGreaterEqual(result.execution_time_ms, 0)

    def test_execution_time_ms_set_even_on_validation_error(self):
        tool_record = _make_tool_record(schema=SCHEMA_INT_ID)
        result = self._run("my_func", {}, tool_record,
                           mock_func=MagicMock(return_value={}))
        self.assertIsNotNone(result.execution_time_ms)
        self.assertGreaterEqual(result.execution_time_ms, 0)
