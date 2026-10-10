from django.shortcuts import redirect

from django.views.generic import TemplateView, View


class RedirectAppView(View):
    def get(self, request, *args, **kwargs):
        return redirect("/app")


class AppView(TemplateView):
    """
    This view renders the frontend app

    """

    template_name = "app.html"
