# The design kit

What makes a page look designed rather than generated. Three files:

| File | Read when | Size |
|---|---|---|
| [tokens.md](tokens.md) | 5b (pick the accent) and 5c (write `tokens.css`) | ~5 KB |
| [directions.md](directions.md) | 5b, to pick the row — then record it | ~3 KB |
| [treatments.md](treatments.md) | 5d/5e, before writing any page | ~5 KB |

**Read all three inside the page subagent, not in the main thread.** Together
they are ~13 KB; carried in the main thread they are re-sent on every
remaining turn of the build, and the pages are written in subagents anyway.

`design-system.md` is the *bar* — what must be true of a finished page, and the
four states every page needs. This kit is the *material* — the values and
recipes that get you there. Read the bar once at 5b; read the kit at the point
of writing.

## Why this exists

A page assembled from theme variables and Tailwind defaults comes out flat:
one hue plus gray, three levels of text, single-layer shadows, every block
rendered identically. Every rule in `design-system.md` can be satisfied by
such a page — that is the documented failure it warns about.

What closes the gap is not more instruction. It is specific values: a seven-
level text hierarchy, a derived brand ramp, compound shadows with the inset
highlight, a second hue, and two or three card treatments per page instead of
one. That is what these files carry.
