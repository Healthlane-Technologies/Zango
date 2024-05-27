from ..packages.crud.base import BaseCrudView
from .tables import PatientTable
from .forms import PatientForm
from .workflow import PatientWorkflow
from .models import Patient

class PatientCrudView(BaseCrudView):
    page_title = "Patient Records"
    add_btn_title = "Add New Patient"
    table = PatientTable
    form = PatientForm
    workflow = PatientWorkflow

    def display_add_button_check(self, request):
        # Add your logic here
        return True