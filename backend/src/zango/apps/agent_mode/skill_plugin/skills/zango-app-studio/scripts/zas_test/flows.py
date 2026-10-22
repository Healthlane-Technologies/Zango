"""
UI layer, group `flows`: the app's journeys driven end to end in a real browser, checked on screen
and in the backend after every step. The other UI groups prove pages render; this one proves a
person can actually do the work: fill each create form through its real widgets, run every manual
workflow move from the 360 header, and add child records from the 360's tabs.

    python3 -m zas_test.ui --workspace <ws> --only flows [--role "Executive"]

Per entity with a create form, as the first role that may create it:
  create        list page → Add → fill every field the API layer would fill (same values, same
                .zas/test_fixtures.py hooks) → Submit; the dialog closes, the record exists in the
                backend and the typed values were saved (a phone saves with its country code)
  <transition>  the record created above is walked along the longest chain of manual moves, each
                one from the 360 header (button or ⋯ menu) and its dialog; every other manual move
                is run on a record the API walks to its from-status. After each move: the backend
                status is `to`, the header badge shows it, a timeline event was written
  tab_<code>    per related_table tab whose child the role may add: 360 → tab → Add → Submit; the
                child is saved under this parent
A step that fails is retried over the API with the same values, and the failure says which side
broke: "the API accepted the same values" points at the frontend (widget, pattern, default), "the
API refused them too" points at the backend. A screenshot of every failure lands in
.zas/screens/flows/. Results go to the "ui" layer with ids ui.flow.<entity>.<step>.<role>.
"""

import datetime
import json
import os
import re
import shutil
import sys
import tempfile

from . import browser
from . import api as A

FORM_TIMEOUT = 15000
STEP_TIMEOUT = 20000
PY_REPR = re.compile(r"^<(function|bound method|built-in|lambda)\b|object at 0x[0-9a-f]+>$")
TEXT_WIDGETS = ("TextFieldWidget", "EmailFieldWidget", "NumberFieldWidget", "TextareaFieldWidget",
                "PasswordFieldWidget", "UrlFieldWidget", "IntegerFieldWidget")


def slug(s):
    return re.sub(r"[^a-z0-9]+", "_", str(s).lower()).strip("_")


class StepFailed(Exception):
    """A UI step that did not complete; the message already names the side that broke. `uid` is
    set when the record was saved anyway (saved with a wrong value), so later steps can use it."""

    def __init__(self, msg, uid=None):
        super().__init__(msg)
        self.uid = uid


class Blocked(Exception):
    """An earlier step this one depends on failed."""


# ───────────────────────── form filling ─────────────────────────

