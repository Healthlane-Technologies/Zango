"""Phase 1: conversational requirement gathering.

Each user message is one short SDK call that **resumes** the previous session
rather than replaying history. That matters operationally: a conversation can
span hours of human thinking time, and no worker can be held open for that.
Resume turns it into a series of short, independently-scheduled tasks.

The analyst is read-only by construction — no Write, Edit or Bash — so it can
ground its questions in the real workspace without any risk of changing it.
"""

from __future__ import annotations

import json
import re

from .prompt import PLUGIN_NAME


ANALYST_SKILL = f"{PLUGIN_NAME}:zango-requirements-analyst"
PROTOTYPE_SKILL = f"{PLUGIN_NAME}:zango-prototype"

# The analyst signals "ready for review" by emitting the spec in this fence.
_SPEC_FENCE = re.compile(r"```zango-spec[ \t]*\n(.*?)```", re.DOTALL | re.IGNORECASE)

# A template interview fills its spec in as it goes, so the analyst re-emits
# the whole thing after every answer. Those are drafts: the pane shows them,
# the user watches the shape arrive, and nothing is offered for approval until
# the ordinary ```zango-spec fence appears.
_DRAFT_SPEC_FENCE = re.compile(
    r"```zango-spec-draft[ \t]*\n(.*?)```", re.DOTALL | re.IGNORECASE
)

# How the analyst tells the platform the user accepted a template. Without it
# the choice would live only inside the model's session, so nothing downstream
# — the panel, the spec format, the build — could know about it.
_TEMPLATE_FENCE = re.compile(
    r"```zango-template[ \t]*\n(.*?)```", re.DOTALL | re.IGNORECASE
)

# Questions come back as structured choices so the user answers by clicking.
# Typing prose is the thing that stalls a non-technical user, and it is the
# analyst — not the panel — that knows which answers are plausible, so the
# options have to come from the model rather than from a fixed form.
_QUESTIONS_FENCE = re.compile(
    r"```zango-questions[ \t]*\n(.*?)```", re.DOTALL | re.IGNORECASE
)

# Caps, because this payload is rendered straight into the panel. A model that
# emits forty options has misunderstood the format, and truncating is better
# than a page the user has to scroll to answer.
MAX_QUESTIONS = 6
MAX_OPTIONS = 8
MAX_QUESTION_CHARS = 240
MAX_OPTION_CHARS = 120
QUESTION_TYPES = ("single", "multi")

MAX_MESSAGE_CHARS = 10_000

ANALYST_TOOLS = ["Read", "Glob", "Grep", "TodoWrite", "Skill"]
ANALYST_DISALLOWED = [
    "Write",
    "Edit",
    "MultiEdit",
    "NotebookEdit",
    "Bash",
    "WebFetch",
    "WebSearch",
    # A turn has no later session to wake up into.
    "ScheduleWakeup",
    "CronCreate",
    "CronDelete",
    "CronList",
    "Monitor",
    "RemoteTrigger",
    "PushNotification",
]


def extract_spec(text: str) -> str:
    """The finished spec from a ```zango-spec fence, or "" if none.

    Draft fences are removed first so that a half-answered interview can never
    be read as a finished spec — offering one for approval would let a user
    build from a journey that is still missing half its sections.
    """
    if not text:
        return ""
    matches = _SPEC_FENCE.findall(_DRAFT_SPEC_FENCE.sub("", text))
    return matches[-1].strip() if matches else ""


def extract_draft_spec(text: str) -> str:
    """The work-in-progress spec from a ```zango-spec-draft fence."""
    if not text:
        return ""
    matches = _DRAFT_SPEC_FENCE.findall(text)
    return matches[-1].strip() if matches else ""


def extract_template(text: str) -> str:
    """The template slug the analyst says the user accepted, or "".

    Validated against the catalogue rather than trusted: a slug that names no
    pack would leave the requirement claiming a template whose interview and
    schema do not exist.
    """
    if not text:
        return ""
    matches = _TEMPLATE_FENCE.findall(text)
    if not matches:
        return ""
    raw = matches[-1].strip()
    slug = ""
    try:
        data = json.loads(raw)
    except (ValueError, TypeError):
        # A bare slug on its own line is a reasonable thing for a model to
        # emit, and refusing it would lose a choice the user actually made.
        slug = raw.splitlines()[0].strip().strip("\"'") if raw else ""
    else:
        if isinstance(data, dict):
            slug = str(data.get("template") or data.get("slug") or "").strip()
        elif isinstance(data, str):
            slug = data.strip()

    from .app_templates import get_template

    template = get_template(slug)
    return template.slug if template else ""


def extract_questions(text: str) -> list:
    """Structured questions from a ```zango-questions fence.

    Everything is normalised and capped here rather than trusted: the payload
    is model output that the panel renders directly, and a malformed block
    must degrade to "no options offered" — the user can still type — rather
    than break the turn.
    """
    if not text:
        return []
    matches = _QUESTIONS_FENCE.findall(text)
    if not matches:
        return []
    try:
        raw = json.loads(matches[-1].strip())
    except (ValueError, TypeError):
        return []
    if not isinstance(raw, list):
        return []

    questions = []
    for index, item in enumerate(raw[:MAX_QUESTIONS]):
        question = _normalise_question(item, index)
        if question is not None:
            questions.append(question)
    return questions


