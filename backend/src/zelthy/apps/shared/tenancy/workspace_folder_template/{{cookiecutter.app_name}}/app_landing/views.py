from django.views.generic import TemplateView


from zelthy.core.package_utils import package_installed

class AppLandingPageView(TemplateView):    

    template_name = "app_landing.html"

    def get_context_data(self, **kwargs):
        context = super(AppLandingPageView, self).get_context_data(**kwargs)
        from django.conf import settings
        import os
        project_name = os.path.basename(settings.BASE_DIR)
        context = {
            "project_name": project_name,
            "app_name": self.request.tenant.name
        }
        return context
    

    def get(self, request, *args, **kwargs):
        if package_installed("frame", request.tenant.name):
            from ..packages.frame.decorator import apply_frame_routing
            decorated_method = apply_frame_routing(self.get_decorated)
            return decorated_method(self, request, *args, **kwargs)

        return super(AppLandingPageView, self).get(request, *args, **kwargs)
    
    def get_decorated(self, request, *args, **kwargs):
        return super(AppLandingPageView, self).get(request, *args, **kwargs)