import os
import uuid
from django.db import models, connection
from django.core.exceptions import ValidationError
from uuid import uuid4


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
  
def upload_to(instance, filename):
    class_name = str(type(instance))
    folder = class_name.split('.')[-1].split("'")[0]
    tenant = class_name.split('.')[3]
    extension = filename.split(".")[-1]
    return f"{tenant}/{folder}/{uuid4()}.{extension}"

class S3PrivateFileField(models.FileField):

    def __init__(self, *args, **kwargs):
        if kwargs.get("upload_to"):
            del kwargs["upload_to"]
        super().__init__(upload_to=upload_to, *args, **kwargs)