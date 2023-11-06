import requests
import json


def lambda_invocation(payload):
    print("payload: ", payload)
    url = "https://microservices.zelthy.com/dev/codeassistv1"
    response = requests.request("POST", url, data=json.dumps(payload)).json()
    return response
