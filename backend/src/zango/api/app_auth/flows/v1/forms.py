from allauth.headless.internal.restkit import inputs

from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from zango.apps.appauth.models import OldPasswords


class BaseSetPasswordForm(forms.Form):
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
    confirm_password = forms.CharField(
        label=_("Confirm new password"),
        widget=forms.PasswordInput(
            attrs={
                "class": "form-control",
                "placeholder": "Confirm your new password",
                "autocomplete": "new-password",
            }
        ),
        strip=False,
    )

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user")
        super().__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = super().clean()
        new_password = cleaned_data.get("new_password")
        confirm_password = cleaned_data.get("confirm_password")

        if new_password and confirm_password:
            if new_password != confirm_password:
                raise ValidationError(
                    _("The two password fields didn't match."),
                    code="password_mismatch",
                )

    def save(self):
        self.user.set_password(self.cleaned_data["new_password"])
        self.user.save()
        obj = OldPasswords.objects.create(user=self.user)
        obj.setPasswords(self.user.password)
        obj.save()


class PasswordSetForm(BaseSetPasswordForm, inputs.Input):
    pass
