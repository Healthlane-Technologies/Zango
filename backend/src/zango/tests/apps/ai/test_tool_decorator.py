"""
Unit tests for the @tool decorator (zango.ai.tools.decorator).

These are pure Python tests — no DB, no workspace, no tenant context required.
The decorator is a code-analysis tool that generates JSON Schema from function
signatures at definition time, so all assertions can be made on the decorated
function's _tool_meta attribute directly.
"""

from typing import Optional
from django.test import SimpleTestCase

from zango.ai.tools.decorator import ToolParam, ToolSafety, tool


class ToolDecoratorSchemaTest(SimpleTestCase):
    """Tests that @tool generates correct JSON Schema from type annotations."""

    def test_required_field_no_default(self):
        """A ToolParam without a default must appear in 'required'."""

        @tool(name="t", description="d")
        def my_tool(employee_id: int = ToolParam(description="The employee ID")):
            return {}

        schema = my_tool._tool_meta.parameters_schema
        self.assertIn("employee_id", schema["required"])

    def test_optional_field_with_default_not_required(self):
        """A ToolParam with a default must NOT appear in 'required'."""

        @tool(name="t", description="d")
        def my_tool(days: int = ToolParam(description="Look-back days", default=7)):
            return {}

        schema = my_tool._tool_meta.parameters_schema
        self.assertNotIn("days", schema["required"])

    def test_mixed_required_and_optional(self):
        """Only params without defaults are required."""

        @tool(name="t", description="d")
        def my_tool(
            employee_id: int = ToolParam(description="The ID"),
            days: int = ToolParam(description="Days", default=7),
        ):
            return {}

        schema = my_tool._tool_meta.parameters_schema
        self.assertIn("employee_id", schema["required"])
        self.assertNotIn("days", schema["required"])

    def test_int_maps_to_integer(self):
        @tool(name="t", description="d")
        def my_tool(count: int = ToolParam(description="Count")):
            return {}

        prop = my_tool._tool_meta.parameters_schema["properties"]["count"]
        self.assertEqual(prop["type"], "integer")

    def test_str_maps_to_string(self):
        @tool(name="t", description="d")
        def my_tool(name: str = ToolParam(description="Name")):
            return {}

        prop = my_tool._tool_meta.parameters_schema["properties"]["name"]
        self.assertEqual(prop["type"], "string")

    def test_bool_maps_to_boolean(self):
        @tool(name="t", description="d")
        def my_tool(active: bool = ToolParam(description="Active flag")):
            return {}

        prop = my_tool._tool_meta.parameters_schema["properties"]["active"]
        self.assertEqual(prop["type"], "boolean")

    def test_float_maps_to_number(self):
        @tool(name="t", description="d")
        def my_tool(score: float = ToolParam(description="Score")):
            return {}

        prop = my_tool._tool_meta.parameters_schema["properties"]["score"]
        self.assertEqual(prop["type"], "number")

    def test_list_int_maps_to_array_of_integer(self):
        @tool(name="t", description="d")
        def my_tool(ids: list[int] = ToolParam(description="List of IDs")):
            return {}

        prop = my_tool._tool_meta.parameters_schema["properties"]["ids"]
        self.assertEqual(prop["type"], "array")
        self.assertEqual(prop["items"], {"type": "integer"})

    def test_dict_maps_to_object(self):
        @tool(name="t", description="d")
        def my_tool(data: dict = ToolParam(description="Data payload")):
            return {}

        prop = my_tool._tool_meta.parameters_schema["properties"]["data"]
        self.assertEqual(prop["type"], "object")

    def test_optional_str_unwrapped_to_string(self):
        """Optional[str] should produce type=string, not a union."""

        @tool(name="t", description="d")
        def my_tool(tag: Optional[str] = ToolParam(description="Tag", default=None)):
            return {}

        prop = my_tool._tool_meta.parameters_schema["properties"]["tag"]
        self.assertEqual(prop["type"], "string")

    def test_enum_values_included_in_schema(self):
        @tool(name="t", description="d")
        def my_tool(
            status: str = ToolParam(
                description="Status", enum=["active", "inactive", "pending"]
            )
        ):
            return {}

        prop = my_tool._tool_meta.parameters_schema["properties"]["status"]
        self.assertEqual(prop["enum"], ["active", "inactive", "pending"])

    def test_description_set_on_property(self):
        @tool(name="t", description="d")
        def my_tool(employee_id: int = ToolParam(description="The employee's DB ID")):
            return {}

        prop = my_tool._tool_meta.parameters_schema["properties"]["employee_id"]
        self.assertEqual(prop["description"], "The employee's DB ID")

    def test_schema_hash_changes_when_type_changes(self):
        """Changing a param type must produce a different schema_hash."""

        @tool(name="t", description="d")
        def v1(employee_id: int = ToolParam(description="ID")):
            return {}

        @tool(name="t", description="d")
        def v2(employee_id: str = ToolParam(description="ID")):
            return {}

        self.assertNotEqual(v1._tool_meta.schema_hash, v2._tool_meta.schema_hash)

    def test_schema_hash_changes_when_required_changes(self):
        """Making a param required vs optional must change the hash."""

        @tool(name="t", description="d")
        def required_ver(days: int = ToolParam(description="Days")):
            return {}

        @tool(name="t", description="d")
        def optional_ver(days: int = ToolParam(description="Days", default=7)):
            return {}

        self.assertNotEqual(
            required_ver._tool_meta.schema_hash, optional_ver._tool_meta.schema_hash
        )

    def test_schema_hash_identical_for_same_signature(self):
        """Two functions with identical signatures must produce the same hash."""

        @tool(name="t", description="d")
        def a(employee_id: int = ToolParam(description="ID")):
            return {}

        @tool(name="t", description="d")
        def b(employee_id: int = ToolParam(description="ID")):
            return {}

        self.assertEqual(a._tool_meta.schema_hash, b._tool_meta.schema_hash)


