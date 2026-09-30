# App templates

A template is a product Zelthy already builds and maintains — the software is
written, and a new client is described rather than developed. When the user's
ask is plainly one of these, offering the template is the single most useful
thing the analyst can do: it turns a months-long build into a description.

Each directory here is one template:

| directory | what it builds |
|---|---|
| `psp/` | Patient Support / Patient Assistance Programs |

## What a template directory holds

| file | when to read it |
|---|---|
| `template.json` | the manifest — name, when it fits, what it gives you. The platform already put a summary of this in your prompt, so you do **not** need to read it to make the offer. |
| `INTERVIEW.md` | **read this first** once the user accepts. It replaces the general interview. |
| `SCHEMA.md` | the spec format. Read before writing any part of the spec. |
| `starter.yaml` | the defaults every interview starts from. |
| `example.yaml` | one real, fully-answered spec, for depth. |

## The rules that apply to every template

- **Offer once.** If the user says no, build from scratch and never raise it
  again.
- **Read nothing until they say yes.** The offer is made from the summary the
  platform gave you. Reading a template pack the user then declines is wasted
  budget.
- **Declare the choice.** The turn on which the user accepts must carry a
  `zango-template` fence naming the slug, so the platform records which
  template this requirement is for.
- **The template's own format wins.** A template that specifies YAML gets YAML,
  not the general Markdown spec headings.
