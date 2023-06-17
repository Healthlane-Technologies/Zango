# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.apps import apps

from zelthybase.zelthy_safe_functions import load_safe_function_globals

def add_basic_builtins(_globals):
    #available builtins
    _globals['abs'] = abs
    _globals['all'] = all
    _globals['any'] = any
    _globals['int'] = int
    _globals['str'] = str
    _globals['pow'] = pow
    _globals['len'] = len
    _globals['range'] = range
    _globals['float'] = float
    _globals['list'] = list
    _globals['round'] = round
    _globals['min'] = min
    _globals['max'] = max
    _globals['round'] = round
    _globals['sorted'] = sorted
    _globals['bool'] = bool
    _globals['unicode'] = unicode
    _globals['True'] = True
    _globals['False'] = False
    # _globals['Exception'] = Exception
    return _globals

def add_math_funcs(_globals):
    #available math functions
    from math import ceil, floor, sqrt
    _globals['ceil'] = ceil
    _globals['floor'] = floor
    _globals['sqrt'] = sqrt
    return _globals

def add_pytz_funcs(_globals):
    #available pytz functions
    from pytz import timezone, utc
    _globals['timezone'] = timezone
    _globals['utc'] = utc
    return _globals

def add_datetime_funcs(_globals):
    #available datetime functions
    from datetime import date, datetime, timedelta, time, tzinfo
    _globals['date'] = date
    _globals['datetime'] = datetime
    _globals['timedelta'] = timedelta
    _globals['time'] = time
    _globals['tzinfo'] = tzinfo
    return _globals

def add_json_funcs(_globals):
    #available json functions
    from json import dumps, loads
    _globals['dumps'] = dumps
    _globals['loads'] = loads
    return _globals

def add_django_utils(_globals):
    from django.shortcuts import redirect
    from django.apps import apps
    from django.conf import settings
    from django.core.urlresolvers import reverse
    from django.http import HttpResponseRedirect, HttpResponse
    from django.core.files.storage import FileSystemStorage
    from django.utils import timezone
    from django.template import loader
    from django.db.models import Q
    _globals['redirect'] = redirect
    _globals['apps'] = apps
    _globals['settings'] = settings
    _globals['reverse'] = reverse
    _globals['HttpResponseRedirect'] = HttpResponseRedirect
    _globals['HttpResponse'] = HttpResponse
    _globals['FileSystemStorage'] = FileSystemStorage
    _globals['timezone'] = timezone
    _globals['loader'] = loader
    _globals['Q'] = Q
    return _globals

def add_communication_utils(_globals):
    from backend.core.mail import ZelthyEmail
    _globals['ZelthyEmail'] = ZelthyEmail
    from django.apps import apps
    sms_config = apps.get_model(
                        app_label='sms', 
                        model_name='SMSConfig'
                        )
    _globals['SMS'] = sms_config.objects.all().first()
    return _globals


def zelthy_importer(module, obj, caller_type):
    from importlib import import_module
    mod = import_module(module)
    return getattr(mod, obj)


def zelthy_trigger_importer(module, obj):
    return zelthy_importer(module, obj, "trigger")



def zelthy_task_importer(module, obj):
    return zelthy_importer(module, obj, "task")


def zelthy_safe_exec(obj, _globals, _locals):
    """Allowed functions:
    Builtins: abs, all any, int, str, pow, len, range, float, list\
    round, min, max, round, sorted
    math function: ceil, floor, sqrt
    pytz functions: timezone, utc
    datetime functions: date, datetime, timedelta, time, tzinfo
    json functions: loads, dumps
    Import is prohibited
    -----------------------
    For search formula: objects & search_value will refer to 
    the filter queryset and search string. E.g.
    objects = objects.filter(patient__ethnicity__icontains=search_value)


    """
    _globals = add_basic_builtins(_globals)
    _globals = add_math_funcs(_globals)
    _globals = add_pytz_funcs(_globals)
    _globals = add_datetime_funcs(_globals)
    _globals = add_json_funcs(_globals)

        
    exec(obj, _globals, _locals)

