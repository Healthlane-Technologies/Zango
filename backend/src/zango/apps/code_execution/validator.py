"""AST deny-list validator for Code Execution snippets (isolation Layer 1).

Walks a parsed AST and returns a list of `Violation` records. Used both at
snippet save time (so the editor can show problems inline) and at job pickup
(catches changes to the deny list mid-flight).

This is one of four isolation layers — see docs/code-execution-spec.html.
Anything that slips past here is still caught at the Postgres role (L2),
locked search_path (L3), or ConnectionGuard (L4).
"""

from __future__ import annotations

import ast
import re
from dataclasses import dataclass
from typing import List, Optional, Set, Tuple


# ---------------------------------------------------------------------------
# Deny lists
# ---------------------------------------------------------------------------

# Banned module imports — both `import X` and `from X import …`.
# Submodule prefixes are matched (e.g. "subprocess" blocks "subprocess.run").
BANNED_IMPORT_PREFIXES: Set[str] = {
    "subprocess",
    "socket",
    "ctypes",
    "importlib",
    "pickle",
    "marshal",
    "multiprocessing",
    "pty",
    "resource",
    "_thread",
    "django_tenants.utils",
}

# Names that, when imported via `from X import Y`, are blocked outright.
BANNED_FROM_IMPORT_NAMES: Set[str] = {
    "schema_context",
    "tenant_context",
    "get_tenant_model",
    "connections",  # from django.db import connections
    "system",  # from os import system
    "popen",  # from os import popen
    "execv",
    "execvp",
    "execvpe",
    "execlp",
    "execle",
    "fork",
    "spawn",
    "kill",
    "rmtree",  # from shutil import rmtree
    "TenantModel",
    "SECRET_KEY",
    "DATABASES",
}

# Names that cannot be referenced (loaded) — even if never explicitly imported.
BANNED_NAMES: Set[str] = {
    "eval",
    "exec",
    "compile",
    "__import__",
    "globals",
    "locals",
    "vars",
    "setattr",
    "delattr",
    "breakpoint",
    "input",
}

# Dunder attributes — reflection escape hatches.
BANNED_DUNDERS: Set[str] = {
    "__class__",
    "__bases__",
    "__subclasses__",
    "__globals__",
    "__builtins__",
    "__import__",
    "__code__",
    "__dict__",
    "__mro__",
    "__getattribute__",
    "__reduce__",
    "__reduce_ex__",
}

# Attribute chains that resolve to dangerous APIs. Matched as a prefix —
# (("connection", "set_tenant")) blocks `connection.set_tenant(...)` and any
# attribute access beneath it. Root token is resolved through import aliases.
BANNED_ATTR_PATHS: Set[Tuple[str, ...]] = {
    # Tenant switching
    ("connection", "set_tenant"),
    ("connection", "set_schema"),
    ("connection", "set_schema_to_public"),
    ("connection", "schema_name"),
    ("connection", "tenant"),
    ("django", "db", "connections"),
    ("django_tenants", "utils"),
    # os shell hatches
    ("os", "system"),
    ("os", "popen"),
    ("os", "execv"),
    ("os", "execvp"),
    ("os", "execvpe"),
    ("os", "fork"),
    ("os", "kill"),
    ("os", "spawn"),
    # Settings
    ("settings", "SECRET_KEY"),
    ("settings", "DATABASES"),
    # Shutil
    ("shutil", "rmtree"),
}

# Function calls (by attribute tail) that are banned as a hard rule.
BANNED_CALLS: Set[str] = {
    "schema_context",
    "tenant_context",
    "set_tenant",
    "set_schema",
    "set_schema_to_public",
}

# Dangerous SQL fragments in string constants. Matched case-insensitively.
SQL_DANGER_PATTERNS = [
    re.compile(r"\bSET\s+search_path\b", re.IGNORECASE),
    re.compile(r"\bSET\s+SCHEMA\b", re.IGNORECASE),
    re.compile(r"\bSET\s+ROLE\b", re.IGNORECASE),
    re.compile(r"\bSET\s+SESSION\s+AUTHORIZATION\b", re.IGNORECASE),
]


# ---------------------------------------------------------------------------
# Result types
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Violation:
    line: int
    col: int
    code: str
    message: str

    def to_dict(self) -> dict:
        return {
            "line": self.line,
            "col": self.col,
            "code": self.code,
            "message": self.message,
        }


class CodeValidationError(Exception):
    """Raised when a snippet has one or more deny-list violations."""

    def __init__(self, violations: List[Violation]):
        self.violations = violations
        super().__init__(f"{len(violations)} validation violation(s)")


