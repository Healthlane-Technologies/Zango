import json
import re
from django.http import HttpResponse
from django.conf import settings
from django.http import Http404

from .zelthy_preprocessor import *
from .helpers import get_app_base_dir, get_module_path, get_userrole_model, get_view_unique_name


def check_userAccessPerm(request):
    if request.user.is_anonymous:
        user_role = get_userrole_model().objects.get(name='AnonymousUsers')
        return user_role.has_perm(request, 'userAccess')
    else:
        return request.user.has_perm(request, 'userAccess') \
                or request.user_role.has_perm(request, 'userAccess')

def check_view_perm(request, view_name):
    if request.user.is_anonymous:
        user_role = get_userrole_model().objects.get(name='AnonymousUsers')
        return user_role.has_perm(request, 'view', view_name)
    else:
        return request.user.has_perm(request, 'view', view_name) \
                or request.user_role.has_perm(request, 'view', view_name)



    


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
    if not check_userAccessPerm(request):
        return HttpResponse('Permission denied!', status=403)
    app_dir = get_app_base_dir(request.tenant)
    app_settings_file = app_dir / "settings.json" 
    with app_settings_file.open() as f:
        app_settings = json.load(f)
    routes = app_settings['routes']
    path = request.path.lstrip('/')    
    for r in routes:
        r_regex = re.compile(r['re_path'])
        if r_regex.search(path): # match module
            module = r['module']
            module_path = get_module_path(request.tenant, module)            
            mod_url_path = path[len(r['re_path'].strip("^")):]
            url_file = app_dir / module_path / r["url"]
            url_file = url_file.with_suffix(".py")
            with url_file.open() as f:
                _url_file = f.read()  
            zcode = ZPreprocessor(
                    _url_file, 
                    request=request, 
                    parent_path=url_file.parent, 
                    app_dir=app_dir,
                    app_settings=app_settings
                    )
            c = ZimportStack(zcode, request=request)
            c.process_import_and_execute()
            urlpatterns = c._globals['urlpatterns']
            for pattern in urlpatterns:                
                resolve = pattern.resolve(mod_url_path) # find view
                if resolve:
                    match = pattern.pattern.regex.search(mod_url_path)
                    kwargs = match.groupdict()
                    view_unique_name = get_view_unique_name(r['module'], pattern.callback)
                    if check_view_perm(request, view_unique_name):
                        return pattern.callback(request, *args, **kwargs)
                    else:
                        return HttpResponse('Permission denied!', status=403)


                    
    raise Http404()
