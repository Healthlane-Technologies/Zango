from django.db import models


class FullAuditMixin(models.Model):

    """
    An abstract base class model that provides audit fields
    to keep track of creation and modification timestamps
    and the users who carried out these actions.

    Attributes:
    - `created_at`: The timestamp when the object was first created.
    - `created_by`: The user who created the object.
                   This is non-editable and can be left blank.
    - `modified_at`: The timestamp of the last modification of the object.
    - `modified_by`: The user who last modified the object.
                    This is non-editable and can be left blank.
    """
    # TODO: make created_by and modified_by as fk to Users

    created_at = models.DateTimeField(
        auto_now_add=True
    )
    created_by = models.CharField(
        max_length=255, blank=True, editable=False
    )
    modified_at = models.DateTimeField(auto_now=True)
    modified_by = models.CharField(
        max_length=255, blank=True, editable=False
    )

    class Meta:
        abstract = True