def zelthy_formula_search_safe_exec(
                obj, _globals, _locals):
    _globals = add_basic_builtins(_globals)
    _globals = add_math_funcs(_globals)
    _globals = add_pytz_funcs(_globals)
    _globals = add_datetime_funcs(_globals)
    _globals = add_json_funcs(_globals)
    _globals['zelthy_importer'] = zelthy_task_importer        
    exec(obj, _globals, _locals)
    

def zelthy_triggers_safe_exec(obj, _globals, _locals):
    
    import __future__
    _globals['__future__'] = __future__

    #available pytz functions
    import pytz
    _globals['pytz'] = pytz

    #available datetime functions
    import datetime
    _globals['datetime'] = datetime
    
    #available json functions
    import json
    _globals['json'] = json

    import requests
    _globals['requests'] = requests

    import urllib
    _globals['urllib'] = urllib

    import hashlib
    _globals['hashlib'] =hashlib

    import uuid
    _globals['uuid'] = uuid

    import boto3
    _globals['boto3'] = boto3

    import xlrd
    _globals['xlrd'] = xlrd

    import xlsxwriter
    _globals['xlsxwriter'] = xlsxwriter

    import mimetypes
    _globals['mimetypes'] = mimetypes

    import pdfkit
    _globals['pdfkit'] = pdfkit

    _globals = add_django_utils(_globals)
    _globals = add_communication_utils(_globals)
    _globals['zelthy_importer'] = zelthy_trigger_importer
    # _globals['tkv'] = apps.get_model('configuration', 'TenantKeyValueStore')
    _globals = load_safe_function_globals(_globals)
    exec(obj, _globals, _locals)

def zelthy_tasks_safe_exec(obj, _globals, _locals, tenant=None):

    _globals['tenant'] = tenant
    
    import __future__
    _globals['__future__'] = __future__

    #available pytz functions
    import pytz
    _globals['pytz'] = pytz

    #available datetime functions
    import datetime
    _globals['datetime'] = datetime
    
    #available json functions
    import json
    _globals['json'] = json

    import requests
    _globals['requests'] = requests

    import hashlib
    _globals['hashlib'] =hashlib

    import uuid
    _globals['uuid'] = uuid

    import boto3
    _globals['boto3'] = boto3

    import xlrd
    _globals['xlrd'] = xlrd

    import xlsxwriter
    _globals['xlsxwriter'] = xlsxwriter

    import mimetypes
    _globals['mimetypes'] = mimetypes

    import pdfkit
    _globals['pdfkit'] = pdfkit

    _globals = add_django_utils(_globals)
    _globals = add_communication_utils(_globals)
    _globals['zelthy_importer'] = zelthy_task_importer
    # _globals['tkv'] = apps.get_model('configuration', 'TenantKeyValueStore')
    _globals = load_safe_function_globals(_globals)
    exec(obj, _globals, _locals)


def zelthy_codeexec_safe_exec(obj, _globals, _locals):
    
    import __future__
    _globals['__future__'] = __future__

    #available pytz functions
    import pytz
    _globals['pytz'] = pytz

    #available datetime functions
    import datetime
    _globals['datetime'] = datetime
    
    #available json functions
    import json
    _globals['json'] = json

    import requests
    _globals['requests'] = requests

    import urllib
    _globals['urllib'] = urllib

    import hashlib
    _globals['hashlib'] =hashlib

    import uuid
    _globals['uuid'] = uuid

    import boto3
    _globals['boto3'] = boto3

    import xlrd
    _globals['xlrd'] = xlrd

    import xlsxwriter
    _globals['xlsxwriter'] = xlsxwriter

    import mimetypes
    _globals['mimetypes'] = mimetypes

    import pdfkit
    _globals['pdfkit'] = pdfkit

    _globals = add_django_utils(_globals)
    _globals = add_communication_utils(_globals)
    _globals['zelthy_importer'] = zelthy_task_importer
    # _globals['tkv'] = apps.get_model('configuration', 'TenantKeyValueStore')
    _globals = load_safe_function_globals(_globals)
    exec(obj, _globals, _locals)
