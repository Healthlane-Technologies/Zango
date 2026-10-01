# Drafting a Patient Support Program in one pass

The user has given you their material — an SOP, an RFP, a protocol, a process
map, or a detailed written brief — instead of answering an interview. Your job
is to turn it into a **complete journey in one turn**: every section filled,
every value you did not take straight from their material flagged, and only
the real gaps left as a short list of decisions. Do not interview them.

Read `SCHEMA.md` for what every key means before you write anything.

## 1. Read everything first

1. The documents: start with `INDEX.md` in the documents directory (its path is
   in your run context). Read each PDF directly; for Word, Excel and text files
   read the `.txt` extract. Skim once end to end, then go back for detail.
2. The brief the user typed, if any. Where it disagrees with a document, the
   brief wins — it is newer — and you flag the conflict.
3. The reference journeys listed in your run context. Pick the closest one as
   your base (or use the one the user chose). If none is close, start from
   `starter.yaml`.

## 2. Write the journey section by section

Use `spec_replace_section` — one call per section, with the whole section's
YAML — rather than many small edits. Work in this order, because later
sections refer to codes declared in earlier ones:

1. program (`/journey`, `/name`)
2. roles (`/roles`)
3. masters (`/masters`)
4. documents (`/documents`)
5. catalogue (`/catalogue`)
6. patient — attributes, create, labels, table (`/patient`), with its
   lifecycle (`/patient/states`, `/patient/steps`) and consent
7. programs — eligibility, required documents, enrolment lifecycle, schemes
   and orders (`/programs`)
8. detail (`/detail`)
9. adverse events, reports, extra modules, custom requirements

Keep codes snake_case and reuse them exactly across sections — a step's `by`
must name a declared role, a link field's `to` a declared master. After the
last section, call `spec_validate` and fix every **error** before you finish.

## 3. Flag what you did not read

Call `spec_flag` for every value that is not stated in the user's material.
Flag the most specific path you can (a field, a step, a scheme — not a whole
section), and say in `note`, in plain words, what you assumed:

- `inferred` — you deduced it from something the material says. Put the
  passage in `source`: `document` is the document's name exactly as
  `INDEX.md` lists it in bold (not the numbered file name), `locator` is
  like "p. 4" or "sheet Orders", and `quote` is a short extract.
- `reference` — you kept it from the reference journey because the material
  says nothing either way.
- `default` — the template's default, untouched.
- `missing` — the material should say this and doesn't; you put a placeholder.

Values the material states outright need no flag — cite nothing for them.
A draft with no flags almost always means you did not flag honestly.

## 4. Leave only real decisions

Finish with one `spec_open_decisions` call: at most **8** questions, only for
things you genuinely cannot decide and that change how the program works
(who approves enrolment, whether distributors see each other's orders, how a
scheme accrues). Each has 2–5 options, your recommended one, and a one-line
why. Everything else is a flag, not a question.

## 5. Reply briefly

Your chat reply is three or four lines: what you drafted from, the base you
chose, how many flags and decisions there are, and that the user can review
them on the Review tab. Do not paste the journey and do not list the flags —
the panel shows them.

## Later turns

When the user answers the decisions or asks for changes, apply them with the
spec tools, `spec_unflag` anything they have now confirmed, and call
`spec_open_decisions` again with whatever is still open (an empty list when
nothing is). Call `spec_mark_ready` only when there are no open decisions and
no errors.
