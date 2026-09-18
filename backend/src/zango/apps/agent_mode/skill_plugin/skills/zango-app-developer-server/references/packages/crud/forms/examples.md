# Zango CRUD Forms — Examples

> Worked form examples, best practices and troubleshooting. Start at [core.md](core.md).

## Complete Examples

### Example 1: Patient Form with Validation

```python
from django import forms
from ...packages.crud.forms import BaseForm
from ...packages.crud.form_fields import ModelField
from .models import Patient

class PatientForm(BaseForm):
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
        placeholder="10-digit number",
        required=True,
        required_msg="Phone is required"
    )
    date_of_birth = forms.DateField(
        label="Date of Birth",
        required=True
    )

    def __init__(self, *args, **kwargs):
        super(PatientForm, self).__init__(*args, **kwargs)
        instance = kwargs.get('instance')
        self.is_edit = True if instance else False

        if self.is_edit:
            self.Meta.title = "Update Patient"
        else:
            self.Meta.title = "Add Patient"

    def clean_email(self):
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

        if not self.is_edit:
            instance.save()
            instance.code = f"PAT-{instance.id:06d}"

        if commit:
            instance.save()
        return instance

    class Meta:
        model = Patient
        title = "Add Patient"
        layout = "drawer-two-third"
        order = [
            ["name"],
            ["email", "phone"],
            ["date_of_birth"]
        ]
```

### Example 2: Form with CustomSchemaField

```python
from ...packages.crud.forms import BaseSimpleForm
from ...packages.crud.form_fields import CustomSchemaField

class DocumentSignersForm(BaseSimpleForm):
    signers = CustomSchemaField(
        required=True,
        schema={
            "type": "array",
            "title": "Document Signers",
            "minItems": 1,
            "items": {
                "type": "object",
                "required": ["name", "email", "routing_order"],
                "properties": {
                    "name": {
                        "type": "string",
                        "title": "Signer Name",
                        "minLength": 2
                    },
                    "email": {
                        "type": "string",
                        "title": "Email Address",
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
                        "description": "Optional role of the signer"
                    }
                }
            }
        },
        ui_schema={
            "ui:options": {
                "orderable": True,
                "addable": True,
                "removable": True
            },
            "items": {
                "routing_order": {
                    "ui:widget": "updown"
                }
            }
        }
    )

    def __init__(self, *args, **kwargs):
        super(DocumentSignersForm, self).__init__(*args, **kwargs)
        self.Meta.title = "Configure Document Signers"

    def save(self):
        object_instance = self.initial.get("object_instance")
        object_instance.signers_data = self.cleaned_data.get('signers')
        object_instance.save()
        return object_instance

    class Meta:
        title = "Configure Signers"
        layout = "drawer-two-third"
        order = [["signers"]]
```

### Example 3: Workflow Transition Form

```python
from django import forms
from ...packages.crud.forms import BaseSimpleForm

class RejectionForm(BaseSimpleForm):
    rejection_reason = forms.CharField(
        label="Rejection Reason",
        required=True
    )

    def __init__(self, *args, **kwargs):
        super(RejectionForm, self).__init__(*args, **kwargs)
        self.Meta.title = "Reject Record"

        # Use textarea widget
        self.declared_fields['rejection_reason'].extra_ui_schema = {
            "ui:widget": "TextareaFieldWidget",
            "ui:options": {"rows": 5}
        }

    def save(self):
        object_instance = self.initial.get("object_instance")
        object_instance.rejection_reason = self.cleaned_data.get('rejection_reason')
        object_instance.save()
        return object_instance

    class Meta:
        title = "Reject Record"
        layout = "drawer-half"
        order = [["rejection_reason"]]
        success_message = "Record rejected successfully"
```

---

## Best Practices

1. **Always inherit from `BaseForm` or `BaseSimpleForm`**: Never use `forms.ModelForm` directly
2. **Set `is_edit` in `__init__`**: Used for differentiating create vs update
3. **Update title dynamically**: Show "Add" vs "Update" based on mode
4. **Generate codes after save**: Save first to get ID, then update code
5. **Validate uniqueness**: Exclude current instance in edit mode
6. **Use meaningful placeholders**: Help users understand what to enter
7. **Specify `required_msg`**: Provide clear error messages
8. **Use `CustomSchemaField` for complex inputs**: Arrays, nested objects, multi-select
9. **Never write `cleaned_data = super().clean()`**: `BaseForm.clean()` returns `None`.
   Call `super().clean()`, then read `self.cleaned_data`.
9. **Return instance from save**: Always return the saved instance
10. **Validate in `clean_*` methods**: Not in `save` method

---

## Troubleshooting

### Form Not Saving

**Problem**: `save()` method not returning instance

**Solution**:
```python
def save(self, commit=True):
    instance = super(MyForm, self).save(commit=False)
    # Custom logic
    if commit:
        instance.save()
    return instance  # Don't forget this!
```

### Validation Error Not Showing

**Problem**: Validation in `save()` method instead of `clean_*()`

**Solution**: Move validation to `clean_*` methods

### Edit Mode Not Working

**Problem**: Not setting `is_edit` flag

**Solution**:
```python
def __init__(self, *args, **kwargs):
    super(MyForm, self).__init__(*args, **kwargs)
    instance = kwargs.get('instance')
    self.is_edit = True if instance else False
```

### CustomSchemaField Not Rendering

**Problem**: Invalid JSON schema or UI schema

**Solution**: Validate schema structure, ensure proper rjsf format

### Cross-field validation never runs / values save as blank

**Problem**: `cleaned_data = super().clean()` in a `clean()` override.
`BaseForm.clean()` has no `return`, so it hands back `None`. Every subsequent
`cleaned_data.get(...)` is `None` (or raises `AttributeError`), the validation
silently does nothing, and the record saves without the values you expected.

**Solution**: call `super().clean()` for its side effects and read
`self.cleaned_data`:

```python
def clean(self):
    super().clean()
    cleaned_data = self.cleaned_data
    ...
    return cleaned_data
```

### `KeyError` on a CustomSchemaField name (form 500s, drawer shows "Server Error")

**Problem**: `self.declared_fields["<name>"]` in `__init__`. A
`CustomSchemaField` is stored in `self.custom_schema_fields`, not
`declared_fields`, so the lookup raises `KeyError` and `initialize_form`
returns 500.

**Solution**: use `self.custom_schema_fields["<name>"].schema = {...}`. See the
note in the CustomSchemaField section above.

### Form Title Not Updating

**Problem**: Setting title on wrong object

**Solution**:
```python
def __init__(self, *args, **kwargs):
    super(MyForm, self).__init__(*args, **kwargs)
    self.Meta.title = "New Title"  # Update Meta.title
```