class Form:
    """One open FormRenderer dialog: fill fields by widget, submit, read back what went wrong."""

    def __init__(self, page, schema):
        self.page = page
        self.dialog = page.locator('[role="dialog"]').last
        self.props = (schema.get("json_schema") or {}).get("properties") or {}
        self.ui = schema.get("ui_schema") or {}
        self.files_dir = tempfile.mkdtemp(prefix="zas_flow_")

    def wait(self):
        self.dialog.wait_for(state="visible", timeout=FORM_TIMEOUT)
        if self.props:
            self.dialog.locator('[id^="zango-form_"]:visible').first.wait_for(timeout=FORM_TIMEOUT)
            self.page.wait_for_timeout(300)  # the form's sync pass settles after the first paint

    def box(self, k):
        """The field's own container: the nearest ancestor of its label that holds its error slot."""
        return self.dialog.locator(f'#zango-form_{k}__label').locator(
            f'xpath=ancestor::*[.//*[@id="zango-form_{k}__error"]][1]')

    def label_for(self, k, v):
        p = self.props.get(k) or {}
        enum = p.get("enum") or (p.get("items") or {}).get("enum") or []
        names = p.get("enumNames") or (p.get("items") or {}).get("enumNames") or []
        sv = str(v)
        if sv in [str(e) for e in enum] and names:
            return str(names[[str(e) for e in enum].index(sv)])
        return sv

    def fill(self, k, v, file=None):
        widget = (self.ui.get(k) or {}).get("ui:widget") or ""
        box = self.box(k)
        if box.count() == 0:
            raise StepFailed(f"field {k!r} is not on the form (hidden by show_when, or missing from the form)")
        if file:
            path = os.path.join(self.files_dir, file[0])
            with open(path, "wb") as fh:
                fh.write(file[1])
            box.locator('input[type="file"]').first.set_input_files(path)
        elif widget == "MobileFieldWidget":
            cc = (self.props.get(k) or {}).get("countryCode") or ""
            national = str(v)[len(cc):] if cc and str(v).startswith(cc) else str(v).lstrip("+")
            box.locator(f'#zango-form_{k}').fill(national)
        elif "Select" in widget:
            values = v if isinstance(v, list) else [v]
            for one in values:
                label = self.label_for(k, one)
                # react-select: a click opens the menu, keystrokes filter it (fill() does not)
                box.locator('input[role="combobox"]').first.click(force=True)
                self.page.keyboard.type(label, delay=10)
                opt = self.page.locator('[id^="react-select-"][id*="-option-"], [role="option"]').filter(
                    has_text=re.compile(r"^\s*" + re.escape(label) + r"\s*$")).first
                try:
                    opt.wait_for(timeout=8000)
                    opt.click()
                except Exception:
                    raise StepFailed(f"{k}: no option {label!r} in the dropdown")
        elif widget == "RadioFieldWidget":
            self.pick_radio(box, k, v)
        elif widget in ("CheckboxFieldWidget", "SwitchFieldWidget") or (self.props.get(k) or {}).get("type") == "boolean" \
                and box.locator('input[type="checkbox"]').count():
            box.locator('input[type="checkbox"]').first.set_checked(str(v).lower() in ("true", "1", "yes"))
        elif "Date" in widget:
            self.fill_date(box, k, str(v))
        elif box.locator(f'#zango-form_{k}').count():
            box.locator(f'#zango-form_{k}').fill(str(v))
        else:
            raise StepFailed(f"{k}: don't know how to fill widget {widget or '(none)'}")

    def pick_radio(self, box, k, v):
        p = self.props.get(k) or {}
        if p.get("type") == "boolean":
            want = ("yes", "true") if str(v).lower() in ("true", "1", "yes") else ("no", "false")
        else:
            want = (self.label_for(k, v).lower(), str(v).lower())
        labels = box.locator('input[type="radio"]').evaluate_all(
            """els => els.map(e => ((document.querySelector('label[for="' + e.id + '"]') || e.closest('label') || e.parentElement || {}).innerText || e.value || '').trim().toLowerCase())""")
        for i, lbl in enumerate(labels):
            if lbl in want:
                # the input itself is visually hidden (0×0): click its label, as a person would
                box.locator('input[type="radio"]').nth(i).evaluate(
                    "e => (document.querySelector('label[for=\"' + e.id + '\"]') || e.closest('label') || e).click()")
                if not box.locator('input[type="radio"]').nth(i).is_checked():
                    raise StepFailed(f"{k}: clicking {lbl!r} did not select it")
                return
        raise StepFailed(f"{k}: no radio option matching {v!r} (options {labels})")

    def fill_date(self, box, k, v):
        """Pick the date in the widget's calendar, as a person would. Typing into the day/month/year
        segments shows the date but leaves the form value unset ("This field is required")."""
        m = re.match(r"(\d{4})-(\d{2})-(\d{2})(?:[ T](\d{2}):(\d{2}))?", v)
        if not m:
            raise StepFailed(f"{k}: cannot type date {v!r}")
        y, mo, d, hh, mm = m.groups()
        want = datetime.date(int(y), int(mo), int(d))
        box.locator("button").last.click()  # the calendar toggle (the other button clears)
        cal = self.page.locator(".react-calendar").last
        cal.wait_for(timeout=5000)
        for _ in range(120):
            shown = datetime.datetime.strptime(cal.locator(".react-calendar__navigation__label").inner_text().strip(), "%B %Y")
            step = (want.year - shown.year) * 12 + (want.month - shown.month)
            if step == 0:
                break
            cal.locator(".react-calendar__navigation__next-button" if step > 0
                        else ".react-calendar__navigation__prev-button").click()
        label = f"{want.strftime('%B')} {want.day}, {want.year}"
        tile = cal.locator(f'.react-calendar__tile:has(abbr[aria-label="{label}"])').first
        if tile.count() == 0 or tile.is_disabled():
            raise StepFailed(f"{k}: {v} cannot be picked in the calendar (outside its min/max?)")
        tile.click()
        if hh is not None and box.locator('input[name="hour24"], input[name="hour12"]').count():
            box.locator('input[name="hour24"], input[name="hour12"]').first.click()
            self.page.keyboard.type(str(int(hh)))
            box.locator('input[name="minute"]').first.click()
            self.page.keyboard.type(str(int(mm)))
        if self.page.locator(".react-calendar").count():
            self.dialog.locator(f'#zango-form_{k}__label').click()  # close it (not Escape: the Modal closes on Escape)

    def errors(self):
        """Field and form errors on screen, error toasts, and an open dialog's own alert."""
        got = self.page.evaluate("""() => {
          const out = {};
          document.querySelectorAll('[id^="zango-form_"][id$="__error"]').forEach(e => {
            const t = (e.innerText || '').trim(); if (t) out[e.id.slice(11, -7) || '(form)'] = t; });
          document.querySelectorAll('.zas-toast.err, [role="dialog"] [role="alert"].zas-note').forEach((e, i) => {
            const t = (e.innerText || '').trim(); if (t) out['(message ' + (i + 1) + ')'] = t; });
          return out; }""")
        return got or {}


