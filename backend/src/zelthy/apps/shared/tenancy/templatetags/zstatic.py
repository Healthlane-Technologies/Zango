import os

from django.templatetags.static import static as original_static
from django import template
register = template.Library()

@register.simple_tag(takes_context=True)
def zstatic(context, static_file_path, is_build=False):
    """
        TODO: we can override static tag to return app path if we are in app tenant. For
        public tenant, default behaviour will be retained
    """
    request = context['request']
    app_name = request.tenant.name
    app_static_file_path = "workspaces/%s/"%(app_name)  
    file_path = app_static_file_path+static_file_path
    if is_build:
        try:
            build_file_path = app_static_file_path+static_file_path    
            build_folder_path_without_file = '/'.join(build_file_path.split('/')[:-1])
            folder_contents  = os.listdir(build_folder_path_without_file+'/static')
            build_files = [filename for filename in folder_contents if 'build' in filename]
            if build_files:
                latest_build_file =  '/'+ sorted(build_files)[-1]
                file_path = build_folder_path_without_file+latest_build_file
        except Exception as e:
            import traceback
            print(traceback.format_exc())
        
    return original_static(file_path)