def _normalise_question(item, index: int):
    """One validated question, or None if it cannot be rendered."""
    if not isinstance(item, dict):
        return None

    prompt = str(item.get("question") or "").strip()[:MAX_QUESTION_CHARS]
    if not prompt:
        return None

    options, seen = [], set()
    for option in item.get("options") or []:
        label = str(option).strip()[:MAX_OPTION_CHARS]
        # Duplicates make a radio group ambiguous about what was chosen.
        if label and label not in seen:
            seen.add(label)
            options.append(label)
        if len(options) >= MAX_OPTIONS:
            break
    # One option is not a choice; the user would have nothing to decide.
    if len(options) < 2:
        return None

    kind = str(item.get("type") or "single").strip().lower()
    if kind not in QUESTION_TYPES:
        kind = "single"

    # Pre-ticked defaults are the whole point: a user who agrees with the
    # analyst's reading can send without touching anything.
    selected = [
        label
        for label in (
            str(value).strip()[:MAX_OPTION_CHARS]
            for value in item.get("selected") or []
        )
        if label in seen
    ]
    if kind == "single":
        selected = selected[:1]

    return {
        "id": str(item.get("id") or f"q{index + 1}")[:64],
        "question": prompt,
        "type": kind,
        "options": options,
        "selected": selected,
        "allow_other": bool(item.get("allow_other", True)),
    }


# A template spec is YAML, and names its roles as the keys of a top-level
# `roles:` mapping. Without this, a template-based build starts with no roles
# at all and every policy it writes attaches to nobody.
_YAML_ROLES_HEADING = re.compile(r"^roles:\s*(#.*)?$")
_YAML_ROLE_KEY = re.compile(r"^(?P<indent>\s+)(?P<name>[A-Za-z][\w .\-]{1,49})\s*:")


def roles_from_yaml_spec(spec: str) -> list:
    """Role names from a YAML spec's top-level `roles:` block.

    Only the block's own keys count. Nested settings (`sees_only`,
    `scope_field`) sit deeper, so pinning to the first indent seen keeps them
    out without needing a YAML parser on model output.
    """
    names, indent, in_block = [], None, False
    for line in (spec or "").splitlines():
        if not in_block:
            in_block = bool(_YAML_ROLES_HEADING.match(line))
            continue
        if not line.strip():
            continue
        if not line[:1].isspace():
            break  # back at the top level: the block is over
        match = _YAML_ROLE_KEY.match(line)
        if not match:
            continue
        if indent is None:
            indent = match.group("indent")
        if match.group("indent") != indent:
            continue
        name = match.group("name").strip()
        if name and name not in names:
            names.append(name)
    return names


def strip_fences(text: str) -> str:
    """The conversational part of a reply, with the agent's blocks removed.

    The spec renders in its own editable pane and the questions render as
    clickable options, so repeating either as chat text is noise. The template
    declaration is a signal to the platform and was never meant to be read.
    """
    if not text:
        return ""
    cleaned = _TEMPLATE_FENCE.sub(
        "",
        _QUESTIONS_FENCE.sub("", _SPEC_FENCE.sub("", _DRAFT_SPEC_FENCE.sub("", text))),
    ).strip()
    return re.sub(r"\n{3,}", "\n\n", cleaned)


def looks_like_question(text: str) -> bool:
    """Whether the reply expects an answer, for the UI's input affordance."""
    return "?" in (text or "")


# A YAML spec has no headings; its name is a top-level key. Matched loosely
# because the analyst writes the file, not a serialiser.
_YAML_NAME = re.compile(r"^(name|journey|title)\s*:\s*(.+?)\s*$", re.MULTILINE)


def derive_title(spec_markdown: str, fallback: str) -> str:
    """Title from the spec, else the opening ask.

    Markdown specs name the app in their first heading. A template spec is
    configuration — the PSP journey names itself in `name:` — and without this
    every template requirement in the panel would be titled with the sentence
    the user happened to open with.
    """
    spec = spec_markdown or ""
    for line in spec.splitlines():
        line = line.strip()
        if line.startswith("#"):
            title = line.lstrip("#").strip()
            if title:
                return title[:255]

    # `name:` wins over `journey:` — one is words, the other is a code — so the
    # keys are checked in that order rather than in the order they appear.
    found = {key: value for key, value in _YAML_NAME.findall(spec)}
    for key in ("name", "title", "journey"):
        value = (found.get(key) or "").strip().strip("\"'")
        if value:
            return value[:255]

    return (fallback or "").strip()[:255]


