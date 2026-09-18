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
    """Return the spec from a ```zango-spec fence, or "" if none."""
    if not text:
        return ""
    matches = _SPEC_FENCE.findall(text)
    return matches[-1].strip() if matches else ""


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


def strip_fences(text: str) -> str:
    """The conversational part of a reply, with the agent's blocks removed.

    The spec renders in its own editable pane and the questions render as
    clickable options, so repeating either as chat text is noise.
    """
    if not text:
        return ""
    cleaned = _QUESTIONS_FENCE.sub("", _SPEC_FENCE.sub("", text)).strip()
    return re.sub(r"\n{3,}", "\n\n", cleaned)


def looks_like_question(text: str) -> bool:
    """Whether the reply expects an answer, for the UI's input affordance."""
    return "?" in (text or "")


def derive_title(spec_markdown: str, fallback: str) -> str:
    """Title from the spec's first heading, else the opening ask."""
    for line in (spec_markdown or "").splitlines():
        line = line.strip()
        if line.startswith("#"):
            title = line.lstrip("#").strip()
            if title:
                return title[:255]
    return (fallback or "").strip()[:255]


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

    return f"""/{ANALYST_SKILL}

## The app you are scoping

app_name: {ctx.app_name}
workspace: {ctx.workspace_path}   (read-only; inspect it before asking)
installed_packages: {packages}
existing_modules: {modules}
existing_roles: {roles}

## What the user asked for

{user_message.strip()}

Read the workspace first, then ask your opening questions.
"""


def build_analyst_options(*, ctx, creds, requirement):
    """Read-only ClaudeAgentOptions for a gathering turn."""
    from claude_agent_sdk import ClaudeAgentOptions

    from django.conf import settings as dj

    from .config import load_config
    from .options import SKILL_PLUGIN_DIR, agent_home, build_env

    cfg = load_config()

    kwargs = dict(
        cwd=ctx.workspace_path,
        add_dirs=[],
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
                "about how their business works."
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
