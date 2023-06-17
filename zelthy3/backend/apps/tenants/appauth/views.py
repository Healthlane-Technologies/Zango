import time

import logging
logger = logging.getLogger('zelthy')

from django.core import signing
from django.conf import settings
from django.urls import reverse
from django.shortcuts import redirect
from django.views.generic import View
from django.contrib.auth import authenticate
from django.views.generic.base import TemplateView
from django.views.decorators.csrf import csrf_exempt
from django.core.exceptions import ImproperlyConfigured

from rest_framework import status
from rest_framework import exceptions
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny

from django.contrib.auth import login, logout
from django.core.exceptions import ImproperlyConfigured

from tenant_schemas.utils import schema_context

# from backend.core.common_utils import get_company_tenant

from django.utils.decorators import method_decorator
from backend.core.api import ZelthySessionAppAPIView



USER_AUTH_BACKEND = 'backend.apps.tenants.appauth.auth_backend.AppUserModelBackend'


@method_decorator(csrf_exempt, name='dispatch')
class AppUserLoginView(TemplateView):
    """
    View to render the login page html.
    """
    template_name = 'applogin/login.html' # To be updated with new html

    def get_template_names(self):
        """ 
        returns custom login template if available else returns default template_name 
        """
        return ['zcustom/login.html', self.template_name]


class AppLogoutView(View):

    def add_protocol(self, request, url):
        if request.is_secure():
            full_url = 'https://' + url
        else:
            full_url = 'http://' + url
        return full_url

    def get(self, request, *args, **kwargs):
        logout(request)
        logout_uri = reverse('app-login-view')
        meta = request.META['HTTP_HOST']
        logout_url = self.add_protocol(request, meta + logout_uri)
        return redirect(logout_url)

@method_decorator(csrf_exempt, name='dispatch')
class AppUserLoginAPI(APIView):
    permission_classes = (AllowAny,)

    def __init__(self):
        self.user = None

    def perform_auth_validation(self, request):
        """
        validation of auth step
        """
        _type = request.data.get('type')
        if _type == 'credentials':
            app_user = authenticate(
                    username=request.data.get('username'),
                    password=request.data.get('password')
                    )
            if not app_user:
                return {"is_validated": False, 
                        "message": "Incorrect username or password",
                        "responsecode": status.HTTP_400_BAD_REQUEST,
                        "data": {}
                        }
            else:
                self.user = app_user.user
                return {"is_validated": True, 
                        "message": "Authenticated. Can proceed to next step",
                        "responsecode": status.HTTP_200_OK,
                        "next_step": "done",
                        "data": {
                            "cuser": app_user.id, 
                            "user": app_user.user.id, 
                            "auth_type": request.data.get('type'),
                            "access_types": request.data.get('accessTypes')
                            }
                        }

    def post(self, request):
        current_step = request.data.get('step', None)

        if current_step == 'auth':
            _data = self.perform_auth_validation(request)
        else:
            _data = {"is_validated": False, 
                    "message": "Invalid Step. Please use auth.",
                    "responsecode": status.HTTP_400_BAD_REQUEST,
                    "next_step": "auth",
                    "data": {}
                    }

        if _data['is_validated']:
            login(self.request, self.user, backend=USER_AUTH_BACKEND)

        _status = _data.get("responsecode", status.HTTP_400_BAD_REQUEST)
        response = Response(data=_data, status=_status)

        if _data['is_validated']:
            response.set_cookie(settings.SESSION_COOKIE_NAME,
                                request.session.session_key, 
                                max_age=request.session.get_expiry_age(),
                                expires=time.time() + request.session.get_expiry_age(), 
                                # domain=self.get_domain(request),
                                path=settings.SESSION_COOKIE_PATH,
                                secure=settings.SESSION_COOKIE_SECURE or None,
                                httponly=settings.SESSION_COOKIE_HTTPONLY or None)
        return response



from backend.core.api import get_api_response
class InitializeAppAPIV1(ZelthySessionAppAPIView):

    """
    API to initialize app. Called by the FE App to initialize User Profile, Frames, Menu, etc.
    The layout of the app is created and the landing page content is determined from the first menu
    """

    def get(self, request, *args, **kwargs):
        response_content = {
                        "profile": {
                            "name": "John Doe",
                            "email": "jd@zelthy.com",
                            "mobile": "+919999999999",
                            "role": "PAP Executive",
                            "switch_roles": []
                        },
                        "frame": {
                            "name": "condense",
                            "api_level": 1,
                            "config": {
                                "extra_js":['<!-- Default Statcounter code for Zelthy Website\nhttps://www.zelthy.com -->\n<script type="text/javascript">\nvar sc_project=11738016; \nvar sc_invisible=1; \nvar sc_security="5a2e2e33"; \n</script>\n<script type="text/javascript"\nsrc="https://www.statcounter.com/counter/counter.js"\nasync></script>\n<noscript><div class="statcounter"><a title="Web Analytics\nMade Easy - Statcounter" href="https://statcounter.com/"\ntarget="_blank"><img class="statcounter"\nsrc="https://c.statcounter.com/11738016/0/5a2e2e33/1/"\nalt="Web Analytics Made Easy - Statcounter"\nreferrerPolicy="no-referrer-when-downgrade"></a></div></noscript>\n<!-- End of Statcounter Code -->', 
                                     '<script>alert("Hi")</script>'],
                                "header": {
                                    "color": "#ffffff",
                                    "opacity": "100",
                                    },
                                "sidebar": {
                                "color": '#E1D6AE',
                                "opacity": '100',
                                    },
                                "logo_background": {
                                    "color": "",
                                    "opacity": "100",
                                    },
                                "menu_text_color": {
                                    "color": '#212429',
                                    "opacity": '100',
                                },
                                "selected_menu_background": {
                                    "color": '#7f7676',
                                    "opacity": '100',
                                },
                                "menu_background": {
                                    "color": '#E1D6AE',
                                    "opacity": '100',
                                },
                                "menu_icon_background": {
                                "color": '',
                                "opacity": '100',
                                }                                
                            },
                            "menu": [
                                {
                                    "title": "All Patients1",
                                    "icon": "",
                                    "page_uuid": "3cf5e646-8e6c-42f9-8c35-e44a256639bc"
                                },
                                {
                                    "title": "All Orders",
                                    "icon": "",
                                    "page_uuid": "f156545c-8cd8-4070-bbdd-2f0cb81fe5ab"
                                }
                            ]
                        }
                    }   
        return get_api_response(True, response_content, 200)


@method_decorator(csrf_exempt, name='dispatch')
class AppView(TemplateView):
    """
    View to render the login page html.
    """
    template_name = 'app.html' # To be updated with new html
