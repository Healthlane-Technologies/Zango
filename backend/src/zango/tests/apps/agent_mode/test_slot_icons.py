"""Icons used only by hand-written slots.

Prepare generates icons.gen.ts from the spec, before any slot exists, and the agent cannot run
lucide_icons.py in server mode, so a slot's icon used to render as the Circle fallback. The
platform regenerates it before app_shell, and design lint names unknown lucide names.
"""

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

from pathlib import Path
from unittest import mock

from zango.apps.agent_mode import studio_build
from zango.apps.agent_mode.studio_build import StudioBuild
from zango.apps.shared.app_templates.services.generic import studio_plugin_dir


SCRIPTS = Path(studio_plugin_dir()) / "skills" / "zango-app-studio" / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import lucide_icons  # noqa: E402

from zas_test import design  # noqa: E402


GEN = '// Generated\nimport {{ Circle }} from "lucide-react";\n\nexport const ICONS = {{\n{}}} as const;\n'


def gen(**icons):
    return GEN.format("".join(f'  "{k}": {v},\n' for k, v in icons.items()))


class SlotIconTests(unittest.TestCase):
    def setUp(self):
        self.ws = Path(tempfile.mkdtemp(prefix="icons-"))
        (self.ws / "frontend" / "src" / "custom" / "slots").mkdir(parents=True)
        (self.ws / "frontend" / "src" / "zas").mkdir(parents=True)
        (self.ws / ".zas").mkdir()
        (self.ws / ".zas" / "spec.resolved.json").write_text(json.dumps({"roles": {}}))

    def tearDown(self):
        shutil.rmtree(self.ws, ignore_errors=True)

    def test_icons_in_item_objects_are_collected(self):
        # Regression: Kpis items carry `icon: "package"`, which only icon="…" props were matched for.
        (self.ws / "frontend" / "src" / "custom" / "slots" / "Overview.tsx").write_text(
            '<Kpis items={[{ label: "Ready", icon: "package" }, { icon: \'pen-line\' }]} />\n'
            '<Panel icon="workflow" /><Icon name="bell" />\n'
        )
        self.assertEqual(
            lucide_icons.collect_custom(str(self.ws)), {"package", "pen-line", "workflow", "bell"}
        )

    def test_lint_names_icons_drawn_as_the_circle_fallback(self):
        (self.ws / "frontend" / "src" / "zas" / "icons.gen.ts").write_text(
            gen(circle="Circle", clock="Clock", **{"pie-chrt": "Circle"})
        )
        Dx = design.D(str(self.ws))
        design.g_lint(Dx)
        lint = next(r for r in Dx.results if r["id"] == "design.lint")
        self.assertEqual(lint["status"], "fail")
        self.assertIn("pie-chrt", lint["detail"])
        self.assertNotIn("clock", lint["detail"])

    def test_platform_regenerates_icons_and_asks_for_a_rebuild(self):
        root = Path(tempfile.mkdtemp(prefix="studio-"))
        self.addCleanup(shutil.rmtree, root, True)
        ws = self.ws
        (ws / "settings.json").write_text(json.dumps({
            "app_name": "demo", "modules": [{"name": "app", "path": "backend.app"}],
            "app_routes": [{"module": "app", "re_path": "^", "url": "urls"}],
        }))
        app = ws / "backend" / "app"
        (app / "templates").mkdir(parents=True)
        for f in ("urls.py", "views.py", "policies.json"):
            (app / f).write_text("\n")
        (app / "templates" / "app.html").write_text("<script src=\"{% zstatic 'js/zango-app.1.min.js' %}\">")
        (ws / "static" / "js").mkdir(parents=True)
        build_file = ws / "static" / "js" / "zango-app.1.min.js"
        icons = ws / "frontend" / "src" / "zas" / "icons.gen.ts"
        icons.write_text(gen(circle="Circle"))
        build_file.write_text("// build\n")
        os.utime(icons, (1_000_000, 1_000_000))
        os.utime(build_file, (1_000_100, 1_000_100))  # deployed after the sources: not stale yet

        def regenerate(argv, **kw):
            icons.write_text(gen(circle="Circle", package="Package"))
            return subprocess.CompletedProcess(argv, 0, stdout="", stderr="")

        build = StudioBuild(skill_dir=str(root), workspace=str(ws), spec_path=str(root / "s.yaml"),
                            run_dir=str(root), base_dir=str(root), app_name="demo", frontend_ready=True)
        with mock.patch.object(studio_build.subprocess, "run", side_effect=regenerate):
            layer = build.check_app_shell()
        stale = next(f for f in layer.failures if f["id"] == "app_shell.stale")
        self.assertIn("package", stale["title"] + stale["detail"])


if __name__ == "__main__":
    unittest.main()
