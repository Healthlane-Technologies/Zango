"""Phase 1 — spec extraction and conversation helpers.

The ```zango-spec fence is the contract between the analyst and the platform:
if parsing drifts, the UI never offers the spec for approval and the whole
phase silently stalls.
"""

import unittest

from zango.apps.agent_mode.requirements import (
    ANALYST_DISALLOWED,
    ANALYST_SKILL,
    ANALYST_TOOLS,
    derive_title,
    extract_spec,
    looks_like_question,
    strip_fences,
)


SPEC = """## Appointment Scheduling

### Entities
- Appointment
"""


class SpecExtractionTests(unittest.TestCase):
    def test_no_fence_means_still_gathering(self):
        self.assertEqual(extract_spec("A few questions first:\n1. Who books?"), "")

    def test_extracts_fenced_spec(self):
        reply = f"Here's the requirement.\n\n```zango-spec\n{SPEC}```\n"
        self.assertEqual(
            extract_spec(reply).splitlines()[0], "## Appointment Scheduling"
        )

    def test_last_fence_wins_on_revision(self):
        reply = (
            "```zango-spec\n## Old\n```\n"
            "On reflection:\n"
            "```zango-spec\n## New\n```"
        )
        self.assertEqual(extract_spec(reply).strip(), "## New")

    def test_fence_tag_is_case_insensitive(self):
        self.assertTrue(extract_spec("```ZANGO-SPEC\n## X\n```"))

    def test_ordinary_code_fence_is_not_a_spec(self):
        self.assertEqual(extract_spec("```python\nprint(1)\n```"), "")

    def test_chat_text_excludes_the_spec_block(self):
        reply = f"Ready for review.\n\n```zango-spec\n{SPEC}```\n"
        chat = strip_fences(reply)
        self.assertIn("Ready for review.", chat)
        self.assertNotIn("Appointment", chat)

    def test_question_detection_drives_the_reply_affordance(self):
        self.assertTrue(looks_like_question("Who books the appointment?"))
        self.assertFalse(looks_like_question("I've drafted the requirement."))


class TitleTests(unittest.TestCase):
    def test_title_from_first_heading(self):
        self.assertEqual(derive_title(SPEC, "fallback"), "Appointment Scheduling")

    def test_falls_back_to_the_opening_ask(self):
        self.assertEqual(
            derive_title("", "Build a task tracker"), "Build a task tracker"
        )

    def test_title_is_bounded(self):
        self.assertLessEqual(len(derive_title("", "x" * 900)), 255)


class AnalystConfigTests(unittest.TestCase):
    def test_analyst_is_read_only(self):
        # The whole point of phase 1 is that it cannot touch the app.
        for tool in ("Write", "Edit", "MultiEdit", "Bash"):
            self.assertNotIn(tool, ANALYST_TOOLS)
            self.assertIn(tool, ANALYST_DISALLOWED)

    def test_analyst_can_inspect(self):
        for tool in ("Read", "Glob", "Grep"):
            self.assertIn(tool, ANALYST_TOOLS)

    def test_skill_is_plugin_qualified(self):
        self.assertEqual(ANALYST_SKILL, "zango-agent-mode:zango-requirements-analyst")


if __name__ == "__main__":
    unittest.main()


class ResumeTests(unittest.TestCase):
    """A build that stops partway leaves real work on disk. Resuming must
    continue from it, not start over."""

    def test_resume_prompt_forbids_restarting(self):
        from zango.apps.agent_mode.prompt import compose_resume_prompt

        class Ctx:
            app_name = "TenderApp"
            workspace_path = "/ws"
            schema_name = "s"
            primary_domain = "t.local"
            packages = [{"name": "crud", "version": "1.0.17"}]
            modules = [{"name": "tenders", "path": "backend.tenders"}]
            roles = ["Admin"]
            appbuilder_config_url = "http://t.local/appbuilder/configure"
            appbuilder_token = "tok"
            appbuilder_reason = ""

        text = compose_resume_prompt(
            "## Spec", Ctx(), "AgentError: Credit balance is too low"
        )
        self.assertIn("RESUMING", text)
        self.assertIn("Do not start over", text)
        self.assertIn("Credit balance is too low", text)
        # The requirement itself must still be present.
        self.assertIn("## Spec", text)
        # And the normal build constraints must survive.
        self.assertIn("ws_makemigration", text)

    def test_resumable_statuses(self):
        from zango.api.platform.agent_mode.v1.views import AgentRunResumeView

        for status in ("failed", "timeout", "aborted", "partial"):
            self.assertIn(status, AgentRunResumeView.RESUMABLE)
        # Nothing to continue from a clean finish.
        self.assertNotIn("success", AgentRunResumeView.RESUMABLE)
        self.assertNotIn("running", AgentRunResumeView.RESUMABLE)


class TitleFromSpecTests(unittest.TestCase):
    """The title is shown as the app's name — on the requirement list, in the
    Share and Deploy dialogs, and in "<name> is live".

    It starts as the opening ask truncated to 80 characters, which is a
    sentence. Once the spec names the app, that name has to take over, or the
    panel reads "I want to build an app for managing tenders… is live".
    """

    def test_spec_heading_replaces_the_placeholder(self):
        placeholder = "I want to build an app for managing tenders for a pharma co"
        self.assertEqual(
            derive_title(SPEC, placeholder), "Appointment Scheduling"
        )

    def test_a_spec_without_a_heading_keeps_what_we_had(self):
        # derive_title falling through is what makes the overwrite safe.
        placeholder = "Build a task tracker"
        self.assertEqual(derive_title("- just a list\n", placeholder), placeholder)
        self.assertEqual(derive_title("", placeholder), placeholder)

    def test_the_overwrite_is_unconditional_in_the_recorder(self):
        # Guarding on `if not req.title` was the bug: the title is always set
        # at creation, so the guard never let the spec's name through.
        import inspect

        from zango.apps.agent_mode import tasks

        source = inspect.getsource(tasks._record_analyst_reply)
        self.assertIn("req.title = derive_title(spec,", source)
        self.assertNotIn("if not req.title:", source)
