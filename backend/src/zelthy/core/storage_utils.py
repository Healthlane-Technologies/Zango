import os
import uuid
from django.db import models, connection
from django.conf import settings
from django.core.exceptions import ValidationError
from storages.backends.s3boto3 import S3Boto3Storage


class S3StaticStorage(S3Boto3Storage):
    location = getattr(settings, "AWS_STATIC_STORAGE_LOCATION", "static")
    default_acl = "public-read"
    querystring_auth = False
    bucket_name = getattr(settings, "AWS_STATIC_STORAGE_BUCKET_NAME", "")


class S3MediaStorage(S3Boto3Storage):
    location = getattr(settings, "AWS_MEDIA_STORAGE_LOCATION", "media")
    querystring_auth = True
    bucket_name = getattr(settings, "AWS_MEDIA_STORAGE_BUCKET_NAME", "")


def RandomUniqueFileName(instance, filename):
    try:
        path = connection.tenant.name + "/" + instance.__class__.__name__
        extension = filename.split(".")[-1]
        file_ = "%s.%s" % (uuid.uuid4(), extension)
        return os.path.join(path, file_)
    except:
        return


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
            upload_to=(RandomUniqueFileName),
            storage=storage,
            validators=[validate_file_extension],
            **kwargs,
        )
        if make_public is False:
            self.storage.default_acl = "private"
