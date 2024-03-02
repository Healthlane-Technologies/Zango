import os

from django.templatetags.static import static as original_static
from django import template

from zelthy.core.utils import get_current_request

register = template.Library()

@register.simple_tag(takes_context=True)
def static(context, static_file_path):
    """
        TODO: we can override static tag to return app path if we are in app tenant. For
        public tenant, default behaviour will be retained
    """
    request = get_current_request()
    app_name = request.tenant.name
    app_static_file_path = "workspaces/%s/"%(app_name)  
    file_path = app_static_file_path+static_file_path
    
    return original_static(file_path)