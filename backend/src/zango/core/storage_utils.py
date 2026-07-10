import json
import os
import re
import uuid

import filetype
from storages.backends.s3boto3 import S3Boto3Storage

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import connection, models


class S3StaticStorage(S3Boto3Storage):
    location = getattr(settings, "AWS_STATIC_STORAGE_LOCATION", "static")
    default_acl = "public-read"
    querystring_auth = False
    bucket_name = getattr(settings, "AWS_STATIC_STORAGE_BUCKET_NAME", "")
    custom_domain = getattr(settings, "AWS_CLOUDFRONT_DOMAIN", None)


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
    except Exception:
        return


# Binary file types are verified with `filetype` (pure-Python, content-based
# magic-byte detection - no system dependency like libmagic). The submitted
# filename extension and Content-Type header are both attacker-controlled,
# so the actual bytes are checked against the extension the upload claims.
_FILETYPE_EXTENSION_MAP = {
    ".pdf": "pdf",
    ".doc": "doc",
    ".docx": "docx",
    ".jpg": "jpg",
    ".jpeg": "jpg",
    ".png": "png",
    ".xls": "xls",
    ".xlsx": "xlsx",
    ".mp3": "mp3",
    ".wav": "wav",
    ".ppt": "ppt",
    ".pptx": "pptx",
    ".zip": "zip",
    ".ico": "ico",
    ".mp4": "mp4",
    ".webm": "webm",
}

# SVG is XML/text, so it has no fixed magic-byte signature. It is instead
# scanned for embedded script/event-handler content, the classic stored-XSS
# vector for image-upload features (a valid SVG can carry <script> tags).
_SVG_DANGEROUS_PATTERNS = [
    re.compile(rb"<\s*script", re.IGNORECASE),
    re.compile(rb"on\w+\s*=", re.IGNORECASE),  # onload=, onerror=, onclick=...
    re.compile(rb"javascript\s*:", re.IGNORECASE),
    re.compile(rb"<\s*foreignobject", re.IGNORECASE),
    re.compile(rb"<!entity", re.IGNORECASE),  # XXE
    re.compile(rb"<!doctype", re.IGNORECASE),
]


def _read_head(value, num_bytes):
    value.seek(0)
    head = value.read(num_bytes)
    value.seek(0)
    return head


def _validate_svg_content(value):
    content = _read_head(value, 1024 * 1024)
    for pattern in _SVG_DANGEROUS_PATTERNS:
        if pattern.search(content):
            raise ValidationError(
                "This SVG file contains embedded scripts or executable "
                "content and cannot be uploaded."
            )
    if b"<svg" not in content.lower():
        raise ValidationError("This file is not a valid SVG image.")


def _validate_json_content(value):
    content = _read_head(value, 1024 * 1024)
    try:
        json.loads(content.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        raise ValidationError("This file is not valid JSON.")


def _validate_binary_signature(value, ext):
    expected = _FILETYPE_EXTENSION_MAP.get(ext)
    if not expected:
        return
    value.seek(0)
    kind = filetype.guess(value)
    value.seek(0)
    if kind is None or kind.extension != expected:
        raise ValidationError(
            "The file content does not match its extension. Upload rejected."
        )


def validate_file_extension(value):
    ext = os.path.splitext(value.name)[-1].lower()  # [0] returns path+filename
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
        ".mp4",
        ".webm",
        ".csv",
        ".json",
    ]
    if ext not in valid_extensions:
        raise ValidationError(
            "The file type you are trying to upload is not supported."
        )

    if ext == ".svg":
        _validate_svg_content(value)
    elif ext == ".json":
        _validate_json_content(value)
    elif ext == ".csv":
        pass  # plain text, no reliable binary signature to check
    else:
        _validate_binary_signature(value, ext)


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