def submit_button(dialog):
    """The form's own Submit: a type=submit button on create forms, a plain button on workflow forms."""
    typed = dialog.locator('button[type="submit"]')
    return typed.first if typed.count() else dialog.get_by_role("button", name=re.compile(r"^(submit|save)$", re.I)).last


def submit(page, dialog, url_part, click):
    """Click Submit and wait for the POST whose URL contains `url_part`. Returns (response json | None, status)."""
    try:
        with page.expect_response(lambda r: r.request.method == "POST" and url_part in r.url, timeout=STEP_TIMEOUT) as info:
            click()
        r = info.value
        try:
            return r.json(), r.status
        except Exception:
            return None, r.status
    except Exception:
        return None, None  # no request left the browser: client-side validation stopped it


def closed(dialog, timeout=STEP_TIMEOUT):
    try:
        dialog.wait_for(state="detached", timeout=timeout)
        return True
    except Exception:
        try:
            return not dialog.is_visible()
        except Exception:
            return True


# ───────────────────────── the runner ─────────────────────────

class Flows:
    def __init__(self, U, b):
        self.U, self.b, self.ws, self.M = U, b, U.ws, U.M
        self.C = A.Ctx(U.ws, None)
        self.C.login_all()
        self.pages = {}

    # ----- plumbing -----
    def rp(self, role):
        if role not in self.pages:
            self.pages[role] = browser.RolePage(self.b, self.U.target, self.C.session(role))
        return self.pages[role]

    def close(self):
        for p in self.pages.values():
            p.close()

    def fail_shot(self, role, name):
        try:
            self.rp(role).shot(self.ws, "flows", f"{slug(role)}__{name}")
        except Exception:
            pass

    def schema(self, role, ent, params):
        code, j = self.C.get(role, self.C.ep(ent), action="initialize_form", **(params or {}))
        if code != 200:
            raise StepFailed(f"initialize_form as {role} → HTTP {code}")
        return self.C.body(j).get("form") or {}

    def status_label(self, ent, code):
        for s in (self.M["entities"][ent].get("workflow") or {}).get("statuses") or []:
            if s["code"] == code:
                return s["label"]
        return code

    def timeline_count(self, ent, uuid, role):
        code, j = self.C.get(role, self.C.ep(ent), view="detail", action="zas_timeline", object_uuid=uuid)
        b = self.C.body(j) if code == 200 else {}
        return len((b or {}).get("events") or []) if isinstance(b, dict) else 0

    # ----- values (what the API layer would send) -----
    def create_values(self, ent, role, params, form):
        C, E = self.C, self.M["entities"][ent]
        props = (form.get("json_schema") or {}).get("properties") or {}
        required = set((form.get("json_schema") or {}).get("required") or [])
        fmap = {f["key"]: f for f in E["fields"]}
        vals = {}
        if C.fixtures and hasattr(C.fixtures, "values"):
            fv = C.fixtures.values
            takes = len(__import__("inspect").signature(fv).parameters) >= 4
            vals.update((fv(C, ent, role, params) if takes else fv(C, ent, role)) or {})
        tag = A.rnd()
        data, files = {}, {}
        for k in sorted((required | (C.needed_fields(ent) & set(props)) | set(vals)) & set(props)):
            if k in vals:
                data[k] = vals[k]
                continue
            p = props.get(k) or {}
            if p.get("default") not in (None, ""):
                continue  # the browser already shows the form's own default (a 360 parent preset)
            f = fmap.get(k) or {"key": k, "type": "boolean" if p.get("type") == "boolean" else "text"}
            if f.get("type") == "link" and not p.get("enum") and f.get("to") in self.M["entities"] and f["to"] != ent:
                C.create(f["to"])
            v, fl = A.value_for(f, p, tag)
            if fl:
                files[k] = fl
            elif v is not None:
                data[k] = v
        return data, files

    def transition_values(self, ent, t, role):
        C, data, files = self.C, {}, {}
        tag = A.rnd()
        for f in t.get("form") or []:
            v, fl = A.value_for(f, {"enum": [c["id"] for c in f.get("choices") or []]}, tag)
            if fl:
                files[f["key"]] = fl
            elif v is not None:
                data[f["key"]] = v
        if C.fixtures and hasattr(C.fixtures, "transition_values"):
            data.update(C.fixtures.transition_values(C, ent, t["name"], role) or {})
        return data, files

    # ----- checks against what was saved -----
    def saved_problems(self, ent, uuid, role, data):
        row = self.C.record(ent, uuid, role) or self.C.record(ent, uuid)
        if row is None:
            return ["the new record is not in the list the API returns"]
        fmap = {f["key"]: f for f in self.M["entities"][ent]["fields"]}
        probs = []
        for k, v in data.items():
            f = fmap.get(k) or {}
            t = f.get("type", "text")
            if k not in row or t not in ("text", "long_text", "email", "phone", "choice"):
                continue
            got = json.dumps(row[k], default=str) if not isinstance(row[k], str) else row[k]
            if t == "phone":
                ok = re.sub(r"\D", "", str(v))[-10:] in re.sub(r"\D", "", got)
            elif t == "choice":
                ok = str(v) in got or str(v).replace("_", " ").lower() in got.lower() or \
                    any(c.get("label", "") in got for c in f.get("choices") or [] if c.get("id") == v)
            else:
                ok = str(v)[:40] in got
            if not ok:
                probs.append(f"{k}: typed {v!r}, saved {row[k]!r}")
        return probs

    def bad_defaults(self, form):
        props = (form.get("json_schema") or {}).get("properties") or {}
        return [f"{k}: the form's default is a Python object ({p['default']!r}), not a value"
                for k, p in props.items() if isinstance(p.get("default"), str) and PY_REPR.search(p["default"])]

    # ----- one create through the browser -----
    def ui_create(self, ent, role, open_form, params=None):
        """open_form(page) opens the dialog. Returns the new uuid; raises StepFailed with a triaged detail."""
        page = self.rp(role).page
        form = self.schema(role, ent, params)
        problems = self.bad_defaults(form)
        data, files = self.create_values(ent, role, params, form)
        form = self.schema(role, ent, params)  # a fixture may have just created an option a select needs
        open_form(page)
        F = Form(page, form)
        F.wait()
        for k, v in data.items():
            F.fill(k, v)
        for k, fl in files.items():
            F.fill(k, None, file=fl)
        j, status = submit(page, F.dialog, "form_type=create_form",
                           lambda: submit_button(F.dialog).click())
        b = self.C.body(j) if isinstance(j, dict) else {}
        uid = str((b or {}).get("object_uuid") or "") or None
        if not uid or not closed(F.dialog):
            raise StepFailed(self.triage_create(ent, role, params, data, F, status, b))
        self.C.made.setdefault(ent, []).append(uid)
        problems += self.saved_problems(ent, uid, role, data)
        if problems:
            raise StepFailed("saved, but: " + "; ".join(problems), uid=uid)
        return uid

    def triage_create(self, ent, role, params, data, F, status, body):
        on_screen = F.errors()
        where = ("no request was sent: the browser's own validation stopped the form" if status is None
                 else f"the server answered HTTP {status}: {json.dumps((body or {}).get('errors') or body)[:300]}")
        try:
            api_uid = self.C.create(ent, role, values=dict(data), params=params)
            side = f"The API accepted the same values (created {api_uid}), so the problem is in the browser form"
        except Exception as e:
            side = f"The API refused the same values too ({str(e)[:200]}), so the problem is in the backend"
        return f"{where}. On screen: {on_screen or 'no error shown'}. Typed: {data}. {side}."

    # ----- one transition through the 360 -----
    def ui_transition(self, ent, uuid, t, role):
        C, page = self.C, self.rp(role).page
        if C.fixtures and hasattr(C.fixtures, "before_transition"):
            C.fixtures.before_transition(C, ent, t["name"], uuid, role)
        before = self.timeline_count(ent, uuid, role)
        self.rp(role).open(browser.detail_path(self.M, ent, uuid), wait='[data-zas="header"], [data-zas="empty"]')
        header = page.locator('[data-zas="header"]')
        if header.count() == 0:
            raise StepFailed(f"the 360 did not open for {role}")
        btn = header.locator(f'[data-zas="action"][data-zas-key="{t["name"]}"]')
        if btn.count() == 0:
            more = header.locator('button[aria-label="More actions"]')
            if more.count():
                more.first.click()
            btn = page.locator(f'[role="menuitem"][data-zas-key="{t["name"]}"]')
        if btn.count() == 0:
            raise StepFailed(f"no {t['label']!r} button or menu item on the 360 for {role} "
                             f"(status {C.status_of(ent, uuid)})")
        if btn.first.is_disabled():
            raise StepFailed(f"{t['label']!r} is disabled: {btn.first.get_attribute('title') or 'no reason shown'}")
        data, files = self.transition_values(ent, t, role)
        btn.first.click()
        dialog = page.locator('[role="dialog"]').last
        if t.get("form"):
            code, j = C.get(role, C.ep(ent), view="workflow", action="initialize_form", transition_type="status",
                            transition_name=C.engine(ent, t["name"], C.status_of(ent, uuid)), object_uuid=uuid)
            F = Form(page, (C.body(j) or {}).get("form") or {})
            F.wait()
            for k, v in data.items():
                if k in F.props:
                    F.fill(k, v)
            for k, fl in files.items():
                F.fill(k, None, file=fl)
            j, status = submit(page, dialog, "process_transition",
                               lambda: submit_button(dialog).click())
        else:
            F = Form(page, {})
            dialog.wait_for(state="visible", timeout=FORM_TIMEOUT)
            j, status = submit(page, dialog, "process_transition",
                               lambda: dialog.get_by_role("button", name=t["label"]).last.click())
        ok_post = isinstance(j, dict) and j.get("success", True) is not False and status == 200
        if not ok_post or not closed(dialog):
            on_screen = F.errors()
            where = ("no request was sent: the dialog's own validation stopped it" if status is None
                     else f"the server answered HTTP {status}: {json.dumps(C.body(j) if isinstance(j, dict) else j)[:300]}")
            good, msg = C.run(ent, uuid, t["name"], role, data=dict(data))
            side = ("The API ran the same move with the same values, so the problem is in the browser"
                    if good else f"The API refused it too ({msg}), so the problem is in the backend")
            raise StepFailed(f"{where}. On screen: {on_screen or 'no error shown'}. Sent: {data}. {side}.")
        probs = []
        st = C.status_of(ent, uuid)
        if st != t["to"]:
            probs.append(f"backend status is {st}, expected {t['to']}")
        page.wait_for_timeout(500)
        badge = page.locator('[data-zas="header"] [data-zas="badge"][data-zas-key="status"]')
        want = self.status_label(ent, t["to"])
        if badge.count() and want.lower() not in badge.first.inner_text().lower():
            probs.append(f"header badge reads {badge.first.inner_text()!r}, expected {want!r}")
        if self.timeline_count(ent, uuid, role) <= before:
            probs.append("no new timeline event")
        if self.rp(role).errors:
            probs.append(f"browser errors: {self.rp(role).errors[:2]}")
        if probs:
            raise StepFailed("moved, but: " + "; ".join(probs))

    # ----- one child add from a 360 tab -----
    def ui_tab_add(self, hero, uuid, tab, role):
        child, param = tab["entity"], tab["param"]
        self.rp(role).open(browser.detail_path(self.M, hero, uuid), wait='[data-zas="header"], [data-zas="empty"]')

        def open_form(page):
            page.locator(f'[data-zas="tab"][data-zas-key="{tab["code"]}"]').first.click()
            page.wait_for_load_state("networkidle")
            add = page.locator('[data-zas="page"] [data-zas="action"][data-zas-key="add"]')
            try:
                add.first.wait_for(timeout=8000)
            except Exception:
                raise StepFailed(f"no Add button on the {tab['label']!r} tab for {role} "
                                 f"(hero status {self.C.status_of(hero, uuid)})")
            add.first.click()
        uid = self.ui_create(child, role, open_form, params={param: uuid})
        rows, _ = self.C.rows(role, child, **{param: uuid})
        if uid not in [str(r.get("object_uuid")) for r in rows or []]:
            raise StepFailed(f"saved {child} {uid}, but the tab's list for this {hero} does not include it")
        return uid


