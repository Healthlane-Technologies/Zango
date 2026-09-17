"""The vendored skill plugin must be present and consistently named.

A mismatch between plugin.json's name, SKILL.md's name, and the qualified
identifier used for dispatch is a **silent** failure: the run proceeds and
the skill simply never loads. These assertions are cheap insurance.
"""

import json
import re
import unittest

from pathlib import Path

from zango.apps.agent_mode.options import SKILL_PLUGIN_DIR
from zango.apps.agent_mode.prompt import PLUGIN_NAME, QUALIFIED_SKILL, SKILL_NAME


PLUGIN = Path(SKILL_PLUGIN_DIR)
SKILL_DIR = PLUGIN / "skills" / SKILL_NAME


def _frontmatter(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    m = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    if not m:
        return {}
    out = {}
    for line in m.group(1).splitlines():
        if ":" in line and not line.startswith(" "):
            k, v = line.split(":", 1)
            out[k.strip()] = v.strip()
    return out


class SkillPluginTests(unittest.TestCase):
    def test_plugin_directory_exists(self):
        # options.py passes this path to ClaudeAgentOptions.plugins.
        self.assertTrue(PLUGIN.is_dir(), f"missing plugin dir: {PLUGIN}")

    def test_manifest_is_valid_and_named(self):
        manifest = PLUGIN / ".claude-plugin" / "plugin.json"
        self.assertTrue(manifest.is_file(), f"missing manifest: {manifest}")
        data = json.loads(manifest.read_text(encoding="utf-8"))
        self.assertEqual(data["name"], PLUGIN_NAME)
        self.assertTrue(data.get("description"))

    def test_skill_md_exists_with_matching_name(self):
        skill_md = SKILL_DIR / "SKILL.md"
        self.assertTrue(skill_md.is_file(), f"missing SKILL.md: {skill_md}")
        fm = _frontmatter(skill_md)
        self.assertEqual(fm.get("name"), SKILL_NAME)
        self.assertTrue(fm.get("description"))

    def test_qualified_name_is_plugin_colon_skill(self):
        # How plugin-provided skills are addressed, and what the prompt
        # dispatches with.
        self.assertEqual(QUALIFIED_SKILL, f"{PLUGIN_NAME}:{SKILL_NAME}")

    def test_references_are_present(self):
        refs = list((SKILL_DIR / "references").rglob("*.md"))
        self.assertGreater(len(refs), 20, "reference docs missing from the fork")

    def test_bootstrap_template_removed(self):
        # Capability 1 (Docker bootstrap) has no meaning in server mode.
        self.assertFalse((SKILL_DIR / "references" / "bootstrap-templates.md").exists())

    def test_no_nonexistent_cli_command_survives(self):
        # `zango manage-app ... sync_policies` does not exist in the CLI.
        for path in SKILL_DIR.rglob("*.md"):
            # VENDORED.md documents the fix, so it names the command on purpose.
            if path.name == "VENDORED.md":
                continue
            text = path.read_text(encoding="utf-8")
            self.assertNotIn(
                "zango manage-app", text, f"stale CLI command in {path.name}"
            )

    def test_skill_md_states_the_server_mode_constraints(self):
        text = (SKILL_DIR / "SKILL.md").read_text(encoding="utf-8").lower()
        for phrase in ("no human", "cannot restart", "backstop"):
            self.assertIn(phrase, text, f"missing guidance: {phrase}")

    def test_skill_md_has_no_stale_do_not_run_migrations_rule(self):
        # The agent now runs its own migrations; earlier revisions said both.
        text = (SKILL_DIR / "SKILL.md").read_text(encoding="utf-8").lower()
        for contradiction in (
            "migrations and sync are run **by the platform**",
            "do **not** run migrations, sync or restarts",
            "you do **not** run migrations",
        ):
            self.assertNotIn(contradiction, text, f"contradiction: {contradiction}")

    def test_skill_md_covers_reachability(self):
        text = (SKILL_DIR / "SKILL.md").read_text(encoding="utf-8")
        for phrase in ("backend/app/", "get_configs", "data-base-path"):
            self.assertIn(phrase, text, f"missing reachability guidance: {phrase}")


if __name__ == "__main__":
    unittest.main()


class PackageMandateTests(unittest.TestCase):
    """The first live run hand-rolled Django views because the packages were
    never installed and the skill told the agent not to install them."""

    def setUp(self):
        self.skill_md = (SKILL_DIR / "SKILL.md").read_text(encoding="utf-8")

    def test_skill_states_packages_are_preinstalled(self):
        self.assertIn("already installed", self.skill_md.lower())

    def test_skill_names_the_required_packages(self):
        for pkg in ("appbuilder", "crud", "workflow"):
            self.assertIn(pkg, self.skill_md)

    def test_skill_mandates_basecrudview_over_handrolled_views(self):
        self.assertIn("BaseCrudView", self.skill_md)
        self.assertIn("Never", self.skill_md)

    def test_skill_no_longer_tells_the_agent_not_to_install(self):
        self.assertNotIn("do not try to install it", self.skill_md.lower())

    def test_prompt_carries_the_package_mandate(self):
        from zango.apps.agent_mode.prompt import compose_prompt

        class Ctx:
            app_name = "DemoApp"
            workspace_path = "/tmp/ws"
            schema_name = "demo"
            primary_domain = "demo.local"
            packages = [{"name": "crud", "version": "1.0.17"}]
            modules = []
            roles = ["Admin"]

        text = compose_prompt("Add a vendor module", Ctx())
        self.assertIn("ALREADY INSTALLED", text)
        self.assertIn("BaseCrudView", text)
        self.assertIn("crud 1.0.17", text)
        # Constraints must stay uniquely numbered after the insertion.
        numbers = [
            line.split(".")[0].strip()
            for line in text.splitlines()
            if line[:2].strip().isdigit() and ". " in line[:4]
        ]
        self.assertEqual(
            len(numbers), len(set(numbers)), f"duplicate numbering: {numbers}"
        )


class ApiSerializationTests(unittest.TestCase):
    """`get_api_response` does a bare `json.dumps()`, so any hand-built payload
    must contain only JSON-native types.

    Regression: the availability endpoint returned raw `datetime` objects for
    `started_at` / `ended_at`, so opening Agent Mode failed with "Object of
    type datetime is not JSON serializable" — but only once the app had a run,
    which is why it surfaced late.
    """

    def test_iso_helper(self):
        import datetime as dt

        from zango.api.platform.agent_mode.v1.views import _iso

        self.assertIsNone(_iso(None))
        self.assertEqual(_iso(dt.datetime(2026, 9, 12, 8, 30)), "2026-09-12T08:30:00")

    def test_availability_shaped_payload_is_json_serializable(self):
        import datetime as dt
        import json
        from decimal import Decimal

        from zango.api.platform.agent_mode.v1.views import _iso

        payload = {
            "available": True,
            "reasons": [],
            "checks": {"worker_online": True, "worker_nodes": ["agent@host"]},
            "config": {"max_budget_usd": 25.0},
            "in_flight_run": {
                "uuid": "abc",
                "status": "running",
                "started_at": _iso(dt.datetime(2026, 9, 12, 8, 0)),
            },
            "last_run": {
                "uuid": "def",
                "status": "success",
                "ended_at": _iso(dt.datetime(2026, 9, 12, 8, 20)),
                "requires_restart": True,
            },
            # Decimals must be stringified by the caller too.
            "cost": str(Decimal("8.377981")),
        }
        json.dumps({"success": True, "response": payload})

    def test_raw_datetime_would_still_fail(self):
        # Guards the assumption above: json.dumps really has no default here.
        import datetime as dt
        import json

        with self.assertRaises(TypeError):
            json.dumps({"started_at": dt.datetime(2026, 9, 12)})


class MenuConfigGuidanceTests(unittest.TestCase):
    """The first successful build registered routes but no menus: the agent
    passed a role NAME to create_config, which needs a numeric primary key,
    and the vendored reference contradicted itself about which."""

    def setUp(self):
        self.skill = (SKILL_DIR / "SKILL.md").read_text(encoding="utf-8")
        self.ref = (
            SKILL_DIR / "references/packages/appbuilder/api-configuration.md"
        ).read_text(encoding="utf-8")

    def test_skill_states_role_id_is_numeric(self):
        self.assertIn("NUMERIC ID", self.skill)
        self.assertIn("get_available_roles", self.skill)

    def test_skill_shows_the_actual_error(self):
        self.assertIn("expected a number but got", self.skill)

    def test_skill_says_roles_already_exist(self):
        self.assertIn("already exist", self.skill)

    def test_reference_no_longer_claims_user_role_is_a_name_in_requests(self):
        self.assertNotIn("- `user_role` is a string (role name)", self.ref)
        self.assertIn("must be the role's numeric ID", self.ref)

    def test_reference_response_examples_are_annotated(self):
        self.assertIn("RESPONSE: name", self.ref)


class FrontendSetupGuidanceTests(unittest.TestCase):
    """Node is now guaranteed server-side, so the frontend is mandatory rather
    than conditional. A run that produces no frontend/ is a failed run.

    These assertions were inverted in v1.2.0. They previously required the step
    to be conditional and to carry "Do not scaffold a frontend just because you
    can" -- guidance written when the plan assumed no Node, and the reason a
    real run (wapp2) shipped no frontend at all."""

    def setUp(self):
        self.skill = (SKILL_DIR / "SKILL.md").read_text(encoding="utf-8")

    def test_scaffold_command_is_documented(self):
        self.assertIn("npx @zango-core/create-zango-app frontend", self.skill)

    def test_build_and_proxy_config_documented(self):
        self.assertIn("npm run build:zango", self.skill)
        self.assertIn("VITE_PROXY_ROUTES", self.skill)
        self.assertIn("Never include `/app`", self.skill)

    def test_step_is_mandatory_not_conditional(self):
        self.assertIn("Every sub-step 5a–5h is mandatory", self.skill)
        self.assertNotIn("5a, 5b and 5c are mandatory", self.skill)

    def test_scaffolding_is_not_discouraged(self):
        self.assertNotIn(
            "Do not scaffold a frontend just because you can", self.skill
        )

    def test_scaffold_runs_before_the_app_module(self):
        """The ordering is the fix: app.html is written once, after a bundle
        exists. Reversed, the agent writes it against appbuilder's prebuilt
        shell and never comes back."""
        self.assertLess(
            self.skill.index("### 5a. Scaffold the frontend"),
            self.skill.index("### 5g. Create the `app` module"),
        )

    def test_appbuilder_shell_is_not_offered_as_an_out(self):
        """Both tells of the wapp2 failure must be named as errors."""
        self.assertIn("app_initializer_endpoint", self.skill)
        self.assertIn("packages/appbuilder/js/", self.skill)
        self.assertNotIn("is a working reference", self.skill)

    def test_build_deploy_copy_is_documented(self):
        self.assertIn("cp -r frontend/zango-build/. static/js/", self.skill)

    def test_app_module_root_redirect_pattern_is_pinned(self):
        """An agent improvised r"^$" for the root redirect on one run and broke
        it. The skill must show the working pattern and name the wrong one."""
        self.assertIn('re_path(r"^/", RedirectAppView.as_view())', self.skill)
        self.assertIn('Writing `r"^$"` instead does', self.skill)

    def test_app_module_mounts_at_site_root(self):
        """The app module is mounted at "^" so its own urls.py owns the whole
        path -- that is what makes r"^/" and r"^login/?$" reachable. SKILL.md
        said "^app/", which would leave both redirects dead."""
        self.assertIn(
            '{"app_routes": [{"re_path": "^", "module": "app", "url": "urls"}]}',
            self.skill,
        )
        self.assertNotIn('"re_path": "^app/", "module": "app"', self.skill)

    def test_routes_and_menus_have_no_file_substitute(self):
        """wapp4 wrote routes_payload.json + menu_payloads.md, never attempted a
        POST, and reported the build complete -- leaving 0 routes and 0 menus in
        the schema. The skill must close that substitution and require read-back."""
        # Match on collapsed whitespace: the wording is pinned, the line
        # wrapping is not -- rewrapping a paragraph must not fail this test.
        flat = " ".join(self.skill.split())
        self.assertIn("is not a saved config", flat)
        self.assertIn("attempt the call before concluding anything is blocked", flat)
        # A failed registration must block the run, not be filed as a TODO.
        self.assertIn("A failure here is not an outstanding item", flat)

    def test_prompt_does_not_imply_post_is_blocked(self):
        """Constraint 6 said Bash is read-only in absolute terms, directly above
        constraint 8 asking for a POST; the agent resolved that by never trying."""
        from zango.apps.agent_mode.prompt import _CONSTRAINTS
        self.assertIn("read-only **for the filesystem**", _CONSTRAINTS)
        self.assertIn("POST with a request body\n   is allowed", _CONSTRAINTS)

    def test_base_form_clean_returns_none_is_documented(self):
        """BaseForm.clean() has no return, so `cleaned_data = super().clean()`
        yields None. Observed live in two generated apps: wapp3 payments reads
        from it (AttributeError on save) and wapp4 appointments returns it
        (validated data discarded). Django's own docs teach the opposite idiom,
        so this must be stated explicitly."""
        forms_md = (
            SKILL_DIR / "references" / "packages" / "crud" / "forms.md"
        ).read_text()
        self.assertIn("`BaseForm.clean()` returns `None`", forms_md)
        self.assertIn("Never write `cleaned_data = super().clean()`", forms_md)
        self.assertIn("read **`self.cleaned_data`**", forms_md)

    def test_menu_icons_are_required(self):
        """Observed in wapp3: every sidebar item rendered as the same grey page
        because the agent sent no icon and clean_icon() substituted U+1F4C4.
        The skill must name the fallback so a skip is recognisable."""
        self.assertIn("clean_icon()", self.skill)
        self.assertIn("Give every menu item its own icon", self.skill)
        # and it must not teach the fallback glyph as an example
        self.assertNotIn('"icon": "\U0001F4C4", "children"', self.skill)

    def test_shared_primitives_precede_the_pages(self):
        """shared.tsx is the polish mechanism: pages that each hand-roll their
        own tab strip and skeleton diverge immediately. It must be its own
        ordered sub-step, before the pages that compose from it."""
        self.assertIn("### 5c. Write the shared primitives", self.skill)
        self.assertLess(
            self.skill.index("### 5c. Write the shared primitives"),
            self.skill.index("### 5d. Write the custom pages"),
        )

    def test_polish_gate_is_checkable(self):
        """The wapp3 failure was literal hexes and inline styles everywhere,
        with no loading or empty state. Each gate item must be greppable."""
        self.assertIn("No literal hex colour in `src/custom/pages/`", self.skill)
        # auth/ is the one exception: it renders pre-auth with no tokens in
        # scope and takes its palette from the run context's theme: line.
        self.assertIn("`src/custom/auth/` is the one exception", self.skill)
        self.assertIn("style={{...}}", self.skill)
        self.assertIn("including each child tab", self.skill)
