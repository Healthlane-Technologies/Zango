"""Agent create/update serializers: the output_json_schema field, checked on its own."""

from django.test import SimpleTestCase
from rest_framework.exceptions import ValidationError

from zango.api.platform.ai.v1.serializers import (
    AppLLMAgentCreateSerializer,
    AppLLMAgentUpdateSerializer,
)


class OutputJsonSchemaTest(SimpleTestCase):
    def field(self, cls):
        return cls().fields["output_json_schema"]

    def test_create_takes_a_null_schema(self):
        # App Studio sends null for agents whose output is text or markdown
        self.assertIsNone(self.field(AppLLMAgentCreateSerializer).run_validation(None))

    def test_update_takes_a_null_schema(self):
        self.assertIsNone(self.field(AppLLMAgentUpdateSerializer).run_validation(None))

    def test_create_still_checks_a_schema_given(self):
        s = AppLLMAgentCreateSerializer()
        with self.assertRaises(ValidationError):
            s.validate_output_json_schema({"properties": {}})
