import os
import uuid
from django.db import models, connection
from django.core.exceptions import ValidationError


def RandomUniqueFileName(instance, filename):
  try:
    path = connection.tenant.name + '/' + instance.__class__.__name__
    extension = filename.split('.')[-1]
    file_ = "%s.%s" %(uuid.uuid4(), extension)
    return os.path.join(path, file_)
  except:
    return


def validate_file_extension(value):
    ext = os.path.splitext(value.name)[-1]  # [0] returns path+filename
    valid_extensions = ['.pdf', '.doc', '.docx', '.jpg', '.jpeg', '.png', '.svg', '.xls', '.xlsx', '.mp3', '.wav', '.ppt', '.pptx', '.zip']
    if not ext.lower() in valid_extensions:
        raise ValidationError(u'The file type you are trying to upload is not supported.')