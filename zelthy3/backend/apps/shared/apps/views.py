import json
import traceback
from backend.core.api import ZelthySessionPlatformAPIView, get_api_response, ZelthyGenericPlatformAPIView
from backend.core.common_utils import get_next_schema_name
from .tasks import launch_new_app
from .models import AppModel
from .serializers import AppSerializerModel

import logging
logger = logging.getLogger('zelthy')


class AppaunchAppAPIV1(ZelthyGenericPlatformAPIView):

  def validate_domain(self, domain_url):
    import re
    pattern = "^(([a-zA-Z]{1})|([a-zA-Z]{1}[a-zA-Z]{1})|([a-zA-Z]{1}[0-9]{1})|([0-9]{1}[a-zA-Z]{1})|([a-zA-Z0-9][a-zA-Z0-9-_]{1,61}[a-zA-Z0-9]))\.([a-zA-Z]{2,6}|[a-zA-Z0-9-]{2,30}\.[a-zA-Z]{2,3})$"
    match_re = re.compile(pattern)
    if re.search(match_re, domain_url):
      return True
    return False


  def validate_data(self, data):
    if AppModel.objects.filter(name=data['name']).exists():
      success, message = False, "App name already taken"
    elif len(data['name']) < 5:
      success, message = False, "App name must have at least 5 charecters"
    elif not self.validate_domain(data['domain_url']):
      success, message =  False, "Invalid domain url"
    else:
      success, message = True, ""
    return success, message
    

  def post(self, request, *args, **kwargs):
    data = json.loads(request.data['data'])
    logo = request.data['logo']
    response_data = {}
    try:
      success, message = self.validate_data(data)
      if success:
        app = AppModel(
                  name=data['name'], 
                  schema_name=get_next_schema_name(), 
                  domain_url=data['domain_url'],
                  description=data['description'],
                  timezone=data['timezone'],
                  app_language=data['app_language'],
                  date_format=data['date_format'],
                  datetime_format=data['datetime_format'],
                  app_type='tenant',
                  category=data['category'],
                  logo=logo,
                  status='staged'
                  )
        app.save()
        task = launch_new_app.delay(str(app.uuid), countdown=30)
        result = {
                'app_uuid': str(app.uuid),
                'task_uuid': str(task)
                }
        status = 200
      else:
        result = {'message': message}
        status = 200
    except Exception as e:
      logger.error(traceback.format_exc())
      result = {'message': str(e)} 
      status = 500
      success = False   
    return get_api_response(
                      success, 
                      result,
                      status
                      )      



class AppDetailViewAPIV1(ZelthyGenericPlatformAPIView):

    def get_obj(self, **kwargs):
        obj = AppModel.objects.get(uuid=kwargs.get('app_uuid'))
        return obj

    def get(self, request, *args, **kwargs):
        try:
            obj = self.get_obj(**kwargs)
            serializer = AppSerializerModel(obj)
            success = True
            response_content = serializer.data
            status  = 200
        except Exception as e:
            success = False
            response_content = {"message": str(e)}
            status = 500

        return get_api_response(success, response_content, status)

    def put(self, request, *args, **kwargs):
        obj = self.get_obj(**kwargs)
        return 
        