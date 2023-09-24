import json
from django.http import HttpResponse


def get_api_response(success, response_content, status):
    response = {
        "success": success,
        "response": response_content
    }
    
    return HttpResponse(json.dumps(response), status=status)
