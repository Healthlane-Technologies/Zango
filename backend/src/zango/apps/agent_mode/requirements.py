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
        for label in (str(value).strip()[:MAX_OPTION_CHARS] for value in item.get("selected") or [])
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


def compose_analyst_prompt(requirement, ctx, user_message: str) -> str:
    """First turn dispatches the skill and supplies context; later turns are
    just the user's reply, since the session is resumed."""
    if requirement.session_id:
        return user_message.strip()

    packages = (
        ", ".join(f"{p['name']} {p['version']}".strip() for p in ctx.packages)
        or "(none yet — appbuilder, crud and workflow are installed before the build)"
    )
    modules = ", ".join(m["name"] for m in ctx.modules) or "(none — empty app)"
    roles = ", ".join(ctx.roles) or "(only the framework defaults)"

    from .app_templates import catalogue_digest

    catalogue = catalogue_digest()
    templates = (
        "\n" + _TEMPLATE_BRIEF.format(catalogue=catalogue) if catalogue else ""
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
Read the workspace first, then ask your opening questions.
"""


def build_analyst_options(*, ctx, creds, requirement):
    """Read-only ClaudeAgentOptions for a gathering turn."""
    from claude_agent_sdk import ClaudeAgentOptions

    from django.conf import settings as dj

    from .config import load_config
    from .app_templates import templates_dir
    from .options import SKILL_PLUGIN_DIR, agent_home, build_env

    cfg = load_config()

    kwargs = dict(
        cwd=ctx.workspace_path,
        # Template packs are materialised under templates_dir() and the
        # analyst has to read them once a template is accepted. It has no
        # write tool at all, so widening what it can *read* costs nothing.
        add_dirs=[SKILL_PLUGIN_DIR, templates_dir()],
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
    if cfg.analyst_model:
        kwargs["model"] = cfg.analyst_model
    if cfg.analyst_effort:
        kwargs["effort"] = cfg.analyst_effort
    if getattr(dj, "AGENT_MODE_CLAUDE_BIN", ""):
        kwargs["cli_path"] = dj.AGENT_MODE_CLAUDE_BIN
    if requirement.session_id:
        kwargs["resume"] = requirement.session_id
    return ClaudeAgentOptions(**kwargs)
