from ..packages.crud.base import BaseCrudView
from .forms import PatientForm
from .tables import PatientTable
from .workflow import PatientWorkflow


class PatientCrudView(BaseCrudView):
    page_title = "Patient Records"
    add_btn_title = "Add New Patient"
    table = PatientTable
    form = PatientForm
    workflow = PatientWorkflow

    def display_add_button_check(self, request):
        # Add your logic here
        return True
