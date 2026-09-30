"""Cross-reference rules a JSON Schema cannot express (rules.json).

Each rule is ``{"id", "kind", "level", "message", ...params}``. Paths are
slash-separated patterns into the spec document:

* ``*``      one level, any key or index — captured as ``$1``, ``$2``…
* ``**``     any depth
* ``{a,b}``  one of the named keys
* ``@key``   (last) the key of a single-key map item, or a bare string item
* ``$N``     in ``target`` / ``path``: the N-th capture from ``source`` / ``if``

Kinds: ``unique`` {path, key, group_by_parent?}, ``ref`` {source, target, key},
``exactly_one`` {path, where:{key, equals}}, ``required_when`` {path,
if:{path, equals}}, ``max_items`` {path, max}. ``key: ""`` means the item's
own identity: a bare string, or a single-key map's key. ``{value}`` in a
message is replaced with the offending value.
"""

from __future__ import annotations

from .document import to_pointer


def _children(node):
    if isinstance(node, dict):
        return list(node.items())
    if isinstance(node, list):
        return list(enumerate(node))
    return []


def _match(node, segs, caps=(), where=()):
    if not segs:
        yield node, caps, where
        return
    seg, rest = segs[0], segs[1:]
    if seg == "**":
        yield from _match(node, rest, caps, where)
        for k, child in _children(node):
            yield from _match(child, segs, caps, (*where, k))
        return
    if seg == "@key":
        if isinstance(node, str):
            yield node, caps, where
        elif isinstance(node, dict) and len(node) == 1:
            yield next(iter(node)), caps, where
        return
    if seg == "*":
        for k, child in _children(node):
            yield from _match(child, rest, (*caps, k), (*where, k))
        return
    if seg.startswith("{") and seg.endswith("}"):
        for opt in seg[1:-1].split(","):
            if isinstance(node, dict) and opt in node:
                yield from _match(node[opt], rest, caps, (*where, opt))
        return
    if isinstance(node, dict) and seg in node:
        yield from _match(node[seg], rest, caps, (*where, seg))
    elif isinstance(node, list) and seg.isdigit() and int(seg) < len(node):
        yield from _match(node[int(seg)], rest, caps, (*where, int(seg)))


def glob(doc, path: str, caps=()):
    """Every (node, captures, location) the pattern matches."""
    for i, cap in enumerate(caps, 1):
        path = path.replace(f"${i}", str(cap))
    return list(_match(doc, [p for p in path.split("/") if p]))


def _ident(item, key: str):
    if key:
        return item.get(key) if isinstance(item, dict) else None
    if isinstance(item, (str, int, float)) and not isinstance(item, bool):
        return str(item)
    if isinstance(item, dict) and len(item) == 1:
        return next(iter(item))
    return None


def _values(node):
    if isinstance(node, (str, int, float)) and not isinstance(node, bool):
        return [str(node)]
    if isinstance(node, list):
        return [
            str(x)
            for x in node
            if isinstance(x, (str, int, float)) and not isinstance(x, bool)
        ]
    return []


def evaluate(doc, rules) -> list:
    """Issues [{level, path, message, code, rule}] for ``doc`` against ``rules``."""
    issues = []

    def add(rule, where, value=""):
        issues.append(
            {
                "level": rule.get("level", "error"),
                "path": to_pointer(where),
                "message": str(rule.get("message", "")).replace("{value}", str(value)),
                "code": f"rule:{rule.get('kind')}",
                "rule": rule.get("id", ""),
            }
        )

    for rule in rules or ():
        if not isinstance(rule, dict):
            continue
        kind = rule.get("kind")
        key = rule.get("key", "")
        if kind == "unique":
            groups: dict = {}
            for item, _, where in glob(doc, rule["path"]):
                value = _ident(item, key)
                if value is None:
                    continue
                group = where[:-1] if rule.get("group_by_parent") else ()
                groups.setdefault(group, {}).setdefault(value, []).append(where)
            for group in groups.values():
                for value, wheres in group.items():
                    if len(wheres) > 1:
                        add(rule, wheres[1], value)
        elif kind == "ref":
            for node, caps, where in glob(doc, rule["source"]):
                known = set()
                for target, _, _ in glob(doc, rule["target"], caps):
                    if rule["target"].endswith("*"):
                        value = _ident(target, key)
                        if value is not None:
                            known.add(value)
                    elif isinstance(target, dict):
                        known.update(target.keys())
                    elif isinstance(target, list):
                        known.update(filter(None, (_ident(x, key) for x in target)))
                for value in _values(node):
                    if value not in known:
                        add(rule, where, value)
        elif kind == "exactly_one":
            cond = rule.get("where") or {}
            for node, _, where in glob(doc, rule["path"]):
                if not isinstance(node, list) or not node:
                    continue
                hits = 0
                for item in node:
                    if isinstance(item, dict) and len(item) == 1:
                        inner = next(iter(item.values()))
                        if isinstance(inner, dict) and inner.get(
                            cond.get("key")
                        ) == cond.get("equals"):
                            hits += 1
                if hits != 1:
                    add(rule, where, hits)
        elif kind == "required_when":
            cond = rule.get("if") or {}
            for node, caps, where in glob(doc, cond.get("path", "")):
                if node == cond.get("equals"):
                    hit = glob(doc, rule["path"], caps)
                    if not hit or hit[0][0] in (None, "", [], {}):
                        add(rule, where)
        elif kind == "max_items":
            for node, _, where in glob(doc, rule["path"]):
                if isinstance(node, list) and len(node) > rule.get("max", 0):
                    add(rule, where, len(node))
    return issues