def longest_path(wf, roles_ok):
    """The longest chain of manual moves from the initial status, by transition name."""
    manual = [t for t in wf["transitions"] if not t.get("system") and roles_ok(t)]
    best = []

    def walk(st, path, seen):
        nonlocal best
        if len(path) > len(best):
            best = list(path)
        for t in manual:
            if st in t["from"] and t["to"] not in seen:
                walk(t["to"], path + [t], seen | {t["to"]})
    walk(wf["initial"], [], {wf["initial"]})
    return best


def g_flows(U, b):
    shutil.rmtree(os.path.join(U.ws, ".zas", "screens", "flows"), ignore_errors=True)  # only this run's failures
    F = Flows(U, b)
    C, M = F.C, F.M
    try:
        for ent, E in M["entities"].items():
            creators = [r for r in C.creators(ent) if r in C.sessions and (not U.roles or r in U.roles)]
            list_page = next((code for code, P in M["pages"].items()
                              if P.get("type") == "crud" and P.get("entity") == ent), None)
            role = creators[0] if creators else None
            wf = E.get("workflow") or {}
            uid, blocked = None, None
            if role and list_page:
                def t_create(role=role, ent=ent, list_page=list_page):
                    nonlocal uid
                    F.rp(role).open(M["pages"][list_page]["route"])
                    try:
                        uid = F.ui_create(ent, role, lambda p: p.locator('[data-zas="action"][data-zas-key="add"]').first.click())
                    except StepFailed as e:
                        uid = e.uid  # saved with a problem: the walk can still use it
                        raise
                    return True, ""
                run_step(U, F, f"ui.flow.{ent}.create.{slug(role)}", f"{E['name']}: create from the list page",
                         role, f"entities.{ent}.form.create", t_create, f"{ent}__create")
                if uid is None:
                    blocked = f"the {E['name']} could not be created in the browser"

            if wf and wf.get("initial"):
                path = longest_path(wf, lambda t: any(r in C.sessions for r in t.get("roles") or []))
                done = set()
                for t in path:
                    actor = next(r for r in t["roles"] if r in C.sessions)

                    def t_move(t=t, actor=actor, ent=ent):
                        if blocked:
                            raise Blocked(blocked)
                        F.ui_transition(ent, uid, t, actor)
                        return True, ""
                    if run_step(U, F, f"ui.flow.{ent}.{t['name']}.{slug(actor)}", f"{E['name']}: {t['label']} from the 360",
                                actor, f"entities.{ent}.workflow.transitions.{t['name']}", t_move, f"{ent}__{t['name']}") != "pass":
                        blocked = blocked or f"{t['label']} failed earlier in this {E['name']}'s walk"
                    done.add(t["name"])
                for t in wf["transitions"]:
                    actor = next((r for r in t.get("roles") or [] if r in C.sessions), None)
                    if t.get("system") or t["name"] in done or not actor:
                        continue

                    def t_side(t=t, actor=actor, ent=ent):
                        try:
                            other = C.record_in(ent, t["from"][0])
                        except A.Skip as e:
                            raise Blocked(str(e))
                        F.ui_transition(ent, other, t, actor)
                        return True, ""
                    run_step(U, F, f"ui.flow.{ent}.{t['name']}.{slug(actor)}", f"{E['name']}: {t['label']} from the 360",
                             actor, f"entities.{ent}.workflow.transitions.{t['name']}", t_side, f"{ent}__{t['name']}")

            for vcode, V in (M.get("detail_views") or {}).items():
                if V["hero"] != ent:
                    continue
                for tab in V.get("tabs") or []:
                    if tab.get("type") != "related_table" or not tab.get("add"):
                        continue
                    adders = [r for r in C.creators(tab["entity"]) if r in C.sessions
                              and (not V.get("roles") or r in V["roles"]) and C.can(ent, r, "detail")]
                    if not adders:
                        continue
                    actor = adders[0]

                    def t_tab(tab=tab, actor=actor, ent=ent):
                        hero = None
                        if C.fixtures and hasattr(C.fixtures, "record_for"):
                            hero = C.fixtures.record_for(C, ent, actor)
                        hero = hero or uid
                        if not hero:
                            raise Blocked(f"no {E['name']} to open")
                        F.ui_tab_add(ent, hero, tab, actor)
                        return True, ""
                    run_step(U, F, f"ui.flow.{ent}.tab_{tab['code']}.{slug(actor)}",
                             f"{E['name']}: {tab.get('add', {}).get('label') or 'Add'} from the {tab['label']} tab",
                             actor, f"detail_views.{vcode}.tabs.{tab['code']}", t_tab, f"{ent}__tab_{tab['code']}")
    finally:
        F.close()


def run_step(U, F, id, title, role, path, fn, shot):
    """U.check with a failure screenshot; a Blocked step is a skip. Returns the status recorded."""
    def wrapped():
        try:
            return fn()
        except Blocked as e:
            # the runner's own SkipCheck: under `python -m zas_test.ui` that module is __main__
            raise sys.modules[type(U).__module__].SkipCheck(f"blocked: {e}")
        except StepFailed as e:
            F.fail_shot(role, shot)
            return False, str(e)
        except Exception:
            F.fail_shot(role, shot)
            raise
    U.check(id, title, role, path, wrapped)
    return U.results[-1]["status"]
