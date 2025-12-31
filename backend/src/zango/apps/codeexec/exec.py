def add_django_utils(_globals):
    from django.apps import apps
    from django.conf import settings
    from django.core.files.storage import FileSystemStorage
    from django.db.models import Q
    from django.http import HttpResponse, HttpResponseRedirect
    from django.shortcuts import redirect
    from django.template import loader
    from django.urls import reverse
    from django.utils import timezone

    _globals["redirect"] = redirect
    _globals["apps"] = apps
    _globals["settings"] = settings
    _globals["reverse"] = reverse
    _globals["HttpResponseRedirect"] = HttpResponseRedirect
    _globals["HttpResponse"] = HttpResponse
    _globals["FileSystemStorage"] = FileSystemStorage
    _globals["timezone"] = timezone
    _globals["loader"] = loader
    _globals["Q"] = Q
    return _globals


def get_workspace():
    from django.db import connection

    from zango.apps.dynamic_models.workspace.base import Workspace

    ws = Workspace(connection.tenant, request=None, as_systemuser=True)
    ws.ready()
    return ws


def add_workspace_utils(_globals):
    _globals["get_workspace"] = get_workspace
    return _globals


def zelthy_codeexec_safe_exec(obj, _globals, _locals):
    import __future__

    _globals["__future__"] = __future__

    # available pytz functions
    import pytz

    _globals["pytz"] = pytz

    # available datetime functions
    import datetime

    _globals["datetime"] = datetime

    # available json functions
    import json

    _globals["json"] = json

    import requests

    _globals["requests"] = requests

    import urllib

    _globals["urllib"] = urllib

    import hashlib

    _globals["hashlib"] = hashlib

    import uuid

    _globals["uuid"] = uuid

    import boto3

    _globals["boto3"] = boto3

    import xlsxwriter

    _globals["xlsxwriter"] = xlsxwriter

    import mimetypes

    _globals["mimetypes"] = mimetypes

    import pdfkit

    _globals["pdfkit"] = pdfkit

    _globals = add_django_utils(_globals)
    _globals = add_workspace_utils(_globals)
    exec(obj, _globals, _locals)
