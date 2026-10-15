"""Which skills a build session loads.

Every app on the generic spec is built with App Studio, from Agent Mode's own
plugin, and nothing else. The general developer skill is only loaded beside a
template build skill of its own (PSP's), which still relies on it.
"""

import sys
import types
import unittest

from pathlib import Path
from types import SimpleNamespace
from unittest import mock

from zango.apps.agent_mode import options
from zango.apps.agent_mode.prompt import DEVELOPER_SKILL, STUDIO_SKILL


def _fake_sdk():
    sdk = types.ModuleType("claude_agent_sdk")
    sdk.ClaudeAgentOptions = lambda **kwargs: kwargs
    sdk.HookMatcher = lambda **kwargs: kwargs
    return sdk


class BuildSkillsTests(unittest.TestCase):
    def options_for(self, template_build):
        run = SimpleNamespace(
            permission_mode="",
            model="",
            effort="",
            max_turns=None,
            max_budget_usd=None,
            resumed_from_id=None,
            resumed_from=None,
        )
        ctx = SimpleNamespace(workspace_path="/ws", primary_domain="demo.local", app_name="demo")
        cfg = SimpleNamespace(
            allow_frontend_build=False, model="", effort="", max_turns=None, max_budget_usd=None
        )
        with mock.patch.dict(sys.modules, {"claude_agent_sdk": _fake_sdk()}), mock.patch(
            "zango.apps.agent_mode.config.load_config", return_value=cfg
        ), mock.patch.object(options, "agent_home", return_value="/tmp/home"), mock.patch.object(
            options, "build_env", return_value={}
        ):
            return options.build_agent_options(
                run=run, ctx=ctx, creds=None, settings_path="/tmp/s.json", template_build=template_build
            )

    def test_a_studio_build_loads_only_app_studio(self):
        skill_dir = Path(options.SKILL_PLUGIN_DIR) / "skills" / "zango-app-studio"
        tb = SimpleNamespace(
            skill=STUDIO_SKILL,
            skill_plugin_dir=options.SKILL_PLUGIN_DIR,
            skill_dir=str(skill_dir),
            plugin_dir="/templates/ordering-portal/1.0.0",
            spec_dir="/runs/x/spec",
        )
        kwargs = self.options_for(tb)
        self.assertEqual(kwargs["skills"], [STUDIO_SKILL])
        self.assertNotIn(DEVELOPER_SKILL, kwargs["skills"])
        # Agent Mode's plugin once: App Studio is in it.
        self.assertEqual(kwargs["plugins"], [{"type": "local", "path": options.SKILL_PLUGIN_DIR}])

    def test_a_template_with_its_own_skill_gets_the_developer_skill_beside_it(self):
        tb = SimpleNamespace(
            skill="zango-tpl-psp:zango-psp-builder",
            skill_plugin_dir="/templates/psp/1.0.0",
            skill_dir="/templates/psp/1.0.0/skills/zango-psp-builder",
            plugin_dir="/templates/psp/1.0.0",
            spec_dir="/runs/x/spec",
        )
        kwargs = self.options_for(tb)
        self.assertEqual(kwargs["skills"], ["zango-tpl-psp:zango-psp-builder", DEVELOPER_SKILL])
        self.assertIn({"type": "local", "path": "/templates/psp/1.0.0"}, kwargs["plugins"])

    def test_no_build_skill_loads_nothing(self):
        # tasks.py refuses such a run before options are built; nothing here
        # falls back to the developer skill either.
        self.assertEqual(self.options_for(None)["skills"], [])


if __name__ == "__main__":
    unittest.main()
