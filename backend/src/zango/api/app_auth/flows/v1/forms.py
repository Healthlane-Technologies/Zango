from allauth.headless.internal.restkit import inputs

from django import forms
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

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user")
        super().__init__(*args, **kwargs)

    def save(self):
        self.user.set_password(self.cleaned_data["new_password"])
        self.user.save()
        obj = OldPasswords.objects.create(user=self.user)
        obj.setPasswords(self.user.password)
        obj.save()


class PasswordSetForm(BaseSetPasswordForm, inputs.Input):
    pass
