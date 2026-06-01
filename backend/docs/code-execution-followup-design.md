# Code Execution — Follow-up Design

Two follow-ups requested. This document is a design plan only — no code changes
in this commit.

1. Switch `models.FileField` → `ZFileField` for the feature's file columns.
2. Block writes to `django.conf.settings.*` from user snippets; reads stay
   allowed.

---

## 1 · Switch to `ZFileField`

### What `ZFileField` is

`src/zango/core/storage_utils.py:64` defines a thin subclass of
`models.FileField` that opinionates three things:

```python
class ZFileField(models.FileField):
    def __init__(self, ..., upload_to="", validators=[validate_file_extension], **kw):
        super().__init__(
            upload_to=(RandomUniqueFileName),         # always — caller's value ignored
            validators=[validate_file_extension],     # always — extension allowlist
            **kw,
        )
        if make_public is False:
            self.storage.default_acl = "private"
```

Three consequences:

| Aspect | Today (`models.FileField`) | After (`ZFileField`) |
|---|---|---|
| Storage path | `codexec/snippets/<snippet_id>/<uuid>` and `codexec/runs/<exec_id>/<kind>/<uuid>` via our `_*_upload_to` callables | `<tenant>/CodeSnippetFile/<uuid>.<ext>` and `<tenant>/CodeExecFile/<uuid>.<ext>` via Zango's `RandomUniqueFileName` |
| `upload_to` callable | Required, lives in `models.py` | Not used — `ZFileField` hard-codes its own |
| Extension validation | None — anything goes | `.pdf, .doc, .docx, .jpg, .jpeg, .png, .svg, .xls, .xlsx, .mp3, .wav, .ppt, .pptx, .zip, .ico, .mp4, .webm, .csv, .json` only |
| S3 ACL | Whatever the backend sets | Forced to `private` (good for us) |

### The extension-allowlist problem

This is the only real friction. Two file roles to consider:

**`CodeSnippetFile`** (user-uploaded inputs)
- Likely in the allowlist: `.csv`, `.json`, `.xlsx`, `.pdf`, `.png`, `.zip`.
- Not in the allowlist: `.txt`, `.yaml`, `.yml`, `.tsv`, `.parquet`, `.html`,
  `.md`, `.xml`, `.log`. Users couldn't upload these.

**`CodeExecFile`** (snippet outputs written via `codexec.write(...)`)
- The snippet may emit any extension. `codexec.write("report.html", …)` would
  fail at validation time.
- This is the bigger problem — outputs should be unconstrained.

### Three options

#### Option A — `ZFileField` for inputs only

Keep `models.FileField` for `CodeExecFile.file` (outputs unconstrained).
Switch only `CodeSnippetFile.file` to `ZFileField`.

- **Pro**: Tightens UI uploads, leaves outputs unconstrained.
- **Con**: Asymmetric — two field types in the same feature.

#### Option B — `ZFileField` for both, accept the extension limit

Use `ZFileField` for both. Snippet outputs must use one of the allowed
extensions. Document this in the codexec helper docs.

- **Pro**: Symmetric, no extra class to maintain.
- **Con**: Restricts what snippets can write — users may need to rename
  outputs (`.html` → `.csv` is awkward).

#### Option C — `ZFileField` for both, with a thin subclass for codexec

Add a small subclass that inherits from `ZFileField` but overrides the
validators to be empty:

```python
# in apps/code_execution/models.py
from zango.core.storage_utils import ZFileField

class _CodexecFileField(ZFileField):
    """ZFileField with no extension allowlist — snippet outputs need any ext."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # ZFileField hard-codes [validate_file_extension] in its super() call,
        # so we drop it after init.
        self.validators = [v for v in self.validators if v.__name__ != "validate_file_extension"]
```

Use `_CodexecFileField` for both `CodeSnippetFile.file` and `CodeExecFile.file`.

- **Pro**: Consistent field type. No surprise rejections on outputs. Get all
  the `RandomUniqueFileName` tenant scoping + private ACL for free.
- **Con**: One extra small class.

**Recommended: Option C.**

### Migration plan

Regardless of option chosen:

```python
# models.py — replace
class CodeSnippetFile(FullAuditMixin):
    file = models.FileField(upload_to=_snippet_file_upload_to, max_length=512)
# with (Option C):
class CodeSnippetFile(FullAuditMixin):
    file = _CodexecFileField(max_length=512)

class CodeExecFile(FullAuditMixin):
    file = models.FileField(upload_to=_exec_file_upload_to, max_length=512)
# with (Option C):
class CodeExecFile(FullAuditMixin):
    file = _CodexecFileField(max_length=512)
```