_TEMPLATE_BRIEF = """\
## Templates available for this ask

These are products Zelthy already builds and maintains. If what the user
described is plainly one of them, say so on your FIRST reply and let them
choose — a template turns a months-long build into a description, and not
mentioning one that fits is the most expensive mistake you can make here.
Read nothing from a pack until they accept; everything you need to make the
offer is below.

{catalogue}

Making the offer: ask it as the first question of your first
```zango-questions block, with the template pre-selected. Keep building from
scratch as the other option, in their words, and offer it once only.

If they accept, that turn must carry a fence naming the template —

```zango-template
{{"template": "<slug>"}}
```

— and from then on you follow that pack's INTERVIEW.md and SCHEMA.md instead
of your general interview.
"""


_TEMPLATE_MODE = """\
## This app is built on a template

Template: {name} (slug `{slug}`, version {version})

The user chose this template before the conversation started, so do not
offer templates and do not ask whether to use one. Read `{interview}` first,
then `{schema}`, and follow that interview instead of your general one. The
spec is YAML in the template's own vocabulary, rooted at `{root}`.

{draft}
Change the draft with the spec tools (spec_outline, spec_get, spec_set,
spec_add, spec_remove, spec_move, spec_replace_section, spec_validate) as the
answers come in, and call spec_mark_ready when the interview is finished. They
replace the fences the interview mentions.
"""

_TEMPLATE_FIRST_DRAFT = """\
The requirement already holds the template's starter journey as a draft —
it is at `{starter}` — and the user watches it fill in beside the chat. Every
answer should change that draft; nothing is built until they approve it."""

_TEMPLATE_ADOPTED = """\
The user has just chosen this template, part-way through the conversation.
From now on the spec is the template's YAML, edited only with the spec tools —
never a Markdown write-up or a fenced spec. Before anything else, write into
the draft everything already agreed in this conversation (one
spec_replace_section per section), so the preview beside the chat shows their
app; then carry on with the interview."""

# Template mode (template_mode.py): the app opened on the template's own preview, no brief.
_TEMPLATE_OPENED = """\
## This app was opened on a template, as it is

Template: {name} (slug `{slug}`, version {version}). Its vocabulary is in `{schema}`; the
spec is YAML rooted at `{root}`.

The user picked this template, named the app and has been looking at its full preview: the
template's spec (already in the draft) drawn by the kit page, which is the prototype
(`body.html`, `imported/*`). That is the agreed baseline. They have not written a brief; their
message below is the first change they want.

- Edit, don't interview. Make the change they ask for in this turn, then say in a sentence or
  two what changed. Ask only when the request is genuinely ambiguous, and then one short
  question with options, never a questionnaire. Do not re-describe the template to them.
- The preview draws the YAML: change the spec with the spec tools and the preview follows on its
  own (pages, columns, filters, forms, fields, statuses and their buttons, roles, menus, the demo
  data). Do not run the first-draft steps for the whole app.
- A reference they attach (screenshot, sketch, brand guide, a page to match) is about the look, not
  the data: apply it to the prototype (`proto_design`, `proto_patch`) in this turn. Changing only
  labels or fields in the YAML does not apply it.
- The design is completely open. Do exactly what the user says, in their words, labels and layout.
  Never approximate an instruction with the nearest thing the YAML can say. A screen you were not
  asked about stays as the template builds it. Where each kind of change goes:
  - The look (colours, gradients, borders, radius, shadows, type, spacing, decorations): CSS rules in
    `look.css` (proto_write it if it isn't there). It loads after every other stylesheet, so its
    rules win without `!important`. Write them on the kit's own classes, which are also what the
    built app reproduces and is checked against: `.d-head` (a record's header) and its `h1`, `.d-sub`,
    `.d-av`, `.d-facts`/`.d-fact`, `.d-stats`/`.d-stat`, `.d-tabs`/`.d-tab`/`.d-tab.on`, `.d-panel`;
    `.z-card`, `.z-t th`/`.z-t td`, `.z-btn`/`.z-btn.pri`, `.z-qf`/`.z-qf.on`, `.z-chip`, `.z-badge`,
    `.z-ph h1`; the shell `.z-side`, `.z-ni`/`.z-ni.on`, `.z-top`, `.z-logo`, `.z-user`. Scope a rule
    with a parent (`.d-head .z-btn`) to change one place only.
  - The brand colour: `app.theme.primary` in the YAML (the kit sets it on every render; CSS can't
    override it).
  - Content and structure (pages, columns, filters, forms, fields, statuses, tabs, panels, facts,
    stats, dashboard blocks, menus): the YAML. The kit draws only what the YAML says.
  - `body.html`, `tokens.css` and `imported/styles.css` don't change what the preview shows (the kit
    redraws the page from its scripts and its own stylesheet): never edit them for the look.
  - A layout the YAML can't say and CSS can't reach (a widget the kit has no block for): tell the
    user plainly it can't be shown or built on this template, and offer the nearest thing it can do.
- They press Commit for build when the preview is right. Never ask whether to finish, mark it
  ready or build.
"""

_TEMPLATE_CHANGE_DRAFT = """\
This is a change to an app that already runs on the template. The draft
below is the journey the app was last approved on; change only what the user
asks for and keep everything else exactly as it is.

```yaml
{spec}
```"""


