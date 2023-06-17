import json
import re
from django.http import HttpResponse
from django.conf import settings
from django.http import Http404

from .zelthy_preprocessor import *


def zelthy_dynamic_views(request, *args, **kwargs):

    """
    This function handles dynamic views for Zelthy apps. It takes a `request` object as input along with 
    arbitrary `*args` and `**kwargs`. It first gets the app directory, `app_settings_file`, and `app_settings` 
    from the `request.tenant.name` attribute. It then gets the `routes` from `app_settings`. The `path` is 
    obtained by removing the leading slash from `request.path`. A regex match is attempted for each route in 
    `routes`. If a match is found, the corresponding view file is opened and read. The contents of the view file 
    are preprocessed by `ZPreprocessor` and the imports are processed by `ZimportStack`. Finally, the 
    `ZelthyCustomView` is instantiated with `request`, `*args`, and `**kwargs` and its `as_view()` method is 
    called with the same parameters to get the final view. If no match is found, it raises an `Http404` exception.
    
    :param request: A `HttpRequest` object representing the request.
    :type request: django.http.HttpRequest
    :param *args: Arbitrary positional arguments.
    :type *args: tuple
    :param **kwargs: Arbitrary keyword arguments.
    :type **kwargs: dict
    :return: An instantiated view object that can be called with the `request`, `*args`, and `**kwargs`.
    :rtype: django.views.generic.base.View
    :raises Http404: If no match is found in the `routes`.
    """

    from pathlib import Path
    app_dir = settings.BASE_DIR / "zelthy_apps" / request.tenant.name
    app_settings_file = app_dir / "settings.json" 
    with app_settings_file.open() as f:
        app_settings = json.load(f)
    routes = app_settings['routes']
    path = request.path.lstrip('/')
    match_found = False
    for r in routes:
        r_regex = re.compile(r['url_regex'])
        if r_regex.search(path):
            match_found = True
            if r['type'] == 'page':
                view_file = app_dir / "pages"/ r['page'] / "view.py"
            elif r['type'] == 'api':
                view_file = app_dir / "apis" / r['api'] / "view.dpy"
            match = r_regex.search(path)
            break
    if match_found:
        with view_file.open() as f:
            view_file = f.read()    
        zcode = ZPreprocessor(view_file, request=request)
        c = ZimportStack(zcode, request=request)
        c.process_import_and_execute()
        kwargs = match.groupdict()
        ZelthyCustomView = c._globals['ZelthyCustomView']
        return ZelthyCustomView.as_view()(request, *args, **kwargs)
    raise Http404()
