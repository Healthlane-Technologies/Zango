from django.templatetags.static import static as original_static
from django import template
register = template.Library()

@register.simple_tag(takes_context=True)
def zstatic(context, static_file_path):
    """
        TODO: we can override static tag to return app path if we are in app tenant. For
        public tenant, default behaviour will be retained
    """
    request = context['request']
    app_name = request.tenant.name
    app_static_file_path = "workspaces/%s/"%(app_name)    
    return original_static(app_static_file_path+static_file_path)