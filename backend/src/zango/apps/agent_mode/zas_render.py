"""zas-render.js: the one renderer the App Studio preview and the built app both draw with.

The source is the zango_app pack's ``builder/zas-render.js``. It has two copies, never edited by
hand: inline in the kit page (``builder/app-studio.html``, a ``<script data-zas-render>`` block, so
the page stays one self-contained file), and in the runtime's ``assets/frontend/zas/`` (the build
copies that folder into every app). The kit page's stylesheet goes there too, as ``kit.css``, and
its icon library as ``lucide.js``: the markup is the same, so the rules and the icons that draw it
are the same.

    python -m zango.apps.agent_mode.zas_render --check   # exit 1 when a copy differs
    python -m zango.apps.agent_mode.zas_render --write   # refresh both copies from the source
"""

import re
import sys

from pathlib import Path


_APPS = Path(__file__).resolve().parents[1]
BUILDER = _APPS / "shared" / "app_templates" / "packs" / "zango_app" / "builder"
SOURCE = BUILDER / "zas-render.js"
KIT_PAGE = BUILDER / "app-studio.html"
RUNTIME_COPY = (
    Path(__file__).resolve().parent
    / "skill_plugin"
    / "skills"
    / "zango-app-studio"
    / "assets"
    / "frontend"
    / "zas"
    / "zas-render.js"
)

KIT_CSS = RUNTIME_COPY.parent / "kit.css"
CSS_HEADER = (
    "/* The kit page's stylesheet (packs/zango_app/builder/app-studio.html), for the markup\n"
    "   zas-render.js draws. Generated: python -m zango.apps.agent_mode.zas_render --write */\n"
)

LUCIDE = RUNTIME_COPY.parent / "lucide.js"
_LUCIDE_RE = re.compile(r"<script>(/\* lucide [^\n]*\*/)\n(.*?)</script>", re.S)

OPEN = "<script data-zas-render>\n"
CLOSE = "</script>"


def source() -> str:
    js = SOURCE.read_text(encoding="utf-8")
    if "</script" in js.lower():
        raise ValueError(
            "zas-render.js must not contain '</script': it is inlined in the kit page"
        )
    return js


def inlined(html: str) -> str | None:
    """The renderer the kit page carries, or None when it has no zas-render block."""
    start = html.find(OPEN)
    if start < 0:
        return None
    start += len(OPEN)
    end = html.find(CLOSE, start)
    return html[start:end] if end >= 0 else None


def inline(html: str, js: str) -> str:
    """``html`` with its zas-render block replaced by ``js``."""
    start = html.find(OPEN)
    if start < 0:
        raise ValueError(f"the kit page has no {OPEN.strip()} block")
    start += len(OPEN)
    end = html.find(CLOSE, start)
    return html[:start] + js + html[end:]


def kit_css(html: str) -> str:
    """The runtime's kit.css: every <style> of the kit page, in order."""
    return CSS_HEADER + "\n".join(
        re.findall(r"<style[^>]*>(.*?)</style>", html, re.S | re.I)
    )


def kit_icons(html: str) -> str:
    """The runtime's lucide.js: the icon library the kit page inlines (the same version, so
    <i data-lucide> becomes the same SVG). A UMD build: imported for its side effect, it sets
    globalThis.lucide."""
    m = _LUCIDE_RE.search(html)
    if not m:
        raise ValueError("the kit page has no inlined lucide script")
    body = re.sub(r"\n//# sourceMappingURL=\S+\s*$", "\n", m.group(2))
    return (
        m.group(1)[:-2].rstrip()
        + "; copied from the kit page by zas_render.py */\n"
        + body
    )


def _expected() -> dict:
    js = source()
    page = KIT_PAGE.read_text(encoding="utf-8")
    return {
        KIT_PAGE: inline(page, js),
        RUNTIME_COPY: js,
        KIT_CSS: kit_css(page),
        LUCIDE: kit_icons(page),
    }


def stale() -> list[Path]:
    """The copies that differ from the source."""
    return [
        p
        for p, text in _expected().items()
        if not p.exists() or p.read_text(encoding="utf-8") != text
    ]


def write() -> list[Path]:
    """Refresh the stale copies from the source; the paths written."""
    expected = _expected()
    changed = stale()
    for path in changed:
        path.write_text(expected[path], encoding="utf-8")
    return changed


def main(argv: list[str]) -> int:
    if "--write" in argv:
        for path in write():
            print(f"wrote {path}")
        return 0
    bad = stale()
    for path in bad:
        print(f"stale: {path} (run python -m zango.apps.agent_mode.zas_render --write)")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
