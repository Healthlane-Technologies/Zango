from typing import Any
from django.db import models
from zelthy3.backend.core.storage_utils import RandomUniqueFileName, validate_file_extension

class DataModelFileField(models.FileField):

    def __init__(self, verbose_name=None, upload_to=RandomUniqueFileName, name=None, storage=None, make_public = False, validators=[validate_file_extension], **kwargs):
        super(DataModelFileField, self).__init__(
                         verbose_name=verbose_name,
                         name=name,
                         upload_to=upload_to,
                         storage=storage,
                         validators=[validate_file_extension],
                         **kwargs
                         )
        if make_public is False:
          self.storage.default_acl = "private"

class DataModelForeignKey:
   
   def __init__(self, related_model, field_name):
      self.related_model = related_model
      self.field_name = field_name

class DataModelOneToOneField:
   def __init__(self, related_model, field_name):
      self.related_model = related_model
      self.field_name = field_name

class DataModelManyToManyField:
   def __init__(self, related_model, field_name):
      self.related_model = related_model
      self.field_name = field_name