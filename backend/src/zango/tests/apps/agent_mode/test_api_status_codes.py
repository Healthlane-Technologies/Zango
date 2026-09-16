"""The panel's shared `useApi` hook grades only 2xx as success, and before this
test it graded only 200/201 — a 202 from any platform endpoint surfaced to the
user as a generic "Server Error" on a request that had actually succeeded.

That is exactly what happened on `requirements/<uuid>/messages/`: the POST was
accepted and the analyst turn was queued, but the chat reported a failure, so
the user re-sent and got 409 "The agent is still replying".

These tests pin the contract from both ends by reading the source, so neither
half can drift back without failing.
"""

import re

from pathlib import Path
from unittest import TestCase

import zango


BACKEND_SRC = Path(zango.__file__).resolve().parent
REPO_FRONTEND = BACKEND_SRC.parents[2] / "frontend"
AGENT_MODE_VIEWS = BACKEND_SRC / "api/platform/agent_mode/v1/views.py"
USE_API = REPO_FRONTEND / "src/hooks/useApi.jsx"


class AgentModeResponseStatusTests(TestCase):
    def test_no_view_returns_a_status_the_panel_cannot_grade(self):
        """Every agent_mode response must use a code `useApi` understands.

        200/201 are success; 400/409/500 have explicit branches. Anything else
        — 202 included — falls through to the generic error path.
        """
        source = AGENT_MODE_VIEWS.read_text()
        codes = {int(m) for m in re.findall(r"get_api_response\([^()]*?,\s*(\d{3})\)", source)}
        # Multi-line calls are the common form; catch their trailing status too.
        codes |= {int(m) for m in re.findall(r"^\s*(\d{3}),\s*$", source, re.M)}
        understood = {200, 201, 400, 404, 409, 500}
        self.assertTrue(
            codes,
            "parsed no status codes — the regex no longer matches the views",
        )
        self.assertEqual(
            codes - understood,
            set(),
            f"agent_mode returns status codes the panel renders as errors: "
            f"{sorted(codes - understood)}",
        )

    def test_messages_endpoint_returns_200(self):
        """The specific regression: this endpoint returned 202."""
        source = AGENT_MODE_VIEWS.read_text()
        start = source.index("class AgentRequirementMessageView")
        body = source[start : source.index("\nclass ", start + 1)]
        self.assertIn(
            'get_api_response(True, {"status": requirement.status}, 200)',
            body,
            "the messages endpoint must return 200 — the panel renders 202 as "
            "a generic Server Error",
        )


class UseApiSuccessRangeTests(TestCase):
    """The other half of the fix: the hook should accept any 2xx."""

    def test_hook_treats_all_2xx_as_success(self):
        if not USE_API.exists():  # installed package, no frontend tree
            self.skipTest("frontend sources not present")
        source = USE_API.read_text()
        self.assertIn(
            "apiRequest.status >= 200 && apiRequest.status < 300",
            source,
            "useApi must grade the whole 2xx range as success",
        )
        self.assertNotIn(
            "apiRequest.status === 200 || apiRequest.status === 201",
            source,
            "the narrow 200/201 success check is back — a 202 will render as "
            "'Server Error' again",
        )

    def test_hook_handles_bodyless_success_responses(self):
        if not USE_API.exists():
            self.skipTest("frontend sources not present")
        source = USE_API.read_text()
        self.assertIn(
            "apiRequest.status === 204 || apiRequest.status === 205",
            source,
            "204/205 carry no body; json() throws and the catch reports "
            "'Server Error' for a successful call",
        )
