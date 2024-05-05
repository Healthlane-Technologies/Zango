from django.conf import settings


class PlatformUserProfileMixin:

  
  def get_env_details(self, request):
      data = {}
      data['env_type'] = settings.ENV
      data['env_name'] = request.tenant.name
      if request.tenant.logo:
          data['logo_url'] = request.tenant.logo.url
      data['env_id'] = str(request.tenant.uuid)
      data['url'] = request.tenant.domain_url
      return data

  def get_user_profile(self, request):
    data = {}
    data['name'] = request.user.platform_user.name
    data['email'] = request.user.platform_user.email
    data['mobile'] = request.user.platform_user.mobile
    data['role'] = 'Platform User'
    data['user_uuid'] = request.user.username
    return data
  
  def get_profile(self, request):
    data = {
        'platform': self.get_env_details(request),
        'user_profile': self.get_user_profile(request)
    }
    return data