class ToolDecoratorMetaTest(SimpleTestCase):
    """Tests that @tool stores decorator arguments correctly on _tool_meta."""

    def test_name_stored(self):
        @tool(name="get_employee_scores", description="d")
        def my_tool():
            return {}

        self.assertEqual(my_tool._tool_meta.name, "get_employee_scores")

    def test_description_stored(self):
        @tool(name="t", description="Retrieve assessment scores for an employee")
        def my_tool():
            return {}

        self.assertEqual(
            my_tool._tool_meta.description, "Retrieve assessment scores for an employee"
        )

    def test_section_default_is_general(self):
        @tool(name="t", description="d")
        def my_tool():
            return {}

        self.assertEqual(my_tool._tool_meta.section, "general")

    def test_section_custom(self):
        @tool(name="t", description="d", section="assessments")
        def my_tool():
            return {}

        self.assertEqual(my_tool._tool_meta.section, "assessments")

    def test_safety_default_is_read_only(self):
        @tool(name="t", description="d")
        def my_tool():
            return {}

        self.assertEqual(my_tool._tool_meta.safety, ToolSafety.READ_ONLY)

    def test_safety_custom(self):
        @tool(name="t", description="d", safety=ToolSafety.WRITE)
        def my_tool():
            return {}

        self.assertEqual(my_tool._tool_meta.safety, ToolSafety.WRITE)

    def test_timeout_default(self):
        @tool(name="t", description="d")
        def my_tool():
            return {}

        self.assertEqual(my_tool._tool_meta.timeout_seconds, 30)

    def test_timeout_custom(self):
        @tool(name="t", description="d", timeout_seconds=60)
        def my_tool():
            return {}

        self.assertEqual(my_tool._tool_meta.timeout_seconds, 60)

    def test_python_path_set_correctly(self):
        @tool(name="t", description="d")
        def my_tool():
            return {}

        # python_path should end with the function's qualified name
        self.assertTrue(
            my_tool._tool_meta.python_path.endswith("my_tool"),
            msg=f"Unexpected python_path: {my_tool._tool_meta.python_path}",
        )

    def test_return_type_captured(self):
        @tool(name="t", description="d")
        def my_tool() -> dict:
            return {}

        self.assertEqual(my_tool._tool_meta.return_type, "dict")

    def test_return_type_none_when_no_annotation(self):
        @tool(name="t", description="d")
        def my_tool():
            return {}

        self.assertIsNone(my_tool._tool_meta.return_type)

    def test_decorated_function_still_callable(self):
        """The decorator must not break the wrapped function."""

        @tool(name="t", description="d")
        def my_tool(x: int = ToolParam(description="x")) -> int:
            return x * 2

        self.assertEqual(my_tool(x=5), 10)

    def test_rate_limit_default_is_none(self):
        @tool(name="t", description="d")
        def my_tool():
            return {}

        self.assertIsNone(my_tool._tool_meta.rate_limit)

    def test_rate_limit_custom(self):
        @tool(name="t", description="d", rate_limit=100)
        def my_tool():
            return {}

        self.assertEqual(my_tool._tool_meta.rate_limit, 100)
