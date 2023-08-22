from django.http import Http404
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.core import exceptions
from django.core.exceptions import ImproperlyConfigured
from tenant_schemas.utils import schema_context
from django.core.exceptions import PermissionDenied

# from backend.apps.tenants.companyusers.models import ZelthyAccessLogModel
# from backend.core.common_utils import get_company_tenant
# from django.utils import timezone
# from datetime import timedelta

"""
Two types of permissioned accesses are supported:
 - Session based: Works well for webapps hosted on Zelthy 
 - Remote Token based: Works well for external systems, mobile apps, etc.

"""


def update_access_log(request):
  with schema_context(get_company_tenant(request.tenant).name):
    cuser = request.user.zelthy_user
    if not ZelthyAccessLogModel.objects.filter(
                  user=cuser, 
                  resource_path=request.META.get('PATH_INFO'),
                  client=request.tenant,
                  created_at__gte=timezone.now()-timedelta(seconds=60)
                  ):
      try:
        ZelthyAccessLogModel.objects.create(
                    user=cuser,
                    resource_path=request.META.get('PATH_INFO',"")[:250],
                    client=request.tenant,
                    client_ip=request.META.get('HTTP_X_FORWARDED_FOR',""),
                    user_agent=request.META.get('HTTP_USER_AGENT',"")[:250],
                    http_host=request.META.get('HTTP_HOST', "")[:49],
                    server_name=request.META.get('SERVER_NAME', "")[:90],
                    request_method=request.META.get('REQUEST_METHOD'),
                    querystring=request.META.get('QUERY_STRING'),
                    post_data=str(request.POST)                  
                    )
      except Exception as e:
        #trigger email to admin
        pass

    return




class SetUpUtils(object):


  def has_permission(self):
    if not self.is_user_active():
      return False
    # try:
    #   if not self.request.user.default_therapy_role.allow_access(self.request):
    #     return False
    # except:
    #   pass
        
    # if not self.permission:
    #   return False
    # update_access_log(self.request)
    return True


  def dispatch(self, *args, **kwargs):
    if self.has_permission():
      return super(SetUpUtils, self).dispatch(*args, **kwargs)
    raise exceptions.PermissionDenied

  def get_user(self):
    return self.request.user


  def get_user_profile(self, request):
    response = {}
    company = request.tenant.therapy.company
    user = request.user
    from zelthybase.context_processors import current_environment
    env = current_environment(request)
    env = env['env']
    response['env'] = env   

    response['therapy_name'] = request.tenant.description
    if request.tenant.tenant_config.logo:
      response['company_logo'] = request.tenant.tenant_config.logo.url
    if request.tenant.tenant_config.color_config:
      cols = request.tenant.tenant_config.color_config.__dict__
      if cols.get('_state'):
        cols.pop('_state')
      response['colors'] = cols
    response['current_role'] = request.user.default_therapy_role
    response['current_url'] = request.path
    response['zelthy_user'] = request.user.email
    response['zelthy_websocket_endpoint'] = settings.ZELTHY_API_GATEWAY_WEBSOCKET
    all_therapies = []
    for t in request.user.therapy_roles.all():
      if t != request.user.default_therapy_role:
        all_therapies.append(
                  ("/switch_role/"+str(t.id)+"/", 
                    "%s - %s"%(t.role_name, t.therapy.brand_name))
                  )
    response['all_therapies'] = all_therapies
   
    return response


class SetUpMixin(SetUpUtils):
  """
  class to generate basic user settings to be used in all template generating views
  the class method as_view ensures login_required on subclassed views without any explicit declaration of login_required
  """

  @classmethod
  def as_view(cls):

    # if cls.request.path.startswith('/customization/'):
    #   login_url = '/admin/login'
    login_url = None
    module_name = cls.__module__
    if 'customization' in module_name:
      login_url = '/admin/login'
    return login_required(super(SetUpMixin, cls).as_view(), login_url=login_url)

