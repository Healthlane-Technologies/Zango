from django import forms

from ..packages.crud.form_fields import ModelField
from ..packages.crud.forms import BaseForm, BaseSimpleForm
from .models import Patient


class PatientForm(BaseForm):
    name = ModelField(
        placeholder="Enter Name", required=True, required_msg="This field is required."
    )
    dob = ModelField(
        placeholder="Enter Date of Birth",
        required=True,
        required_msg="This field is required.",
    )
    gender = ModelField(
        placeholder="Select Gender",
        required=True,
        required_msg="This field is required.",
    )
    address = ModelField(placeholder="Enter Address", required=False)
    phone_number = ModelField(placeholder="Enter Phone Number", required=False)
    email = ModelField(placeholder="Enter Email", required=False)

    class Meta:
        title = "Patient"
        model = Patient


class PatientDeactivateForm(BaseSimpleForm):
    reason = forms.CharField(label="Reason", max_length=100, required=True)
    date = forms.DateField(label="Date", required=True)
    file = forms.FileField(label="File", required=False)

    class Meta:
        title = "Deactivate Patient"

        order = ["date", "reason", "file"]

    def save(self):
        # form processing
        pass