Then remove the `_snippet_file_upload_to` and `_exec_file_upload_to` helpers
— no longer used.

### What the generated migration looks like

```bash
python manage.py makemigrations code_execution
```

Will produce a single `AlterField` migration per affected column:

```python
operations = [
    migrations.AlterField(
        model_name='codesnippetfile',
        name='file',
        field=models.FileField(  # Django records as FileField since ZFileField is a subclass
            max_length=512,
            upload_to=...,
            validators=[zango.core.storage_utils.validate_file_extension],
        ),
    ),
    migrations.AlterField(
        model_name='codeexecfile',
        name='file',
        field=models.FileField(...),
    ),
]
```

- **No data migration required**: Django stores the path string in the DB. The
  field-class change doesn't touch existing rows.
- **Old files keep their old paths**: `codexec/snippets/<id>/<uuid>` paths
  continue to resolve fine because the storage backend serves whatever string
  is in the DB. We just stop generating new files at those paths.
- **New files go to the new layout**: `<tenant>/CodeSnippetFile/<uuid>.<ext>`
  and `<tenant>/CodeExecFile/<uuid>.<ext>`.

### Code points that need adjusting

Three places besides the model fields:

1. **`models.py`** — drop the `_snippet_file_upload_to` and
   `_exec_file_upload_to` helpers. Import `ZFileField` (and optionally define
   `_CodexecFileField`).

2. **`CodeSnippetRunView.post` (in `views.py`)** — the snapshot-on-run logic
   currently does:

   ```python
   CodeExecFile.objects.create(
       execution=execution,
       kind=FileKind.INPUT,
       name=snip_file.name,
       file=snip_file.file.name,        # ← shares the storage path string
       source_snippet_file=snip_file,
       ...
   )
   ```

   This still works. `ZFileField` records what we set on `file`; we're not
   triggering a new upload, just pointing the new row at the existing blob.
   No code change needed here.

3. **`codexec.py` `_store_output`** — currently:

   ```python
   obj.file.save(name, ContentFile(payload), save=True)
   ```

   This still works. `FileField.save` (which `ZFileField` inherits) routes
   through the upload_to callable. With `ZFileField` that's
   `RandomUniqueFileName`, producing the new layout.

### Storage layout, before and after

| Before | After |
|---|---|
| `codexec/snippets/<snippet_uuid>/<file_uuid>` | `<tenant>/CodeSnippetFile/<file_uuid>.<ext>` |
| `codexec/runs/<exec_uuid>/input/<file_uuid>` | `<tenant>/CodeExecFile/<file_uuid>.<ext>` |
| `codexec/runs/<exec_uuid>/output/<file_uuid>` | `<tenant>/CodeExecFile/<file_uuid>.<ext>` |

Note we lose the "all files for this run live under one prefix" grouping.
Some implications:

- **Listing files by execution**: today you could do an S3 `ListObjectsV2`
  with prefix `codexec/runs/<exec_id>/` and see only that run's files. After
  the switch, you'd have to query the DB instead. In practice we always query
  the DB anyway (via the `CodeExecFile` FK), so this is fine.
- **Bulk delete on GC**: 90-day retention GC needs to iterate the DB rows and
  delete each blob individually rather than doing a single prefix delete.
  Marginally slower; not a real problem for our scale.

### Filename preservation

Unchanged. We continue to store the user-facing name on `CodeSnippetFile.name`
/ `CodeExecFile.name`. The download serializer's `_signed_download_url`
generates S3 presigned URLs with `ResponseContentDisposition` populated from
that DB column. The storage path on disk is the UUID-with-extension produced
by `RandomUniqueFileName` — never seen by the user.

### Test plan

- Apply migration to one tenant.
- Upload a `.csv` snippet file → should succeed.
- Upload a `.txt` snippet file → succeeds if Option C, fails with extension
  validation if Option A/B.
- Run a snippet that does `codexec.write("out.html", b"hi")` → succeeds with
  Option C, fails with Option A/B.
- Verify downloads still come back with the original filename
  (`Content-Disposition: attachment; filename="out.html"`).
- Verify the snapshot-on-run still works — an exec input file's storage path
  equals the snippet file's storage path; bytes shared.
- Verify the old paths (`codexec/snippets/…`) still resolve for rows created
  before the migration.

---

## 2 · Block writes to `settings.*`

### Goal

Reading any `django.conf.settings.X` from a snippet stays allowed.
Modifying any `django.conf.settings.X` from a snippet must be rejected at
save / pickup time.

