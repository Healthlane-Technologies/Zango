from ..packages.crud.table.base import ModelTable
from ..packages.crud.table.column import ModelCol
from .forms import PatientForm
from .models import Patient


class PatientTable(ModelTable):
    id = ModelCol(display_as="ID", sortable=True, searchable=True)
    name = ModelCol(display_as="Name", sortable=True, searchable=True)
    dob = ModelCol(display_as="Date of Birth", sortable=True, searchable=True)
    gender = ModelCol(display_as="Gender", sortable=True, searchable=True)
    address = ModelCol(display_as="Address", sortable=False, searchable=True)
    phone_number = ModelCol(display_as="Phone Number", sortable=False, searchable=True)
    email = ModelCol(display_as="Email", sortable=False, searchable=True)

    table_actions = []
    row_actions = [
        {
            "name": "Edit",
            "key": "edit",
            "description": "Edit Patient",
            "type": "form",
            "form": PatientForm,  # Specify the form to use for editing
            "roles": [
                "PatientSupportManager"
            ],  # Specify roles that can perform the action
        }
    ]

    class Meta:
        model = Patient
        fields = ["id", "name", "dob", "gender", "address", "phone_number", "email"]
        row_selector = {"enabled": False, "multi": False}