_TEMPLATE_DRAFT = """\
## Draft this journey in one pass

Template: {name} (slug `{slug}`, version {version})

The user gave you their material instead of answering an interview. Do not
interview them. Follow `{drafting}` exactly: read everything, draft EVERY
section of the journey with the spec tools (spec_replace_section, one call per
section), flag every value you did not take straight from their material with
spec_flag, fix every error spec_validate reports, describe how each role gets
its work done with one spec_set_workflows call, and finish with one
spec_open_decisions call holding only the real gaps (at most 8).

Vocabulary: `{schema}`. The draft currently holds `{starting_point}`.

{documents}
Reference journeys you may start from (each is a complete, valid journey):
{references}
{base}
Reply in three or four lines when you are done; the user reviews the flags and
decisions on the Review tab.
"""


def _template_draft_block(requirement, template, docs_dir: str) -> str:
    refs = (
        "\n".join(
            f"- `{r['id']}` — {r['title']}: {r['summary']}  ({r['path']})"
            for r in template.references
        )
        or "- (none; start from the starter journey)"
    )
    chosen = next(
        (r for r in template.references if r["id"] == requirement.reference_id), None
    )
    base = (
        f"The user chose `{chosen['id']}` as the base: start from it.\n"
        if chosen
        else "Pick the closest reference as your base, or keep the starter if none is close.\n"
    )
    documents = (
        f"The user's documents are in `{docs_dir}` — start with `{docs_dir}/INDEX.md`.\n"
        if docs_dir
        else "There are no documents: draft from the written brief below.\n"
    )
    spec = (requirement.spec_markdown or "").strip()
    starting_point = (
        "the template's starter journey"
        if spec == (template.starter_yaml or "").strip()
        else "the journey this app was last approved on — change only what the material asks for"
    )
    return _TEMPLATE_DRAFT.format(
        name=template.name,
        slug=template.slug,
        version=template.version or "current",
        drafting=template.file_path("drafting") or "DRAFTING.md",
        schema=template.file_path("schema"),
        starting_point=starting_point,
        documents=documents,
        references=refs,
        base=base,
    )


def _template_mode_block(requirement, template) -> str:
    spec = (requirement.spec_markdown or "").strip()
    is_change = bool(spec) and spec != (template.starter_yaml or "").strip()
    draft = (
        _TEMPLATE_CHANGE_DRAFT.format(spec=spec)
        if is_change
        else _TEMPLATE_FIRST_DRAFT.format(
            starter=template.file_path("starter") or "starter.yaml"
        )
    )
    return _TEMPLATE_MODE.format(
        name=template.name,
        slug=template.slug,
        version=template.version or "current",
        interview=template.file_path("interview"),
        schema=template.file_path("schema"),
        root=template.spec_root or "the top level",
        draft=draft,
    )


def _template_opened_block(template) -> str:
    return _TEMPLATE_OPENED.format(
        name=template.name,
        slug=template.slug,
        version=template.version or "current",
        schema=template.file_path("schema"),
        root=template.spec_root or "the top level",
    )


def compose_analyst_prompt(
    requirement, ctx, user_message: str, docs_dir: str = ""
) -> str:
    """First turn dispatches the skill and supplies context; later turns are
    just the user's reply, since the session is resumed."""
    if requirement.session_id:
        adopted = getattr(requirement, "mode", "") == "adopted"
        template = (
            requirement.template if adopted and requirement.template_slug else None
        )
        if template is not None and template.is_yaml:
            return (
                _template_mode_block(requirement, template)
                + "\n\n"
                + _TEMPLATE_ADOPTED
                + "\n\n## The user's reply\n\n"
                + user_message.strip()
            )
        if getattr(requirement, "mode", "") == "template" and requirement.template_slug:
            # The template's documents move with its version; a path from an earlier turn may be
            # an old copy that lacks what the kit draws now.
            current = requirement.template
            schema = current.file_path("schema") if current is not None else ""
            if schema:
                return (
                    f"[The template's SCHEMA.md this turn: `{schema}`. Read the YAML keys there, "
                    "not in a copy from an earlier turn.]\n\n" + user_message.strip()
                )
        return user_message.strip()

    packages = (
        ", ".join(f"{p['name']} {p['version']}".strip() for p in ctx.packages)
        or "(none yet — appbuilder, crud and workflow are installed before the build)"
    )
    modules = ", ".join(m["name"] for m in ctx.modules) or "(none — empty app)"
    roles = ", ".join(ctx.roles) or "(only the framework defaults)"

    from .app_templates import catalogue_digest

    # A requirement bound to a template up front skips the offer entirely.
    bound = requirement.template if getattr(requirement, "template_slug", "") else None
    opened = bound is not None and getattr(requirement, "mode", "") == "template"
    if opened:
        templates = "\n" + _template_opened_block(bound)
    elif bound is not None and getattr(requirement, "mode", "") == "draft":
        templates = "\n" + _template_draft_block(requirement, bound, docs_dir)
    elif bound is not None:
        templates = "\n" + _template_mode_block(requirement, bound)
    else:
        catalogue = catalogue_digest()
        templates = (
            "\n" + _TEMPLATE_BRIEF.format(catalogue=catalogue) if catalogue else ""
        )

    closing = (
        "Make the change now, in the spec and the prototype, then tell them what changed."
        if opened
        else "Draft now; do not ask questions before the journey is written."
        if bound is not None and getattr(requirement, "mode", "") == "draft"
        else "Read the workspace first, then ask your opening questions."
    )
    return f"""/{ANALYST_SKILL}

## The app you are scoping

app_name: {ctx.app_name}
workspace: {ctx.workspace_path}   (read-only; inspect it before asking)
installed_packages: {packages}
existing_modules: {modules}
existing_roles: {roles}

## What the user asked for

{user_message.strip()}
{templates}
{closing}
"""


