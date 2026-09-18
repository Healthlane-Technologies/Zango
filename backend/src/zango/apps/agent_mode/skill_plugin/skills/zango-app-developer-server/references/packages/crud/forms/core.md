# Zango CRUD Forms — Core

> Splits of the CRUD forms reference: **core.md** (this file), [examples.md](examples.md) (complete examples, best practices, troubleshooting).

## Essential Imports

```python
from django import forms
from ...packages.crud.forms import BaseForm, BaseSimpleForm
from ...packages.crud.form_fields import ModelField, CustomSchemaField
from .models import MyModel
```

---

## Form Types

### BaseForm - Model Forms

For forms that create/edit model instances.

```python
class MyModelForm(BaseForm):
    name = ModelField(placeholder="Enter name", required=True)
    email = ModelField(placeholder="Email address", required=False)

    def __init__(self, *args, **kwargs):
        super(MyModelForm, self).__init__(*args, **kwargs)
        instance = kwargs.get('instance')
        self.is_edit = True if instance else False

        if self.is_edit:
            self.Meta.title = "Update Record"
        else:
            self.Meta.title = "Add Record"

    def save(self, commit=True):
        instance = super(MyModelForm, self).save(commit=False)
        # Custom save logic
        if commit:
            instance.save()
        return instance

    class Meta:
        model = MyModel
        title = "Add Record"
        layout = "drawer-half"
        order = [["name"], ["email"]]
```

### BaseSimpleForm - Non-Model Forms

For forms not tied to a model (workflow transitions, custom actions).

```python
class ApprovalForm(BaseSimpleForm):
    approval_notes = forms.CharField(label="Approval Notes", required=True)

    def __init__(self, *args, **kwargs):
        super(ApprovalForm, self).__init__(*args, **kwargs)
        self.Meta.title = "Approve Record"

    def save(self):
        object_instance = self.initial.get("object_instance")
        object_instance.approval_notes = self.cleaned_data.get('approval_notes')
        object_instance.save()
        return object_instance

    class Meta:
        title = "Approve Record"
        layout = "drawer-half"
        order = [["approval_notes"]]
```

**When to use BaseSimpleForm**:
- Workflow transition forms
- Custom action forms (approve, reject, etc.)
- Forms that don't create/update model instances directly
- Forms that need to operate on existing objects

---

## Field Types

### ModelField - Standard Form Field

The primary field type for form inputs with extensive configuration options.

```python
field_name = ModelField(
    label="Field Label",              # Field label (optional)
    placeholder="Enter value",         # Placeholder text (optional)
    required=False,                    # Is field required (default: False)
    required_msg="",                   # Custom required error message
    pattern="",                        # Regex pattern for validation
    pattern_msg="",                    # Custom pattern error message
    readonly=False,                    # Make field read-only
    hidden=False,                      # Hide field (still submitted)
    initial=None,                      # Default/initial value
    sync_enabled=False,                # Enable field syncing
    prefix=None,                       # Prefix text/icon
    suffix=None,                       # Suffix text/icon
    description="",                    # Help text below field
    tooltip="",                        # Tooltip on hover
    autocomplete={},                   # Autocomplete configuration
    extra_schema={},                   # Additional JSON schema
    extra_ui_schema={},                # Additional UI schema (rjsf)
)
```

**Parameters Explained**:

- **label**: Field label displayed above input
- **placeholder**: Placeholder text in input field
- **required**: Whether field is required (shows *)
- **required_msg**: Custom error message when field is empty
- **pattern**: Regex pattern for validation (e.g., `r'^\d+$'` for numbers only)
- **pattern_msg**: Error message when pattern doesn't match
- **readonly**: Makes field read-only (grayed out, can't edit)
- **hidden**: Hides field but still includes in form submission
- **initial**: Default value (can be callable function)
- **sync_enabled**: Enable real-time field syncing
- **prefix**: Text/icon before input (e.g., "$" for currency)
- **suffix**: Text/icon after input (e.g., "kg" for weight)
- **description**: Help text shown below field
- **tooltip**: Tooltip text on hover
- **autocomplete**: Autocomplete configuration object
- **extra_schema**: Additional JSON schema properties
- **extra_ui_schema**: Additional UI schema properties for rjsf

### ModelField Examples

**Basic Text Field**:
```python
name = ModelField(
    label="Patient Name",
    placeholder="Enter full name",
    required=True,
    required_msg="Patient name is required"
)
```

**Field with Pattern Validation**:
```python
phone = ModelField(
    label="Phone Number",
    placeholder="Enter 10-digit phone",
    required=True,
    pattern=r'^\d{10}$',
    pattern_msg="Phone must be exactly 10 digits"
)
```

**Field with Prefix/Suffix**:
```python
price = ModelField(
    label="Price",
    placeholder="Enter amount",
    prefix="$",
    suffix="USD",
    required=True
)

weight = ModelField(
    label="Weight",
    placeholder="Enter weight",
    suffix="kg",
    description="Patient's weight in kilograms"
)
```

**Field with Tooltip and Description**:
```python
diagnosis = ModelField(
    label="Diagnosis",
    placeholder="Enter diagnosis",
    description="Primary diagnosis for this visit",
    tooltip="This will be shown on patient records",
    required=True
)
```

**Read-Only Field**:
```python
code = ModelField(
    label="Patient Code",
    readonly=True,
    description="Auto-generated patient identifier"
)
```

**Field with Initial Value**:
```python
status = ModelField(
    label="Status",
    initial="pending",
    description="Current status"
)

# Callable initial value
created_date = ModelField(
    label="Created Date",
    initial=lambda: datetime.now().date(),
    readonly=True
)
```

**Field with Custom UI Widget**:
```python
notes = ModelField(
    label="Notes",
    placeholder="Enter notes",
    extra_ui_schema={
        "ui:widget": "TextareaFieldWidget",
        "ui:options": {"rows": 5}
    }
)
```

**Field with Autocomplete**:
```python
currency = ModelField(
    label="Currency",
    placeholder="Select currency",
    autocomplete={"enabled": True, "keys": 3}
)
```

**Autocomplete Configuration**:
- **enabled**: Set to `True` to enable autocomplete
- **keys**: Minimum number of characters before autocomplete triggers

**Implementing Autocomplete Method**:

When you add `autocomplete={"enabled": True}` to a field, you **MUST** implement a method in your form class:

```python
def get_{fieldname}_autocomplete_options(self, request, search_query, form_data):
    """
    Return autocomplete options for the field.

    Args:
        request: HTTP request object
        search_query: User's search input (string)
        form_data: Current form data (dict)

    Returns:
        List of dicts with 'value' and 'label' keys
    """
    return [
        {"value": "option1", "label": "Option 1 Label"},
        {"value": "option2", "label": "Option 2 Label"},
    ]
```

**Complete Autocomplete Example**:
```python
from ...packages.crud.forms import BaseForm, ModelField

class ProjectForm(BaseForm):
    currency = ModelField(
        label="Currency",
        placeholder="Start typing currency code",
        required=True,
        autocomplete={"enabled": True, "keys": 3}
    )

    def get_currency_autocomplete_options(self, request, search_query, form_data):
        """Return currency options filtered by search query"""
        currencies = [
            {"value": "USD", "label": "USD - US Dollar"},
            {"value": "EUR", "label": "EUR - Euro"},
            {"value": "GBP", "label": "GBP - British Pound"},
            {"value": "INR", "label": "INR - Indian Rupee"},
            {"value": "JPY", "label": "JPY - Japanese Yen"},
        ]

        # Filter based on search query
        if search_query:
            search_query = search_query.upper()
            currencies = [
                c for c in currencies
                if search_query in c["value"] or search_query in c["label"]
            ]

        return currencies

    class Meta:
        model = Project
        title = "Project Form"
        fields = ["currency"]
```

**Autocomplete with Database Query**:
```python
def get_country_autocomplete_options(self, request, search_query, form_data):
    """Return country options from database"""
    from ..masters.geography.models import Country

    countries = Country.objects.filter(is_active=True)

    if search_query:
        countries = countries.filter(name__icontains=search_query)

    countries = countries[:10]  # Limit results

    return [
        {"value": str(country.id), "label": country.name}
        for country in countries
    ]
```

**Method Naming Convention**:
- For field named `currency`: method must be `get_currency_autocomplete_options`
- For field named `country_code`: method must be `get_country_code_autocomplete_options`
- Pattern: `get_{field_name}_autocomplete_options`

### CustomSchemaField - Advanced JSON Schema Fields

For complex fields using React JSON Schema Form (rjsf). Allows full JSON schema and UI schema control.

```python
field_name = CustomSchemaField(
    required=False,
    schema={},      # JSON schema definition
    ui_schema={},   # UI schema for rjsf
)
```

**Use Cases**:
- Array fields (multiple values)
- Nested object fields
- Complex custom widgets
- Dynamic form fields
- Multi-select with custom rendering

> **A `CustomSchemaField` is NOT in `self.declared_fields`.** `BaseForm.__init__`
> sorts each field by class: `ModelField` goes into `self.declared_fields`,
> while `CustomSchemaField` goes into **`self.custom_schema_fields`**. So this,
> in `__init__` after `super()`, raises `KeyError` and 500s the whole form —
> `initialize_form` fails, and the Add/Edit drawer shows only "Server Error":
>
> ```python
> # WRONG -- KeyError: 'lines'
> self.declared_fields["lines"].schema = {...}
> ```
>
> Build the schema where the field lives instead:
>
> ```python
> # Right -- same dict BaseForm put it in
> self.custom_schema_fields["lines"].schema = {...}
> self.custom_schema_fields["lines"].ui_schema = {...}
> ```
>
> `self.declared_fields[...]` remains correct for `ModelField` attributes such
> as `extra_ui_schema` — that is what the examples further down this file show.
> The rule is per field class, not per attribute.
>
> This is a build-time-clean, runtime-fatal mistake: the module imports fine and
> the list page renders, so it is only caught by **opening the Add form**. Do
> that for every form you write that uses a `CustomSchemaField`.

> **Every non-null model field the user must supply needs a form field.** A
> required `ZForeignKey` (e.g. `retailer` on a sales order) that you omit from
> the form cannot be filled in, so the save fails validation with no usable
> message. Cross-check the form's fields against the model's required fields
> before moving on — parent FKs are the ones most often forgotten, especially
> when the form is reached from a parent's detail page.

### CustomSchemaField Examples

**Array of Objects** (e.g., multiple signers):

```python
signers = CustomSchemaField(
    required=True,
    schema={
        "type": "array",
        "title": "Signers",
        "minItems": 1,
        "items": {
            "type": "object",
            "required": ["name", "email", "routing_order"],
            "properties": {
                "name": {
                    "type": "string",
                    "title": "Name",
                    "minLength": 2
                },
                "email": {
                    "type": "string",
                    "title": "Email",
                    "format": "email"
                },
                "routing_order": {
                    "type": "integer",
                    "title": "Signing Order",
                    "minimum": 1,
                    "default": 1
                },
                "role": {
                    "type": "string",
                    "title": "Role/Title",
                    "description": "Optional role or title"
                }
            }
        }
    },
    ui_schema={
        "ui:options": {
            "orderable": True,      # Allow reordering
            "addable": True,        # Show add button
            "removable": True       # Show remove button
        }
    }
)
```

**Multi-Select Field**:

```python
team_members = CustomSchemaField(
    required=False,
    schema={
        "type": "array",
        "title": "Team Members",
        "items": {
            "type": "string",
            "enum": ["John", "Jane", "Bob", "Alice"]
        },
        "uniqueItems": True
    },
    ui_schema={
        "ui:widget": "CheckboxesWidget"
    }
)
```

**Nested Object**:

```python
address = CustomSchemaField(
    required=True,
    schema={
        "type": "object",
        "title": "Address",
        "required": ["street", "city", "zip"],
        "properties": {
            "street": {
                "type": "string",
                "title": "Street Address"
            },
            "city": {
                "type": "string",
                "title": "City"
            },
            "state": {
                "type": "string",
                "title": "State"
            },
            "zip": {
                "type": "string",
                "title": "ZIP Code",
                "pattern": "^\\d{5}$"
            }
        }
    },
    ui_schema={
        "street": {"ui:widget": "TextareaFieldWidget"},
        "zip": {"ui:placeholder": "12345"}
    }
)
```

---

## Form Structure

### BaseForm Complete Structure

```python
from django import forms
from ...packages.crud.forms import BaseForm
from ...packages.crud.form_fields import ModelField, CustomSchemaField
from .models import Patient

class PatientForm(BaseForm):
    # Define form fields
    name = ModelField(
        label="Patient Name",
        placeholder="Enter full name",
        required=True,
        required_msg="Name is required"
    )
    email = ModelField(
        label="Email",
        placeholder="email@example.com",
        required=False
    )
    phone = ModelField(
        label="Phone",
        placeholder="10-digit phone number",
        required=True,
        pattern=r'^\d{10}$',
        pattern_msg="Phone must be 10 digits"
    )
    date_of_birth = forms.DateField(
        label="Date of Birth",
        required=True
    )

    def __init__(self, *args, **kwargs):
        super(PatientForm, self).__init__(*args, **kwargs)
        instance = kwargs.get('instance')
        self.is_edit = True if instance else False

        # Update title based on mode
        if self.is_edit:
            self.Meta.title = "Update Patient"
        else:
            self.Meta.title = "Add Patient"

    def clean_email(self):
        """Validate email uniqueness"""
        email = self.cleaned_data.get('email')
        if email:
            existing = Patient.objects.filter(email=email)
            if self.is_edit:
                existing = existing.exclude(id=self.instance.id)
            if existing.exists():
                raise forms.ValidationError("Email already exists")
        return email

    def save(self, commit=True):
        instance = super(PatientForm, self).save(commit=False)

        # Generate code on creation
        if not self.is_edit:
            instance.save()  # Save to get ID
            instance.code = f"PAT-{instance.id:06d}"

        if commit:
            instance.save()
        return instance

    class Meta:
        model = Patient
        title = "Add Patient"
        layout = "drawer-half"
        order = [
            ["name"],
            ["email", "phone"],
            ["date_of_birth"]
        ]
```

### BaseSimpleForm Complete Structure

```python
from django import forms
from ...packages.crud.forms import BaseSimpleForm
from ...packages.crud.form_fields import ModelField

class ApprovalForm(BaseSimpleForm):
    approval_notes = forms.CharField(
        label="Approval Notes",
        required=True
    )
    approved_by = forms.CharField(
        label="Approver Name",
        required=True
    )

    def __init__(self, *args, **kwargs):
        super(ApprovalForm, self).__init__(*args, **kwargs)
        self.Meta.title = "Approve Record"

        # Customize UI widget
        self.declared_fields['approval_notes'].extra_ui_schema = {
            "ui:widget": "TextareaFieldWidget",
            "ui:options": {"rows": 3}
        }

    def save(self):
        object_instance = self.initial.get("object_instance")
        object_instance.approval_notes = self.cleaned_data.get('approval_notes')
        object_instance.approved_by = self.cleaned_data.get('approved_by')
        object_instance.save()
        return object_instance

    class Meta:
        title = "Approve Record"
        layout = "drawer-half"
        order = [["approved_by"], ["approval_notes"]]
```

---

## Meta Class Options

### Required Options

```python
class Meta:
    model = MyModel          # REQUIRED for BaseForm
    title = "Form Title"     # REQUIRED: Form title
    layout = "drawer-half"   # REQUIRED: Form size
    order = [["field1"]]     # REQUIRED: Field layout
```

**Note**: For `BaseSimpleForm`, `model` is not required.

### Layout Options

The `layout` determines the form drawer size:

| Layout | Width | Use Case |
|--------|-------|----------|
| `"drawer-half"` | 50% | Simple forms with few fields |
| `"drawer-two-third"` | 66% | Medium complexity forms |
| `"drawer-full"` | 100% | Complex forms with many fields |

### Field Order

The `order` defines how fields are arranged:

```python
class Meta:
    order = [
        ["name"],                    # One field per row
        ["email", "phone"],          # Two fields in one row
        ["address"],                 # One field per row
        ["city", "state", "zip"]     # Three fields in one row
    ]
```

### Optional Meta Options

```python
class Meta:
    model = MyModel
    title = "Add Record"
    layout = "drawer-half"
    order = [["name"], ["email"]]

    # Optional
    unique_together = [("field1", "field2")]  # Unique constraint validation
    reload_on_success = True                   # Reload page after save (default: True)
    success_message = "Record saved!"          # Custom success message
```

**unique_together**: Validate unique combinations of fields (raises ValidationError if duplicate found, excluding current instance in edit mode).

**reload_on_success**: Whether to reload the page after successful form submission.

**success_message**: Custom message shown on successful save.

---

## Form Methods

### __init__ Method

Set up form state and customize based on add/edit mode.

```python
def __init__(self, *args, **kwargs):
    super(MyForm, self).__init__(*args, **kwargs)

    # Detect add vs edit mode
    instance = kwargs.get('instance')
    self.is_edit = True if instance else False

    # Update title
    if self.is_edit:
        self.Meta.title = "Update Record"
    else:
        self.Meta.title = "Add Record"

    # Customize fields based on mode
    if self.is_edit:
        self.fields['code'].widget.attrs['readonly'] = True
```

### save Method

Custom save logic for the form.

```python
def save(self, commit=True):
    instance = super(MyForm, self).save(commit=False)

    # Custom logic before save
    if not self.is_edit:
        # Generate code on creation
        instance.save()  # Save to get ID
        instance.code = f"CODE-{instance.id:04d}"

    # Additional custom logic
    instance.processed = True

    if commit:
        instance.save()
    return instance
```

### clean Method

Cross-field validation.

> **`BaseForm.clean()` returns `None` — never assign from it.** Unlike Django's
> `Form.clean()`, which returns `self.cleaned_data`, `BaseForm.clean()` runs its
> `unique_together` checks and then falls off the end with no `return`. So the
> familiar Django idiom silently produces `None`:
>
> ```python
> # WRONG -- cleaned_data is None, every .get() below returns None,
> # cross-field validation never fires, and the form saves blank values.
> cleaned_data = super().clean()
> start = cleaned_data.get("start_date")     # AttributeError, or None
> ```
>
> Call it for its side effects, then read **`self.cleaned_data`**, which is
> always the authoritative dict:
>
> ```python
> # Right
> super().clean()
> cleaned_data = self.cleaned_data
> ```
>
> The same applies anywhere else you would normally use a `super()` return
> value from the form: `self.cleaned_data` is the source of truth. Note there
> is nothing to catch this — no exception is raised and validation simply does
> not happen, so the bug surfaces later as missing or unvalidated data.

```python
def clean(self):
    super().clean()              # side effects only -- returns None
    cleaned_data = self.cleaned_data

    start_date = cleaned_data.get('start_date')
    end_date = cleaned_data.get('end_date')

    if start_date and end_date and end_date < start_date:
        raise forms.ValidationError("End date must be after start date")

    return cleaned_data
```

### clean_<field> Methods

Field-specific validation.

```python
def clean_email(self):
    """Validate email uniqueness"""
    email = self.cleaned_data.get('email')
    if email:
        existing = MyModel.objects.filter(email=email)
        if self.is_edit:
            existing = existing.exclude(id=self.instance.id)
        if existing.exists():
            raise forms.ValidationError("Email already exists")
    return email

def clean_code(self):
    """Validate code format"""
    code = self.cleaned_data.get('code')
    if code and not code.startswith('PAT-'):
        raise forms.ValidationError("Code must start with PAT-")
    return code
```

---