### Current state

The AST validator already blocks two specific attribute reads:

```python
BANNED_ATTR_PATHS = {
    ...
    ("settings", "SECRET_KEY"),
    ("settings", "DATABASES"),
    ...
}
```

These prevent `print(settings.SECRET_KEY)` etc. — fine to keep.

What's NOT blocked today: `settings.TIME_ZONE = "UTC"`,
`settings.DEBUG = True`, etc.

### What changes

`visit_Assign` and `visit_AugAssign` in `validator.py` need one extra check
that fires when the assignment target's resolved chain starts with `settings`
(or matches `django.conf.settings.…`).

### Drop-in code

```python
# inside visit_Assign, after the existing tenant-switch check:
elif chain[0] == "settings" or chain[:3] == ("django", "conf", "settings"):
    self._add(
        node.lineno,
        node.col_offset,
        "DENY_SETTINGS_WRITE",
        f"Modifying '{'.'.join(chain)}' is not allowed; settings are read-only.",
    )

# same idea inside visit_AugAssign for `settings.X += 1` etc.
```

The `chain[:3] == ("django", "conf", "settings")` covers the
`import django.conf` path where someone does
`django.conf.settings.TIME_ZONE = "UTC"`.

The `chain[0] == "settings"` covers the much more common path:

```python
from django.conf import settings
settings.TIME_ZONE = "UTC"        # caught — chain = ("settings", "TIME_ZONE")
```

This works because `visit_ImportFrom` already records the alias:

```python
if alias.name in {"os", "shutil", "django", "settings", "connection"}:
    self.alias_to_module[local] = alias.name
```

So `from django.conf import settings as cfg` is also handled — `cfg.X = Y`
becomes `("cfg", "X")` → resolved via the alias map → `("settings", "X")` →
matched.

### Reflection bypasses — already covered

We don't need new checks for these — they're already blocked by existing
logic:

| Bypass attempt | Already blocked by |
|---|---|
| `setattr(settings, "X", value)` | `setattr` in `BANNED_NAMES` → `DENY_NAME` |
| `delattr(settings, "X")` | `delattr` in `BANNED_NAMES` → `DENY_NAME` |
| `settings.__dict__["X"] = value` | `__dict__` in `BANNED_DUNDERS` → `DENY_DUNDER` |
| `vars(settings)["X"] = value` | `vars` in `BANNED_NAMES` → `DENY_NAME` |
| `settings.__class__.X = value` | `__class__` in `BANNED_DUNDERS` → `DENY_DUNDER` |
| `getattr(settings, "_wrapped").X = …` | The leading `_wrapped` dunder access isn't blocked — Django's Settings proxy hides settings on `_wrapped`. **Not currently caught**. See note below. |

### One reflection gap (worth noting)

Django's `settings` is a `LazySettings` wrapper that proxies attribute access
to an inner `Settings` instance stored on `settings._wrapped`. So a
determined attacker could in theory do:

```python
settings._wrapped.TIME_ZONE = "UTC"
```

The chain is `("settings", "_wrapped", "TIME_ZONE")`. My proposed check
`chain[0] == "settings"` does catch this — the chain's first element is
`settings` regardless of what's after it. So the prefix check is sufficient.

### Frontend behavior

No frontend change needed. The validator returns violations with code
`DENY_SETTINGS_WRITE` and the editor's existing violations panel renders them
the same as any other deny-list hit. Save / Save & Run are blocked until the
violation is resolved.

### Test cases

| Snippet | Expected |
|---|---|
| `print(settings.TIME_ZONE)` | ALLOW |
| `tz = settings.TIME_ZONE` | ALLOW |
| `settings.TIME_ZONE = "UTC"` | BLOCK · DENY_SETTINGS_WRITE |
| `settings.NEW_FLAG = True` | BLOCK · DENY_SETTINGS_WRITE |
| `settings.X += 1` | BLOCK · DENY_SETTINGS_WRITE |
| `from django.conf import settings as cfg; cfg.X = 1` | BLOCK · DENY_SETTINGS_WRITE |
| `import django.conf; django.conf.settings.X = 1` | BLOCK · DENY_SETTINGS_WRITE |
| `settings._wrapped.X = 1` | BLOCK · DENY_SETTINGS_WRITE |
| `setattr(settings, "X", 1)` | BLOCK · DENY_NAME (existing) |
| `settings.__dict__["X"] = 1` | BLOCK · DENY_DUNDER (existing) |

### Scope

- ~15 lines of code in `validator.py`.
- No migration needed.
- No frontend change.
- Add a smoke test exercising the table above.
