import os
import uuid
from django.db import models, connection
from django.core.exceptions import ValidationError
from storages.backends.s3boto3 import S3Boto3Storage


def RandomUniqueFileName(instance, filename):
    try:
        path = connection.tenant.name + "/" + instance.__class__.__name__
        extension = filename.split(".")[-1]
        file_ = "%s.%s" % (uuid.uuid4(), extension)
        return os.path.join(path, file_)
    except:
        return


MediaS3Boto3Storage = lambda: S3Boto3Storage(location="media")


def validate_file_extension(value):
    ext = os.path.splitext(value.name)[-1]  # [0] returns path+filename
    valid_extensions = [
        ".pdf",
        ".doc",
        ".docx",
        ".jpg",
        ".jpeg",
        ".png",
        ".svg",
        ".xls",
        ".xlsx",
        ".mp3",
        ".wav",
        ".ppt",
        ".pptx",
        ".zip",
        ".ico",
    ]
    if not ext.lower() in valid_extensions:
        raise ValidationError(
            "The file type you are trying to upload is not supported."
        )


def local_save(instance, filename):
    class_name = str(type(instance))
    folder = class_name.split(".")[-1].split("'")[0]
    tenant = class_name.split(".")[3]
    extension = filename.split(".")[-1]
    return f"{tenant}/{folder}/{uuid.uuid4()}.{extension}"


class ZFileField(models.FileField):
    def __init__(
        self,
        verbose_name=None,
        name=None,
        upload_to="",
        storage=None,
        make_public=False,
        validators=[validate_file_extension],
        **kwargs,
    ):
        super(ZFileField, self).__init__(
            verbose_name=verbose_name,
            name=name,
            upload_to=RandomUniqueFileName
            if os.getenv("USE_S3") == "TRUE"
            else local_save,
            storage=storage,
            validators=[validate_file_extension],
            **kwargs,
        )
        if make_public is False:
            self.storage.default_acl = "private"