_SPEC_TOOLS_APPEND = (
    "\n\nThis requirement is built on an app template, and its YAML journey is "
    "edited ONLY through the mcp__spec__* tools: spec_outline and spec_get to "
    "read it, spec_set / spec_add / spec_remove / spec_move / "
    "spec_replace_section to change it, spec_validate to check it, and "
    "spec_mark_ready when the interview is finished. After every answer, write "
    "what you learned into the draft with these tools before you reply — the "
    "user watches it change beside the chat. Do not paste the journey into your "
    "reply and do not use zango-spec or zango-spec-draft fences, even where the "
    "template's interview says to; the tools replace them. A refused change "
    "tells you why: fix the value, don't retry it unchanged. A message may end "
    "with a [Preview: …] note: where the user was in the preview and, if they "
    'pointed at something, its path in the spec. Words like "this" and '
    '"here" mean that part; read it with spec_get before you change it. Never '
    "ask the user whether the spec is finished, whether to mark it ready or whether to "
    "build: they look at the preview and press Commit for build themselves when it is "
    "right. So finish every change in the turn you make it: a custom page, tab or panel "
    "gets its `preview` sketch and its contract (`data`, `acceptance`), and a custom "
    "requirement its `acceptance` (and `trigger` when it runs on its own). An edit's "
    "result says NOT DONE when something is missing; fix it before you reply."
)


_PREVIEW_TOOLS_APPEND = (
    "\n\nYou can check your custom screens — custom pages, 360 tabs and panels drawn by "
    "a `preview` sketch — in the same preview the user sees. An edit to one reports what "
    "its sketch drew for each role (errors, empty parts, records read, values shown): read "
    "it and fix what is wrong before you reply; a ⚠ line is not a pass. When the edit changed "
    "a sketch, a screenshot of the screen comes with it: look at it and check it shows what the "
    "user asked for, with real values (if a field it needs is empty in the demo data, the "
    "screen only shows its empty case). preview_check runs them all; preview_look screenshots "
    "one as another role, record or width. Lists, forms, 360 pages and views need no check: the "
    "template draws them from the spec. spec_mark_ready wants every custom screen to draw "
    "cleanly and to have been looked at once since it last changed."
)


_OPEN_PROTOTYPE_HEAD = (
    '\n\nOPEN PROTOTYPE MODE. The user turned on "Free design": next to the YAML you '
    "write a working HTML prototype of their app, in any look, and that prototype is the "
    "preview they see. Load the zango-prototype skill before your first prototype write "
    "and follow it.\n"
    "- Write the prototype in parts with the mcp__spec__proto_* tools, never as one big "
    "file; change it later with proto_patch. Call proto_outline first in any turn that "
    "touches it.\n"
)

# The first draft of an app drawn from scratch. Template mode starts on an existing prototype.
_OPEN_FIRST_DRAFT = (
    "- First draft: as soon as the interview tells you who uses the app, what moves "
    "through it and who decides, write manifest.json, tokens.css, app.css, data.js, "
    "shell.js and the home screen yourself, so the user sees their app within minutes. "
    "Then hand every other screen to the screen-writer agent (Agent tool, subagent_type "
    '"screen-writer"), several in ONE message so they run in parallel, each with a '
    "brief: screen id, purpose, personas, records and fields, actions and their outcomes, "
    "states to show. Review what they report and fix shared parts yourself.\n"
)

