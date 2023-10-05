import uuid
from django import forms
from ..plugins.crud.form_fields import ModelField, CustomField
from ..plugins.crud.forms import BaseForm
from .models import FHIRPatient


def get_uuid():
    return str(uuid.uuid4())


class FHIRPatientForm(BaseForm):

    identifier = ModelField(
                placeholder="Enter Identifier",
                required=True,
                required_msg="This field is required.",
                hidden=True,
                initial=get_uuid
                )
    family = ModelField(
                placeholder="Family Name",
                required=True,
                required_msg="Family Name is a mandatory field",
                pattern="^[a-zA-Z]*$",
                pattern_msg="Only Alphabets are allowed.",
            )
    given = ModelField(
                placeholder="Given Name",
                required=True,
                required_msg="Given Name is a mandatory field",
                pattern="^[a-zA-Z]*$",
                pattern_msg="Only Alphabets are allowed.",                
            )
    gender = ModelField(
                placeholder="Gender",
                required=True,
                required_msg="Gender is a mandatory field",
                initial='male'
            )
    birth_date = ModelField(
                placeholder="Date of Birth",
                required=False
                )
    city = ModelField(
                placeholder="City",
                required=True,
                required_msg="City is a mandatory field"
                )
    state = ModelField()
    country = ModelField()
    user_role = ModelField(
                placeholder="User Role",
                required=True,
                required_msg="User Role is a mandatory field"
            )

    class Meta:
        model = FHIRPatient
        