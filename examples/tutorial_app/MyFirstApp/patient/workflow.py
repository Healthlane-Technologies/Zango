from ..packages.workflow.base.engine import WorkflowBase
from .forms import PatientDeactivateForm
from .models import Patient


class PatientWorkflow(WorkflowBase):
    status_transitions = [
        {
            "name": "inactivate",
            "display_name": "Deactivate",
            "description": "Deactivate the Patient",
            "from": "active",
            "to": "inactive",
            "form": PatientDeactivateForm,
        },
        {
            "name": "activate",
            "from": "inactive",
            "to": "active",
            "display_name": "Activate",
            "description": "Activate the Patient",
            "confirmation_message": "Are you sure you want to activate the patient?",
        },
    ]

    def inactivate_condition(self, request, object_instance, **kwargs):
        """
        Checks if the conditions are met to execute the 'inactivate' status transition.

        Parameters:
            request (HttpRequest): The HTTP request object.
            object_instance (Patient): The instance of the Patient model.
            **kwargs: Additional keyword arguments.

        Returns:
            bool: True if the conditions are met, False otherwise.
        """
        # Implement condition logic here
        return True

    def inactivate_done(self, request, object_instance, transaction_obj):
        """
        Executes processing logic for the 'inactivate' status transition.

        Parameters:
            request (HttpRequest): The HTTP request object.
            object_instance (Patient): The instance of the Patient model.
            transaction_obj (TransactionModel): The associated transaction model object.
        """
        # Implement processing logic here
        pass

    def activate_condition(self, request, object_instance, **kwargs):
        """
        Checks if the conditions are met to execute the 'activate' status transition.

        Parameters:
            request (HttpRequest): The HTTP request object.
            object_instance (Patient): The instance of the Patient model.
            **kwargs: Additional keyword arguments.

        Returns:
            bool: True if the conditions are met, False otherwise.
        """
        # Implement condition logic here
        return True

    def activate_done(self, request, object_instance, transaction_obj):
        """
        Executes processing logic for the 'activate' status transition.

        Parameters:
            request (HttpRequest): The HTTP request object.
            object_instance (Patient): The instance of the Patient model.
            transaction_obj (TransactionModel): The associated transaction model object.
        """
        # Implement processing logic here
        pass

    class Meta:
        statuses = {
            "active": {
                "color": "#00857C",
                "label": "Active",
            },
            "inactive": {
                "color": "#FF0000",
                "label": "Inactive",
            },
        }
        model = Patient
        on_create_status = "active"
