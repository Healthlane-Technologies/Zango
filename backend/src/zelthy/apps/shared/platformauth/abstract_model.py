import json

from django.db import models
from django.contrib.auth.models import AbstractBaseUser

# from django.xcontrib.postgres.fields import JSONField
from django.db.models import JSONField
from django.utils import timezone
from django.contrib.auth.models import User

from phonenumber_field.modelfields import PhoneNumberField


# from backend.core.storage_utils import S3PrivateFileField, RandomUniqueFileName
from zelthy.core.storage_utils import RandomUniqueFileName
from zelthy.core.model_mixins import FullAuditMixin
from phonenumber_field.modelfields import PhoneNumberField


class AbstractZelthyUserModel(AbstractBaseUser, FullAuditMixin):
    name = models.CharField("full name of user", max_length=75)
    email = models.EmailField("email address", null=True, blank=True)
    mobile = PhoneNumberField("mobile number", null=True, blank=True)
    is_active = models.BooleanField(
        "active",
        default=True,
        help_text=(
            "Designates whether this user should be treated as active. "
            "Unselect this instead of deleting accounts."
        ),
    )
    date_joined = models.DateTimeField("date joined", default=timezone.now)
    address_line_1 = models.CharField("address line 1", max_length=255, blank=True)
    address_line_2 = models.CharField("address line 2", max_length=255, blank=True)
    address_line_3 = models.CharField("address line 3", max_length=255, blank=True)
    city = models.CharField("city", max_length=100, blank=True)
    state = models.CharField("state", max_length=255, blank=True)
    pincode = models.CharField("pincode/zipcode", max_length=20, blank=True)
    country = models.CharField(
        verbose_name="country",
        max_length=200,
        null=True,
    )
    profile_pic = models.FileField(
        upload_to=RandomUniqueFileName,
        verbose_name="user profile pic",
        null=True,
        blank=True,
    )
    extra_data = JSONField(null=True)
    USERNAME_FIELD = "email"

    class Meta:
        abstract = True


class AbstractOldPasswords(models.Model):
    password = models.CharField(max_length=300)
    password_date = models.DateField(
        verbose_name="Password Change Date", auto_now_add=True
    )
    password_datetime = models.DateTimeField(
        verbose_name="Password Change DateTime",
        auto_now_add=True,
        null=True,
        blank=True,
    )

    def setPasswords(self, password):
        self.password = json.dumps(password)

    def getPasswords(self):
        return json.loads(self.password)

    class Meta:
        abstract = True
