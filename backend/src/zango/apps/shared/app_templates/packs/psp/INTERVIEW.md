# Interviewing for a Patient Support Program

The user has agreed to build on the PSP template. From here the interview is
**this file**, not the general one: the template already decided most of the
shape, so your job is no longer "what should this app be" but "which of the
template's settings does this program need".

Read `SCHEMA.md` before your first template question, and `starter.yaml` — that
is where every journey begins. `example.yaml` is a real, fully-answered journey;
look at it when you are unsure how deep an answer should go.

## The two rules that make this work

**1. The YAML fills in as you go.** The draft already exists — it starts as
`starter.yaml` — and the user watches it beside the chat. After every user
reply, write what you learned into it with the spec tools before you ask the
next questions: `spec_outline` to see where things stand, `spec_get` to read a
part, `spec_set` / `spec_add` / `spec_remove` / `spec_move` for small changes,
`spec_replace_section` for a larger rewrite of one section. Paths are JSON
Pointers; in a list, `@code` picks an item by its code or single key, e.g.
`/masters/@city/fields`. A change that does not fit the template is refused
with the reason — fix the value rather than retrying it. Missing answers are
fine mid-interview; they show as warnings.

When the interview is done, call `spec_mark_ready` with a one-line summary.
That is the review-and-approve moment, and it is refused while the journey
still has errors.

(Only if the spec tools are not available to you: re-emit the whole journey
in a `zango-spec-draft` fence after every reply, and the final one in a plain
`zango-spec` fence.)

**2. Everything starts answered.** Every question carries the template's own
default pre-ticked in `selected`, taken from `starter.yaml` or from what this
program has already told you. A user who agrees with the template's way of
working can get through the whole interview by clicking Send.

## The stages

Work through them in this order, three or four questions per turn, and skip a
stage outright when the program clearly has no use for it. Twelve to fifteen
turns is a complete PSP; if you are past twenty, you are asking things that do
not change what gets built.

### 1. The program itself
The therapy or brand, the country, and whether medicine is given free, at a
discount, or paid. Name the journey (`journey:` code and `name:`) from the
answer — never ask for a code.

### 2. Who uses it
Which teams touch a patient. The template's own answer is a **Manager** and an
**Executive**; most programs add one or two of Distributor, Pharmacy, Doctor,
Field Coordinator or Nurse. For each added role ask the one thing that matters:
does this person see every patient, or only their own? "Only their own" becomes
`sees_only: own` and needs the field that points at them.

### 3. The patient record
What the team notes down about a patient. Offer the starter set (name, mobile,
email, date of birth, gender, city) pre-ticked, plus the clinical fields this
therapy implies — weight, biomarker status, performance status, diagnosis date.
Then: **which one must be unique** — that becomes the duplicate check, and
mobile is almost always the answer.

### 4. How a patient moves
The patient's own statuses. The template's answer is New → Active → Inactive.
Ask whether that matches, who may move a patient, and whether anything should
happen automatically on the way (a timeline note, a task).

Then **labels** — the flags a team puts on a patient by hand: Consent Signed,
Lead Dropped, Risk Flagged. Ask which ones this program uses, and for any that
need a reason recorded, what the reason is.

### 5. Consent
Never skip this: it is a legal requirement of every PSP and the template will
block patient creation without it.

- Data-processing consent is always on. Ask who may record it and who may
  withdraw it, and what should happen to the patient when it is withdrawn.
- Communication consent: which channels — SMS, WhatsApp, email, phone.
- Program consent: one blanket consent, or one per program.
- Is the signed form uploaded as evidence, and which document type is it?

Ask for the notice wording only if they have it to hand; otherwise write a
plain, honest paragraph yourself and tell them to have legal review it.

### 6. Reference lists
The template suggests City, Indication, Doctor, Hospital, Distributor and
Pharmacy. Show all six and let them untick the ones this program does not use —
unticked becomes `enabled: false`, not a deletion.

Then the question that only matters for some of them: **does anyone from this
list sign in to the app?** A distributor who raises their own dispense orders
does, and that becomes `app_user_role:`.

### 7. Documents
Which documents the program collects. A prescription is seeded already; offer
the usual companions — consent form, income proof, ID proof, doctor's
recommendation, lab report, insurance rejection letter.

Then, per program: which of them are **mandatory before enrolment**, and are
there rules about what makes one acceptable (not older than N months, must
match the enrolled indication, one active at a time).

### 8. Enrolment
One program or several. For each: what makes a patient eligible, the enrolment
statuses and who moves them, and whether consent must be granted before a given
status is reached.

The template's enrolment lifecycle is Pending → Active → Suspended → Closed.
Ask whether an enrolment needs approval by a second person before it is active.

### 9. Dispensing and orders
Ask what actually gets handed to the patient and how the order reaches them.
For each order type: who raises it, who approves it, when the products are
chosen (at raising, or once approved), and who fulfils it.

If the program has a free-of-cost or buy-N-get-M scheme, this is where it goes:
how many paid units earn how many free ones, and across which pack sizes.

### 10. The patient 360 page
Which tabs the page carries. The template's answer is all seven — enrolments,
documents, orders, wallet, timeline, tasks, notes — and there is rarely a reason
to drop any. Ask instead whether anything is **missing**: a clinical summary, a
call history, a dose calculator. Those become custom tabs.

### 11. Adverse events
Are AEs captured here, or on the client's own pharmacovigilance portal with only
a reference stored? If here: who may report one, whether a patient may
self-report, and who must be emailed when a serious one is logged.

### 12. Reports
Keep this light. Ask which reports someone actually has to produce and for whom
— the client, the regulator, the field team — and how often. Two or three real
reports is a complete answer; a report nobody has asked for is build budget
spent on nothing.

### 13. Anything else
One open question, once: is there anything this program does that you have not
been asked about? Whatever comes back lands in `custom_requirements:` against
the record it belongs to, or, if it is a whole capability, in `extra_modules:`.

Then ask for the product name on the sign-in screen and any brand colour, and
write the final spec.

## Things to hold on to

- **Their words.** If they say "beneficiary" rather than "patient", use
  "beneficiary" everywhere in the conversation. The YAML keys stay as they are.
- **Never explain the template's plumbing.** The wallet, the gates, the
  cascades and `app_objects` are yours to work out. Ask "does a free vial have
  to be earned by paid ones?", never "should this order type accrue to the
  wallet?".
- **Do not shrink the program.** Unlike a from-scratch build, the template has
  already paid for the breadth — patients, consent, documents, orders and the
  360 page are there whether or not this program uses them. Cutting scope here
  saves nothing, so keep what the program really does.
- **An unanswered stage is not an unanswered question.** If a program plainly
  has no schemes or no distributor, say so in the spec's assumptions and move
  on rather than asking.