_OPEN_PROTOTYPE_BODY = (
    "- Keep the YAML in step in the same turn: every persona is a role, every screen maps "
    'to a page (or is marked "only": "prototype" in the manifest, like a sign-in '
    "screen), every action is a transition or a custom requirement.\n"
    "- Runtime first, however custom a screen looks: the build draws record screens with the "
    "standard runtime and themes them with the prototype's tokens. So every screen that shows "
    "records maps to a crud page (lists, boards, filters, forms), a detail_views page (record "
    "pages, tabs) or a dashboard. Use type: custom only for what none of those can show, and "
    "give it a `reason` saying what (spec_mark_ready refuses a custom page without one and "
    "lists the rest for the user).\n"
    "- Record the mapping in the YAML's top-level `prototype.screens`: one entry per manifest "
    "screen, `{id, maps: /pages/@<code>}` or `/detail_views/@<code>`, or `{id, only: prototype, "
    "why}` (SCHEMA.md, prototype). The build themes standard pages and rebuilds custom ones from "
    "their screen.\n"
    "- The user approves the preview as the app: what it shows is what gets built, exactly, "
    "and nothing it doesn't show. Never rename what the preview says; a record screen of an "
    "uploaded page is `rebuild: true`; leave something out only when the user agreed, and then "
    "take it out of the preview too.\n"
    "- The build follows the YAML, so the YAML says everything each screen shows, in the "
    "prototype's own words: menu items, labels, groups and order per role (a screen not built "
    "stays in the menu through its entry's `menu`), page titles, list columns, status tabs "
    "(quick_filters: never `default: true`, a list opens with no chip selected), 360 tabs, sections, sidebar panels, dashboard blocks, buttons and field "
    "labels. A 360 has the prototype's tabs and no others; a section heading is a section's or "
    "panel's `title`, not a field of that name. Each persona's menu in the prototype is its "
    "role's `roles[].menu`, exactly; when a role gets less than the prototype's menu shows, "
    "patch the prototype's menu for that persona (never widen the role). "
    "Where the YAML can't say it (a stage tracker, a custom row layout), add `rebuild: "
    "true` with a `why` naming it. Only what the user agreed to leave out goes in the entry's "
    "`not_built` with a why, and it comes out of the preview too. spec_mark_ready renders the prototype and lists anything left out.\n"
    "- Once tokens.css (or the imported stylesheet) is settled, call proto_design to record the "
    "look in app.design; call it again whenever the tokens change.\n"
    "- The look is free in this mode: the template's theme/ui limits and its \"fonts and "
    'layouts are not offered" rule do not apply. Custom pages need no `preview` sketch; '
    "their screen in the prototype is the sketch. Contracts (data, acceptance) still apply.\n"
    "- A [Preview: …] note names the screen and persona the user was on; locate the text "
    "with proto_find, then patch only what they asked for.\n"
)

# What to do with uploads when the prototype is drawn from scratch.
_OPEN_UPLOADS = (
    "- If the user uploaded an HTML file (their app, or a prototype to match), that file IS the "
    "prototype: call proto_import with its name in your first turn, before writing the spec, "
    "and never redraw it. Skip it only if the user says the file is a reference, not the app. "
    "An empty prototype leaves the user's preview pane blank. Then fill manifest.json (screens "
    "and roles from the page's own navigation and personas), add one small part that calls "
    "ZAS.ready({go}) with the page's own router, and write the YAML from what the page shows.\n"
    "- Anything else the user gives (screenshots, photos or sketches, a PDF, a brand guide, an "
    "HTML page they call a reference, or nothing at all) is material for the look and the "
    "content, not the prototype. Read each image and document, take the palette, type, density "
    "and layout from it, and DRAW the prototype yourself as in the first-draft step. The "
    "preview pane stays blank (and the spec cannot be approved) until the prototype has parts, "
    "so never end a turn that has a spec but no prototype: ask your interview questions only "
    "after the first draft is on screen, and say which parts you took from the references."
)

_OPEN_PROTOTYPE_APPEND = (
    _OPEN_PROTOTYPE_HEAD + _OPEN_FIRST_DRAFT + _OPEN_PROTOTYPE_BODY + _OPEN_UPLOADS
)


# What a kit prototype can show of a reference's layout, and the YAML that says it (zango_app SCHEMA.md).
_DESIGN_FEATURES = (
    "DESIGN FEATURES the kit draws (and the build makes), and their YAML:\n"
    "  - list cell with a second line: `table.columns.<k>.secondary: [paths]` (`secondary_style: "
    "mono` for codes); avatar of initials or an icon before it: `columns.<k>.icon: initials` | "
    "<lucide name> | {by, map, default}\n"
    "  - status tabs with counts: `table.quick_filters: [{label, where, count: true}]`\n"
    "  - line under a list's title: `pages[].subtitle: text` or `{text, stat: {count: true | sum: "
    "<field>, where, format, suffix}}`\n"
    "  - a coloured cell: `columns.<k>.highlight: {when, tone}`; a status or choice as a badge: "
    "`source: status`, choice `color`\n"
    "  - record page: `detail_views[].header` (avatar, title, subtitle parts such as the code, "
    "badges, facts, banners), `stats` (KPI tiles), `tabs` (`count_badge`), `layout: "
    "header_tabs_sidebar` with `sidebar` cards (fields, timeline, mini_table) for a summary on "
    "the right, `summary` sections in columns, `timeline`\n"
    "  - KPI tiles, charts, lists and boards: a `type: dashboard` page's `blocks`\n"
    "  - KPI tiles above a list: `pages[].stats: [{label, count: true | sum: <number field>, where, "
    "format, icon, tone, hint}]` (crud pages)\n"
    "  - a pill next to a cell value: `columns.<k>.badge: {label, when, tone}`; a step bar and "
    '"Step i of n" under a status: `columns.<k>.progress: true | {steps: [codes]}` (`source: '
    "status`); a chevron at the end of clickable rows: `table.row_chevron: true`\n"
    "  - a lifecycle stepper in the record header: `detail_views[].header.stepper: true | {steps: "
    "[status codes]}` (a status off the steps, like rejected, shows as an end marker)\n"
    "  - menu: `roles[].menu` with groups (section labels), icons and counts (`count: true | "
    "{where}` on a crud page's item); the user card at the top of the sidebar: `app.shell: "
    "{user: top}`\n"
    "  Not drawn by the kit: a search box in the top bar.\n"
)


