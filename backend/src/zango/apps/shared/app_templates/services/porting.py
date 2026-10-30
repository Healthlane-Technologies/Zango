"""Port templates from the Zelthy product catalogue into template packs.

The Zelthy console mockup (``Zelthy.html``) lists ~150 templates: name, category, description,
roles, workflows, data objects, packages, integrations and compliance points. Porting one turns
that entry into a pack under ``packs/<dir>/`` that Agent Mode can preview and build:

    extract   Zelthy.html → porting/zelthy_catalogue.json (run once per new mockup; committed)
    list      the catalogue, and which entries already have a pack
    scaffold  template.json from the entry + a starter.yaml skeleton to author
    check     spec_check the starter (the build's own linter) and screenshot it in the preview
    import    import the pack into the database (and publish it)

Only the starter needs a person (or an agent) to write it: the catalogue says *what* the
template is, not its fields, statuses and screens. Everything else is mechanical.

Run through ``manage.py app_templates port …``. ``extract`` and ``check --shots`` need
Playwright (already installed for Agent Mode's preview probe).
"""

from __future__ import annotations

import json
import re
import subprocess
import sys

from pathlib import Path


APP_TEMPLATES_DIR = Path(__file__).resolve().parent.parent
PACKS_DIR = APP_TEMPLATES_DIR / "packs"
CATALOGUE_PATH = APP_TEMPLATES_DIR / "porting" / "zelthy_catalogue.json"
GENERIC_BUILDER = PACKS_DIR / "zango_app" / "builder"
SPEC_CHECK = (
    APP_TEMPLATES_DIR.parent.parent
    / "agent_mode/skill_plugin/skills/zango-app-studio/scripts/spec_check.py"
)

# The console's template picker draws these (console/src/pages/workspace/templates/catalog.ts,
# ICONS); any other name falls back to the category's icon.
CONSOLE_ICONS = set(
    "heart dna cart truck shield file book pulse card apps gift barcode mic eye bot tpl users "
    "pkg blank agent badge key".split()
)

# Read out of the mockup's script. The catalogue lives inside an IIFE, so the extractor adds
# one line before it closes that hands the data to the page.
_EXPOSE = (
    "window.__ZCAT={TPL,TPLCOMP,VCOMP:(typeof VCOMP!=='undefined'?VCOMP:{}),"
    "TPL_AGENTS_X,PKDESC:(typeof PKDESC!=='undefined'?PKDESC:{}),"
    "AGENTS:AGENTS.map(a=>({id:a.id,name:a.name,mode:a.mode,hitl:a.hitl}))};\n"
)


class PortError(Exception):
    pass


# ------------------------------------------------------------------ catalogue --


