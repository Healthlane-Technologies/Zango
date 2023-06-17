import json
import re
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse
from django.conf import settings

from .zelthy_preprocessor import *

@csrf_exempt
def zelthy_dynamic_views(request, *args, **kwargs):
    from pathlib import Path
    app_dir = settings.BASE_DIR / "zelthy_apps" / request.tenant.name
    app_settings_file = app_dir / "settings.json" 
    with app_settings_file.open() as f:
        app_settings = json.load(f)
    routes = app_settings['routes']
    path = request.path.lstrip('/')
    print(routes)
    for r in routes:
        r_regex = re.compile(r['url_regex'])
        if r_regex.search(path):
            match_found = True
            if r['type'] == 'page':
                view_file = app_dir / "pages"/ r['page'] / "view.py"
            elif r['type'] == 'api':
                view_file = app_dir / "apis" / r['api'] / "view.dpy"
            match = r_regex.search(path)
            print(match)
            print(view_file)
            break
    if match_found:
        with view_file.open() as f:
            view_file = f.read()    
        print(view_file)
        zcode = ZPreprocessor(view_file, request=request)
        c = ZimportStack(zcode, request=request)
        c.process_import_and_execute()
        kwargs = match.groupdict()
        ZelthyCustomView = c._globals['ZelthyCustomView']
        return ZelthyCustomView.as_view()(request, *args, **kwargs)
    raise Http404()

    print(request.path)
    return HttpResponse("Hello world from library!")
    
    url = args[0]
    _globals = globals()
    regexes = ZelthyDynamicVersionsMixin.get_routes(request)
    match_found = False    
    for r in regexes:
        if r['url_regex'].search(url):
            match_found = True
            view_file = r['view_file']
            match = r['url_regex'].search(url)
    if match_found:    
        zcode = ZPreprocessor(view_file, request=request)
        c = ZimportStack(zcode, request=request)
        c.process_import_and_execute()
        kwargs = match.groupdict()
        ZelthyCustomView = c._globals['ZelthyCustomView']
        return ZelthyCustomView.as_view()(request, *args, **kwargs)
    raise Http404()