_TEMPLATE_MODE_APPEND = (
    "\n\nTEMPLATE MODE. The app opened on a template's own prototype, so it already exists: "
    "edit it. Do not draw the app from scratch, do not run the first-draft steps and do not "
    "interview. The design is completely open: do exactly what the user says, in their words, "
    "labels and layout, and never approximate an instruction with the nearest thing the YAML can "
    "say. The look goes in `look.css` (proto_write / proto_patch it): CSS on the kit's own "
    "classes (`.d-head`, `.d-fact`, `.d-stat`, `.d-tabs`, `.d-tab.on`, `.d-panel`, `.z-card`, `.z-t th`, "
    "`.z-btn.pri`, `.z-qf.on`, `.z-side`, `.z-ni.on`, `.z-top`…); it loads last, so its rules win, and the "
    "built app is checked against exactly these parts. The brand colour is `app.theme.primary` in the "
    "YAML. Content and structure are the YAML. `body.html`, `tokens.css` and the kit's own stylesheet "
    "and scripts don't change what the preview shows: never edit them for the look.\n"
    "- References are applied, not just read. A screenshot, photo or sketch, a brand guide, or an "
    "HTML page the user calls a reference (or does not say what it is for) is a design reference. "
    "Apply it to every screen, in this order, before you reply:\n"
    "  1. See it. An HTML reference: open it with ref_look, once per kind of screen it has (a list, "
    "a record page, a dashboard), with `steps` to get past a sign-in screen or into a record. Never "
    "work out its look by grepping the source. An image: Read it.\n"
    "  2. Its structure, in the YAML, wherever the kit can draw it (DESIGN FEATURES below): two-line "
    "cells, avatars, counted status tabs, subtitles, record header facts and badges, stats, tabs "
    "with counts, the side summary card. Keep the app's own entities, fields and data; take the "
    "reference's way of showing them.\n"
    "  3. Its look, in `look.css`, with the values ref_look measured (colours, fonts, sizes, "
    "radii, shadows, row height, padding), never guessed: palette, type, density and decorations.\n"
    "  4. proto_look each kind of screen you changed, compare it with the reference's screenshot, "
    "fix what differs and look again.\n"
    "  5. In your reply, name what you took from it and, plainly, each part of the reference the "
    "kit can't draw (from the list below), so the user can decide.\n"
    "A reply that only changes colours has not applied a reference that shows a different layout.\n"
    + _DESIGN_FEATURES
    + "- An HTML page the user says is their app, or a screen to redraw, is not a reference: "
    "proto_import it, or draw that screen again, as they ask.\n"
    '- A request about how something looks ("make the sidebar dark", "rounder cards", "a hero '
    'header") is a look change even without a reference: it goes in `look.css` in this turn.\n'
    "- Never ask whether to build.\n"
    "- After every visual change, and before you reply, look at the result with proto_look "
    "(the screen you changed, as the persona who sees it): check for overlapping or clipped "
    "text, broken cards and anything that is not what the user asked, fix it and look again. "
    "Only say a change is done once you have looked; if proto_look can't render here, say you "
    "could not check it."
)