def extract(html_path: str | Path, out: Path = CATALOGUE_PATH) -> dict:
    """Read the template catalogue out of the Zelthy console mockup into JSON."""
    from playwright.sync_api import sync_playwright

    html = Path(html_path).read_text(encoding="utf-8")
    end = html.rfind("</script>")
    close = html.rfind("})();", 0, end)
    if end < 0 or close < 0:
        raise PortError(
            "This doesn't look like the Zelthy console mockup (no main script)."
        )
    html = html[:close] + _EXPOSE + html[close:]

    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        page = browser.new_page()
        page.route(
            "**/*",
            lambda r: r.abort() if r.request.url.startswith("http") else r.continue_(),
        )
        page.set_content(html, wait_until="load")
        data = page.evaluate("() => window.__ZCAT || null")
        browser.close()
    if not data or not data.get("TPL"):
        raise PortError(
            "The mockup ran, but its template catalogue (TPL) was not found."
        )

    agents = {a["id"]: a for a in data["AGENTS"]}
    templates = []
    for t in data["TPL"]:
        compliance = (
            data["TPLCOMP"].get(t["id"]) or data["VCOMP"].get(t["vertical"]) or []
        )
        templates.append(
            {
                "id": t["id"],
                "name": t["name"],
                "category": t["vertical"],
                "icon": t.get("icon") or "",
                "description": t.get("desc") or "",
                "packages": t.get("pk") or [],
                "roles": t.get("roles") or [],
                "workflows": t.get("mods") or [],
                "data_objects": t.get("objs") or [],
                "integrations": t.get("ints") or [],
                "compliance": compliance,
                "agents": [
                    {"id": a, "name": agents.get(a, {}).get("name", a)}
                    for a in (data["TPL_AGENTS_X"].get(t["id"]) or [])
                ],
                "app_name": t.get("appName") or t["name"],
            }
        )
    catalogue = {
        "source": Path(html_path).name,
        "package_descriptions": data.get("PKDESC") or {},
        "templates": templates,
    }
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(
        json.dumps(catalogue, indent=1, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    return catalogue


def load_catalogue() -> dict:
    if not CATALOGUE_PATH.exists():
        raise PortError(
            f"No catalogue at {CATALOGUE_PATH}; run `app_templates port extract <Zelthy.html>`."
        )
    return json.loads(CATALOGUE_PATH.read_text(encoding="utf-8"))


def find(entry: str) -> dict:
    """A catalogue entry by id (``consentmgr``) or exact name (``Consent Management``)."""
    want = entry.strip().lower()
    for t in load_catalogue()["templates"]:
        if t["id"].lower() == want or t["name"].lower() == want:
            return t
    raise PortError(f"No catalogue entry {entry!r}; see `app_templates port list`.")


def role_name(name: str) -> str:
    """The catalogue writes roles in sentence case ("Program manager"); specs use title case."""
    return " ".join(w[:1].upper() + w[1:] for w in name.split())


def slug_for(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", name.lower().replace("&", " ")).strip("-")


def ported() -> dict:
    """{catalogue id: pack dir} for packs that were ported (template.json has ``ported_from``)."""
    out = {}
    for manifest in PACKS_DIR.glob("*/template.json"):
        try:
            src = (json.loads(manifest.read_text()).get("ported_from") or {}).get("id")
        except ValueError:
            continue
        if src:
            out[src] = manifest.parent.name
    return out


# ------------------------------------------------------------------- scaffold --


def manifest_for(entry: dict, slug: str, package_descriptions: dict) -> dict:
    """template.json for a catalogue entry. Descriptions it can't know are left empty for the author."""
    icon = entry["icon"] if entry["icon"] in CONSOLE_ICONS else ""
    return {
        "slug": slug,
        "name": entry["name"],
        "version": "0.1.0",
        "category": entry["category"],
        "icon": icon,
        "is_beta": True,
        "aka": [],
        "one_liner": entry["description"],
        "fits_when": [],
        "gives_you": list(entry["workflows"]),
        "spec_format": "yaml",
        "spec_root": "app_spec",
        "spec_dialect": "zango-app/1",
        "starter": "starter.yaml",
        # The starter is the only journey a ported template has; it doubles as the example.
        "example": "starter.yaml",
        "references": "references.json",
        # Template mode (AGENT_MODE_TEMPLATE_MODE_PLAN.html, T0): open on the preview, no brief.
        "launch": "direct",
        "welcome": {
            "message": (
                f"This is the {entry['name']} template, running on demo data. Switch roles with "
                "View as. Tell me what to change: flows, fields, screens, roles or the look. "
                "You can also build it as it is."
            ),
            "suggestions": [],
        },
        "ported_from": {"source": "Zelthy.html", "id": entry["id"]},
        "catalogue": {
            "description": entry["description"],
            "packages": [
                {"name": p, "description": package_descriptions.get(p, "")}
                for p in entry["packages"]
            ],
            "roles": [
                {"name": role_name(r), "description": ""} for r in entry["roles"]
            ],
            "workflows": [{"name": w, "description": ""} for w in entry["workflows"]],
            "data_objects": list(entry["data_objects"]),
            "integrations": list(entry["integrations"]),
            "compliance": list(entry["compliance"]),
            "recommended_agents": [a["id"] for a in entry["agents"]],
            "app_name_prefill": entry["app_name"],
            "app_prompt_prefill": "",
        },
        "changelog": "Ported from the Zelthy catalogue.",
    }


def starter_skeleton(entry: dict) -> str:
    """A starter.yaml to author: the app block and roles filled in, the rest a checklist."""
    code = re.sub(r"[^a-z0-9]+", "_", entry["name"].lower().replace("&", " ")).strip(
        "_"
    )

    def bullets(items):
        return "\n".join(f"#   - {x}" for x in items) or "#   (none listed)"

    roles = "\n".join(
        f"  - name: {role_name(r)}\n"
        "    description: TODO what this role does\n"
        "    landing: TODO\n"
        "    menu: []"
        for r in entry["roles"]
    )
    return f"""# {entry['name']}: the template's starting point. {entry['description']}
# In template mode this journey is what the creator sees the moment the app opens.
#
# PORTING CHECKLIST (delete when done). From the Zelthy catalogue entry `{entry['id']}`:
# Workflows to model (statuses + role-gated transitions):
{bullets(entry['workflows'])}
# Data objects (entities):
{bullets(entry['data_objects'])}
# Integrations (as app.custom_requirements, area: integration):
{bullets(entry['integrations'])}
# Compliance points to honour:
{bullets(entry['compliance'])}
#
# Write it in the generic Zango app spec (packs/zango_app/SCHEMA.md; examples: the other
# packs' starter.yaml). Then: `manage.py app_templates port check <dir> --shots`.
spec_version: 1

app:
  code: {code}
  name: {entry['name']}
  description: {entry['description']}
  timezone: Asia/Kolkata
  locale: en-IN
  currency: INR
  theme: {{ primary: "#4F46E5", secondary: "#64748B" }}

choice_sets: {{}}

roles:
{roles}

pages: []

modules: []

detail_views: []
"""


def scaffold(
    entry_id: str, *, dirname: str = "", slug: str = "", force: bool = False
) -> Path:
    """Write packs/<dir>/ for a catalogue entry. Never overwrites an authored starter."""
    catalogue = load_catalogue()
    entry = find(entry_id)
    slug = slug or slug_for(entry["name"])
    pack = PACKS_DIR / (dirname or slug.replace("-", "_"))
    pack.mkdir(parents=True, exist_ok=True)

    manifest_path = pack / "template.json"
    if manifest_path.exists() and not force:
        raise PortError(f"{manifest_path} exists; pass --force to rewrite it.")
    manifest = manifest_for(entry, slug, catalogue.get("package_descriptions") or {})
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n")
    starter = pack / "starter.yaml"
    if not starter.exists():
        starter.write_text(starter_skeleton(entry))
    refs = pack / "references.json"
    if not refs.exists():
        refs.write_text("[]\n")
    return pack


# ---------------------------------------------------------------------- check --


def spec_check(pack: Path, workspace: Path) -> tuple[int, str]:
    """The build's own spec linter on the starter: (exit code, its report)."""
    proc = subprocess.run(
        [
            sys.executable,
            str(SPEC_CHECK),
            str(pack / "starter.yaml"),
            "--workspace",
            str(workspace),
        ],
        capture_output=True,
        text=True,
    )
    return proc.returncode, (proc.stdout + proc.stderr).strip()


def schema_issues(pack: Path) -> list[str]:
    """The starter against the generic template's JSON Schema: what the DB lint checks on import.

    spec_check (the build's linter) is more lenient in places (it accepts keys the schema
    doesn't), so a port is only ready when both pass.
    """
    from jsonschema import Draft202012Validator

    from .spec import yamlio

    schema = json.loads((PACKS_DIR / "zango_app" / "schema.json").read_text())
    try:
        doc = yamlio.load((pack / "starter.yaml").read_text(encoding="utf-8"))
    except yamlio.SpecYAMLError as exc:
        return [f"not valid YAML: {exc}"]
    return [
        "/" + "/".join(str(p) for p in err.absolute_path) + f": {err.message}"
        for err in sorted(
            Draft202012Validator(schema).iter_errors(doc),
            key=lambda e: list(e.absolute_path),
        )
    ]


def manifest_issues(pack: Path) -> list[str]:
    """What a person still has to write in template.json."""
    m = json.loads((pack / "template.json").read_text())
    cat = m.get("catalogue") or {}
    out = []
    if not m.get("aka"):
        out.append("aka: no other names the analyst can match on")
    if not m.get("fits_when"):
        out.append("fits_when: empty")
    for key in ("roles", "workflows"):
        empty = [x["name"] for x in cat.get(key) or [] if not x.get("description")]
        if empty:
            out.append(f"catalogue.{key}: no description for {', '.join(empty)}")
    if not (m.get("welcome") or {}).get("suggestions"):
        out.append("welcome.suggestions: none (shown as chips when the app opens)")
    if not m.get("icon"):
        out.append("icon: none the console has; the category icon is used")
    return out


def screens(spec_text: str) -> list[tuple[str, str]]:
    """(role, page) for every page on every role's menu, landing first."""
    from .spec import yamlio

    doc = yamlio.load(spec_text)
    out = []
    for role in doc.get("roles") or []:
        pages = [role.get("landing")]

        def walk(items):
            for it in items or []:
                if "page" in it:
                    pages.append(it["page"])
                walk(it.get("items"))

        walk(role.get("menu"))
        for p in dict.fromkeys(x for x in pages if x):
            out.append((role["name"], p))
    return out


def render(pack: Path, out_dir: Path, width: int = 1440) -> list[Path]:
    """Screenshot the starter in the preview (the generic template's builder), per role × menu page."""
    from playwright.sync_api import sync_playwright

    spec_text = (pack / "starter.yaml").read_text(encoding="utf-8")
    html = (GENERIC_BUILDER / "app-studio.html").read_text(encoding="utf-8")
    adapter = (GENERIC_BUILDER / "adapter.js").read_text(encoding="utf-8")
    html = html.replace("</body>", f"<script>{adapter}</script></body>")
    out_dir.mkdir(parents=True, exist_ok=True)
    shots = []
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        page = browser.new_page(viewport={"width": width, "height": 900})
        page.route(
            "**/*",
            lambda r: r.continue_()
            if not r.request.url.startswith("http")
            or "fonts.g" in r.request.url
            or "unpkg.com" in r.request.url
            else r.abort(),
        )
        page.set_content(html, wait_until="domcontentloaded")
        page.wait_for_timeout(600)
        err = page.evaluate(
            "y => { window.zangoLoad(y); return S.parseErr ? String(S.parseErr.message || S.parseErr) : null }",
            spec_text,
        )
        if err:
            browser.close()
            raise PortError(f"The preview could not read the starter: {err}")
        for role, code in screens(spec_text):
            page.evaluate("l => window.ZAS_GOTO(l)", {"role": role, "page": code})
            page.wait_for_timeout(350)
            path = out_dir / f"{slug_for(role)}__{code}.png"
            page.screenshot(path=str(path))
            shots.append(path)
        browser.close()
    return shots
