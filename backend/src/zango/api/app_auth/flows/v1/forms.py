from allauth.headless.internal.restkit import inputs

from django import forms
from django.utils.translation import gettext_lazy as _

from zango.api.app_auth.profile.v1.utils import PasswordValidationMixin
from zango.apps.appauth.models import OldPasswords


class BaseSetPasswordForm(forms.Form, PasswordValidationMixin):
    new_password = forms.CharField(
        label=_("New password"),
        widget=forms.PasswordInput(
            attrs={
                "class": "form-control",
                "placeholder": "Enter your new password",
                "autocomplete": "new-password",
            }
        ),
        strip=False,
    )

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user")
        super().__init__(*args, **kwargs)

    def save(self):
        res = self.run_all_validations(self.user, self.cleaned_data["new_password"])
        if not res.get("validation"):
            raise forms.ValidationError(res.get("msg") or "Invalid password")
        self.user.set_password(self.cleaned_data["new_password"])
        self.user.save()
        obj = OldPasswords.objects.create(user=self.user)
        obj.setPasswords(self.user.password)
        obj.save()


class PasswordSetForm(BaseSetPasswordForm, inputs.Input):
    pass
