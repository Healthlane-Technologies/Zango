"""Addressing and editing a spec document by path.

Two path forms:

* **concrete** RFC 6901 JSON Pointers — ``/masters/2/fields/0/state`` — are
  what the platform reports (issues, changed paths) and what the console maps
  onto fields;
* **selector** paths additionally accept ``@key`` in a list position, which
  picks the item whose ``code``/``id``/``name`` equals ``key``, or the
  single-key map ``{key: ...}``, or the bare string ``key``. PSP writes many
  lists as single-key maps (``- city: {...}``), and an agent editing by index
  would target the wrong item the moment something is inserted above it.

Every edit returns a new document (the input is never mutated) and the
concrete pointers it changed.
"""

from __future__ import annotations

import copy


class PathError(ValueError):
    """A path that does not resolve (or cannot be created)."""


ID_KEYS = ("code", "id", "name", "key")


def escape(token) -> str:
    return str(token).replace("~", "~0").replace("/", "~1")


def unescape(token: str) -> str:
    return token.replace("~1", "/").replace("~0", "~")


def to_pointer(parts) -> str:
    return "".join("/" + escape(p) for p in parts)


def parse(path: str) -> list:
    """Tokens of a pointer or selector path ("" or "/" is the root)."""
    path = (path or "").strip()
    if path in ("", "/"):
        return []
    if not path.startswith("/"):
        path = "/" + path
    return [unescape(t) for t in path.split("/")[1:]]


def _find_in_list(items: list, key: str) -> int:
    for i, item in enumerate(items):
        if isinstance(item, str) and item == key:
            return i
        if isinstance(item, dict):
            if len(item) == 1 and key in item:
                return i
            if any(str(item.get(k)) == key for k in ID_KEYS if k in item):
                return i
    return -1


def _step(node, token, *, create=False):
    """(child, concrete_token) for one token, or PathError."""
    if isinstance(node, list):
        if token.startswith("@"):
            idx = _find_in_list(node, token[1:])
            if idx < 0:
                raise PathError(f"no item {token[1:]!r} in the list")
            return node[idx], idx
        if token == "-":
            raise PathError("'-' can only be the last segment of an add")
        if not token.isdigit() or int(token) >= len(node):
            raise PathError(f"no item {token} in the list (it has {len(node)})")
        return node[int(token)], int(token)
    if isinstance(node, dict):
        if token.startswith("@") and token[1:] in node and token not in node:
            token = token[1:]
        if token not in node:
            if create:
                return None, token
            raise PathError(f"no key {token!r}")
        return node[token], token
    raise PathError(f"cannot step into a {type(node).__name__} with {token!r}")


def resolve(doc, path: str) -> list:
    """The concrete tokens a (selector) path names; the target must exist."""
    node, out = doc, []
    for token in parse(path):
        node, concrete = _step(node, token)
        out.append(concrete)
    return out


def get(doc, path: str):
    node = doc
    for token in parse(path):
        node, _ = _step(node, token)
    return node


def _parent(doc, tokens: list, *, create_parents=False):
    """(parent node, concrete parent tokens, last token) for ``tokens``."""
    if not tokens:
        raise PathError("the document root cannot be the target of this change")
    node, out = doc, []
    for token in tokens[:-1]:
        child, concrete = _step(node, token, create=create_parents)
        if child is None and create_parents and isinstance(node, dict):
            node[concrete] = child = {}
        node = child
        out.append(concrete)
    return node, out, tokens[-1]


def set_at(doc, path: str, value):
    """Replace (or create, in a map) the value at ``path``."""
    doc = copy.deepcopy(doc) if doc is not None else {}
    tokens = parse(path)
    if not tokens:
        return copy.deepcopy(value), [""]
    parent, where, last = _parent(doc, tokens, create_parents=True)
    if isinstance(parent, list):
        _, idx = _step(parent, last)
        parent[idx] = value
        where.append(idx)
    elif isinstance(parent, dict):
        if last.startswith("@") and last[1:] in parent:
            last = last[1:]
        parent[last] = value
        where.append(last)
    else:
        raise PathError(f"{to_pointer(where)} is not a map or a list")
    return doc, [to_pointer(where)]


def add_at(doc, path: str, value, index=None):
    """Insert into a list (at ``index``, or the end), or add a new map key."""
    doc = copy.deepcopy(doc) if doc is not None else {}
    tokens = parse(path)
    try:
        target = get(doc, path) if tokens else doc
    except PathError:
        target = None  # a new map key, or "-" at the end of a list
    if isinstance(target, list):
        pos = len(target) if index is None else max(0, min(int(index), len(target)))
        target.insert(pos, value)
        return doc, [to_pointer([*resolve(doc, path), pos])]
    parent, where, last = _parent(doc, tokens, create_parents=True)
    if isinstance(parent, list) and last == "-":
        parent.append(value)
        return doc, [to_pointer([*where, len(parent) - 1])]
    if isinstance(parent, dict):
        if last in parent:
            raise PathError(f"{to_pointer([*where, last])} already exists; use set")
        parent[last] = value
        return doc, [to_pointer([*where, last])]
    raise PathError(f"cannot add at {path}")


def remove_at(doc, path: str):
    doc = copy.deepcopy(doc)
    parent, where, last = _parent(doc, parse(path))
    _, concrete = _step(parent, last)
    if isinstance(parent, list):
        parent.pop(concrete)
    else:
        del parent[concrete]
    return doc, [to_pointer([*where, concrete])]


def move_at(doc, from_path: str, to_path: str, index=None):
    """Move a value; ``to_path`` names a list (insert at ``index``) or a new key."""
    value = copy.deepcopy(get(doc, from_path))
    doc, removed = remove_at(doc, from_path)
    doc, added = add_at(doc, to_path, value, index)
    return doc, removed + added


def diff(old, new, base=(), limit: int = 200) -> list:
    """Concrete pointers of the deepest nodes that differ between two documents."""
    out: list = []

    def walk(a, b, where):
        if len(out) >= limit or a == b:
            return
        if isinstance(a, dict) and isinstance(b, dict):
            for k in list(a.keys()) + [k for k in b if k not in a]:
                if k not in a or k not in b:
                    out.append(to_pointer([*where, k]))
                else:
                    walk(a[k], b[k], (*where, k))
            return
        if isinstance(a, list) and isinstance(b, list) and len(a) == len(b):
            for i, (x, y) in enumerate(zip(a, b)):
                walk(x, y, (*where, i))
            return
        out.append(to_pointer(where))

    walk(old, new, tuple(base))
    return out


def section_for(pointer: str, sections) -> str:
    """The id of the builder section a concrete pointer falls in, or ""."""
    import re

    best, best_len = "", -1
    for section in sections or ():
        base = section.get("pointer") or ""
        item = section.get("item")
        if item and base:
            # e.g. orders: pointer /programs, item orders → /programs/<n>/orders
            pattern = re.escape(base) + r"/[^/]+/" + re.escape(escape(item))
            m = re.match(pattern + r"(?:/|$)", pointer)
            if m and len(m.group(0)) > best_len:
                best, best_len = section.get("id", ""), len(m.group(0))
            continue
        for prefix in [base, *list(section.get("fields") or ())]:
            if not prefix:
                continue
            if (pointer == prefix or pointer.startswith(prefix + "/")) and len(
                prefix
            ) > best_len:
                best, best_len = section.get("id", ""), len(prefix)
    return best