# ---------------------------------------------------------------------------
# Visitor
# ---------------------------------------------------------------------------


class _DenyVisitor(ast.NodeVisitor):
    def __init__(self) -> None:
        self.violations: List[Violation] = []
        # Map a local name (possibly aliased) → the real module it refers to.
        # e.g. `import os as o` → {"o": "os"}; `from os import system` →
        # the call check picks up "system" via BANNED_FROM_IMPORT_NAMES.
        self.alias_to_module: dict = {}

    # -- imports -----------------------------------------------------------

    def visit_Import(self, node: ast.Import) -> None:
        for alias in node.names:
            mod = alias.name
            local = alias.asname or alias.name.split(".")[0]
            if self._matches_banned_module(mod):
                self._add(
                    node.lineno,
                    node.col_offset,
                    "DENY_IMPORT",
                    f"Import of '{mod}' is not allowed.",
                )
            # Track alias → root module for attribute-chain resolution.
            root = mod.split(".")[0]
            self.alias_to_module[local] = root
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        mod = node.module or ""
        if mod and self._matches_banned_module(mod):
            self._add(
                node.lineno,
                node.col_offset,
                "DENY_IMPORT",
                f"Import from '{mod}' is not allowed.",
            )
            self.generic_visit(node)
            return
        for alias in node.names:
            if alias.name in BANNED_FROM_IMPORT_NAMES:
                self._add(
                    node.lineno,
                    node.col_offset,
                    "DENY_IMPORT_NAME",
                    f"Importing '{alias.name}' from '{mod}' is not allowed.",
                )
            local = alias.asname or alias.name
            # If the imported name itself is a top-level banned module, track it.
            if alias.name in {"os", "shutil", "django", "settings", "connection"}:
                self.alias_to_module[local] = alias.name
        self.generic_visit(node)

    # -- names -------------------------------------------------------------

    def visit_Name(self, node: ast.Name) -> None:
        if isinstance(node.ctx, ast.Load) and node.id in BANNED_NAMES:
            self._add(
                node.lineno,
                node.col_offset,
                "DENY_NAME",
                f"Use of builtin '{node.id}' is not allowed.",
            )
        self.generic_visit(node)

    # -- attribute access --------------------------------------------------

    def visit_Attribute(self, node: ast.Attribute) -> None:
        # Banned dunder attribute access (any object).
        if node.attr in BANNED_DUNDERS:
            self._add(
                node.lineno,
                node.col_offset,
                "DENY_DUNDER",
                f"Access to reflective attribute '{node.attr}' is not allowed.",
            )

        # Resolve attribute chain. If the root maps to an alias, replace it
        # with the real module name before matching against banned paths.
        chain = self._attr_chain(node)
        if chain:
            root = chain[0]
            chain = (self.alias_to_module.get(root, root),) + chain[1:]
            for banned in BANNED_ATTR_PATHS:
                if len(chain) >= len(banned) and chain[: len(banned)] == banned:
                    self._add(
                        node.lineno,
                        node.col_offset,
                        "DENY_ATTR",
                        f"Access to '{'.'.join(banned)}' is not allowed.",
                    )
                    break
        self.generic_visit(node)

    # -- assignment guards (tenant switching) -----------------------------

    def visit_Assign(self, node: ast.Assign) -> None:
        for target in node.targets:
            if isinstance(target, ast.Attribute):
                chain = self._attr_chain(target)
                if chain:
                    root = chain[0]
                    chain = (self.alias_to_module.get(root, root),) + chain[1:]
                    if chain in {
                        ("connection", "schema_name"),
                        ("connection", "tenant"),
                        ("django", "db", "connection", "schema_name"),
                        ("django", "db", "connection", "tenant"),
                    }:
                        self._add(
                            node.lineno,
                            node.col_offset,
                            "DENY_TENANT_SWITCH",
                            f"Assigning to '{'.'.join(chain)}' is not allowed.",
                        )
                    elif chain[0] == "settings" or chain[:3] == (
                        "django",
                        "conf",
                        "settings",
                    ):
                        self._add(
                            node.lineno,
                            node.col_offset,
                            "DENY_SETTINGS_WRITE",
                            f"Modifying '{'.'.join(chain)}' is not allowed; "
                            f"settings are read-only.",
                        )
        self.generic_visit(node)

    def visit_AugAssign(self, node: ast.AugAssign) -> None:
        if isinstance(node.target, ast.Attribute):
            chain = self._attr_chain(node.target)
            if chain:
                root = chain[0]
                resolved = (self.alias_to_module.get(root, root),) + chain[1:]
                if resolved in {
                    ("connection", "schema_name"),
                    ("connection", "tenant"),
                }:
                    self._add(
                        node.lineno,
                        node.col_offset,
                        "DENY_TENANT_SWITCH",
                        f"Mutating '{'.'.join(resolved)}' is not allowed.",
                    )
                elif resolved[0] == "settings" or resolved[:3] == (
                    "django",
                    "conf",
                    "settings",
                ):
                    self._add(
                        node.lineno,
                        node.col_offset,
                        "DENY_SETTINGS_WRITE",
                        f"Modifying '{'.'.join(resolved)}' is not allowed; "
                        f"settings are read-only.",
                    )
        self.generic_visit(node)

    # -- function calls ---------------------------------------------------

    def visit_Call(self, node: ast.Call) -> None:
        # Direct call of a banned name: e.g. `schema_context(...)`.
        if isinstance(node.func, ast.Name) and node.func.id in BANNED_CALLS:
            self._add(
                node.lineno,
                node.col_offset,
                "DENY_CALL",
                f"Call to '{node.func.id}' is not allowed.",
            )
        # Method call where the tail attribute is banned, regardless of root.
        if isinstance(node.func, ast.Attribute) and node.func.attr in BANNED_CALLS:
            self._add(
                node.lineno,
                node.col_offset,
                "DENY_CALL",
                f"Call to '.{node.func.attr}(...)' is not allowed.",
            )
        # getattr / setattr / delattr reflection on `connection`.
        if isinstance(node.func, ast.Name) and node.func.id in {
            "getattr",
            "setattr",
            "delattr",
        }:
            if (
                len(node.args) >= 1
                and isinstance(node.args[0], ast.Name)
                and self.alias_to_module.get(node.args[0].id, node.args[0].id)
                == "connection"
            ):
                self._add(
                    node.lineno,
                    node.col_offset,
                    "DENY_REFLECTION",
                    f"Reflective {node.func.id} on 'connection' is not allowed.",
                )
        self.generic_visit(node)

    # -- string constants -------------------------------------------------

    def visit_Constant(self, node: ast.Constant) -> None:
        if isinstance(node.value, str):
            for pat in SQL_DANGER_PATTERNS:
                if pat.search(node.value):
                    self._add(
                        node.lineno,
                        node.col_offset,
                        "DENY_SQL",
                        "String literal contains a schema/role switching SQL "
                        "fragment (SET search_path, SET SCHEMA, SET ROLE, "
                        "SET SESSION AUTHORIZATION).",
                    )
                    break
        self.generic_visit(node)

    # -- helpers ----------------------------------------------------------

    @staticmethod
    def _matches_banned_module(mod: str) -> bool:
        for banned in BANNED_IMPORT_PREFIXES:
            if mod == banned or mod.startswith(banned + "."):
                return True
        return False

    @staticmethod
    def _attr_chain(node: ast.AST) -> Optional[Tuple[str, ...]]:
        chain: List[str] = []
        cur: ast.AST = node
        while isinstance(cur, ast.Attribute):
            chain.append(cur.attr)
            cur = cur.value
        if isinstance(cur, ast.Name):
            chain.append(cur.id)
            chain.reverse()
            return tuple(chain)
        return None

    def _add(self, line: int, col: int, code: str, message: str) -> None:
        self.violations.append(Violation(line=line, col=col, code=code, message=message))


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def validate(source: str) -> List[Violation]:
    """Return all deny-list violations in `source`. Empty list = clean."""
    if not source.strip():
        return []
    try:
        tree = ast.parse(source)
    except SyntaxError as exc:
        return [
            Violation(
                line=exc.lineno or 1,
                col=(exc.offset or 1) - 1,
                code="SYNTAX",
                message=f"Syntax error: {exc.msg}",
            )
        ]
    visitor = _DenyVisitor()
    visitor.visit(tree)
    # De-dup violations with the same (line, code, message).
    seen: Set[Tuple[int, str, str]] = set()
    unique: List[Violation] = []
    for v in visitor.violations:
        key = (v.line, v.code, v.message)
        if key in seen:
            continue
        seen.add(key)
        unique.append(v)
    unique.sort(key=lambda v: (v.line, v.col))
    return unique


def assert_valid(source: str) -> None:
    """Raise CodeValidationError if any violations are present."""
    violations = validate(source)
    if violations:
        raise CodeValidationError(violations)