def build_analyst_options(
    *, ctx, creds, requirement, spec_server=None, docs_dir="", preview=False
):
    """Read-only ClaudeAgentOptions for a gathering turn.

    ``spec_server`` (template requirements) exposes the spec tools; with it the
    analyst edits the draft through tools rather than fences, and gets more
    turns, since every tool call is one. ``preview``: the server also has the
    custom-screen checks (preview_check, preview_look).
    """
    from claude_agent_sdk import ClaudeAgentOptions

    from django.conf import settings as dj

    from .app_templates import templates_dir
    from .config import load_config
    from .options import SKILL_PLUGIN_DIR, agent_home, build_env

    cfg = load_config()

    kwargs = dict(
        cwd=ctx.workspace_path,
        # Template packs are materialised under templates_dir() and the
        # analyst has to read them once a template is accepted. It has no
        # write tool at all, so widening what it can *read* costs nothing.
        add_dirs=[SKILL_PLUGIN_DIR, templates_dir(), *([docs_dir] if docs_dir else [])],
        setting_sources=["user"],
        plugins=[{"type": "local", "path": SKILL_PLUGIN_DIR}],
        skills=[ANALYST_SKILL],
        allowed_tools=list(ANALYST_TOOLS),
        # Belt and braces: the analyst must not be able to touch the app.
        disallowed_tools=list(ANALYST_DISALLOWED),
        permission_mode="default",
        include_partial_messages=False,
        system_prompt={
            "type": "preset",
            "preset": "claude_code",
            "append": (
                "You are gathering requirements, not implementing. Never "
                "create or modify files. Keep the scope small and say what "
                "you are deliberately leaving out.\n\n"
                "You are talking to a NON-TECHNICAL BUSINESS USER. Ask short, "
                "direct questions in everyday language — three or four per "
                "turn, one or two lines each. Put them in a ```zango-questions "
                "JSON block with 2-6 options each and your recommendation "
                "pre-filled in `selected`, so the user answers by clicking "
                "rather than typing; outside the block write only a one-line "
                "lead-in, never the questions again. "
                "Never use technical vocabulary "
                "(entity, model, field, schema, CRUD, workflow package, "
                "policy, React, frontend, component, API, async task, MVP, "
                "migration, module) and never ask them to make a technical "
                "decision. Work out the technical shape silently; ask only "
                "about how their business works.\n\n"
                "If the run context lists an app template that plainly fits "
                "what they described, offer it on your first reply and let "
                "them choose. When they accept, declare it in a "
                "```zango-template fence, follow that pack's interview, and "
                "re-emit the spec so far in a ```zango-spec-draft fence after "
                "every answer so they watch it fill in. The plain "
                "```zango-spec fence stays reserved for the finished spec."
            ),
        },
        env=build_env(creds, agent_home()),
        max_turns=int(cfg.analyst_max_turns or 40),
        max_budget_usd=float(cfg.analyst_budget_usd or 2.0),
    )
    if spec_server is not None:
        from .spec_tools import ALLOWED_TOOL_NAMES, SERVER_NAME

        kwargs["mcp_servers"] = {SERVER_NAME: spec_server}
        kwargs["allowed_tools"] = [*kwargs["allowed_tools"], *ALLOWED_TOOL_NAMES]
        kwargs["max_turns"] = max(kwargs["max_turns"], 80)
        kwargs["max_budget_usd"] = float(
            getattr(dj, "AGENT_MODE_ANALYST_TEMPLATE_BUDGET_USD", 0)
            or max(kwargs["max_budget_usd"], 4.0)
        )
        if getattr(requirement, "mode", "") == "draft" and not requirement.session_id:
            # One pass over a whole journey: many tool calls in one turn.
            kwargs["max_turns"] = max(kwargs["max_turns"], 150)
            kwargs["max_budget_usd"] = float(
                getattr(dj, "AGENT_MODE_ANALYST_DRAFT_BUDGET_USD", 0)
                or max(kwargs["max_budget_usd"], 8.0)
            )
        kwargs["system_prompt"] = {
            **kwargs["system_prompt"],
            "append": kwargs["system_prompt"]["append"]
            + _SPEC_TOOLS_APPEND
            + (_PREVIEW_TOOLS_APPEND if preview else ""),
        }
    if spec_server is not None and getattr(requirement, "preview_mode", "") == "open":
        from .prototype import is_drafting, screen_writer_agent

        kwargs["allowed_tools"] = [*kwargs["allowed_tools"], "Agent", "Task"]
        kwargs["skills"] = [*kwargs["skills"], PROTOTYPE_SKILL]
        kwargs["agents"] = {"screen-writer": screen_writer_agent()}
        # The CLI starts sub-agents in the background by default, and the turn ends (and
        # kills them) as soon as the analyst stops. Run them in the foreground: an Agent
        # call then returns only once its screen is written. AgentDefinition(background=
        # False) alone did not do this (CLI 0.2.152).
        kwargs["env"] = {**kwargs["env"], "CLAUDE_CODE_DISABLE_BACKGROUND_TASKS": "1"}
        if is_drafting(requirement.prototype_parts):
            # The first draft (or one that left screens unwritten) writes the whole app: many tool calls, and the
            # screen writers' cost counts towards this turn's budget.
            kwargs["max_turns"] = max(kwargs["max_turns"], 250)
            kwargs["max_budget_usd"] = float(
                getattr(dj, "AGENT_MODE_ANALYST_PROTO_BUDGET_USD", 0)
                or max(kwargs["max_budget_usd"], 15.0)
            )
        kwargs["system_prompt"] = {
            **kwargs["system_prompt"],
            "append": kwargs["system_prompt"]["append"]
            + (
                # Template mode edits an existing prototype: it has no first draft and
                # takes uploads as references, so those two parts are left out.
                _OPEN_PROTOTYPE_HEAD + _OPEN_PROTOTYPE_BODY + _TEMPLATE_MODE_APPEND
                if getattr(requirement, "mode", "") == "template"
                else _OPEN_PROTOTYPE_APPEND
            ),
        }
    if cfg.analyst_model:
        kwargs["model"] = cfg.analyst_model
    if cfg.analyst_effort:
        kwargs["effort"] = cfg.analyst_effort
    if getattr(dj, "AGENT_MODE_CLAUDE_BIN", ""):
        kwargs["cli_path"] = dj.AGENT_MODE_CLAUDE_BIN
    if requirement.session_id:
        kwargs["resume"] = requirement.session_id
    return ClaudeAgentOptions(**kwargs)
