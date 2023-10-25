from backend.core.common_utils import set_app_schema_path
from django.utils.decorators import method_decorator

from backend.core.api import ZelthyGenericPlatformAPIView, get_api_response
from backend.apps.tenants.appauth.serializers import UserRoleSerializerModel
from backend.apps.tenants.appauth.models import UserRoleModel


@method_decorator(set_app_schema_path, name='dispatch')
class UserRoleAPIV1(ZelthyGenericPlatformAPIView):

  def get(self, request, *args, **kwargs):    
    roles = UserRoleModel.objects.all()
    serializer = UserRoleSerializerModel(roles, many=True)
    return get_api_response(True, serializer.data, 200)

  def post(self, request, *args, **kwargs):
    data = request.data
    role = UserRoleSerializerModel(data=data)
    if role.is_valid():
      success = True
      obj = role.save()
      response_content = UserRoleSerializerModel(obj).data
    else:
      success = False
      response_content = role.errors
    return get_api_response(success, response_content, 200)

  def put(self, request, *args, **kwargs):
    data = request.data
    try:
      obj = UserRoleModel.objects.get(id=data['id'])
      serializer = UserRoleSerializerModel(obj, data=data)
      if serializer.is_valid():
        serializer.save()
        success, response_content, status = True, "updated", 200
      else:
        success, response_content, status = False, serializer.errors, 200
    except Exception as e:
      success, response_content, status = False, str(e), 404
    return get_api_response(success, response_content, 200)