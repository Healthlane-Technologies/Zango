import requests
import json

from typing import List
from pydantic import BaseModel

from zango.codeassist import TENANT_URL


class GenericLoginConfig(BaseModel):
    card_color: str
    card_title: str
    header_text: str
    corner_radius: int
    logo_placement: str
    paragraph_text: str
    card_text_color: str
    background_color: str
    paragraph_text_color: str

    def apply(self):
        requests.post(
            f"{TENANT_URL}/login/configure/orm/genericloginconfig/",
            data={
                "config": json.loads(self.model_dump_json()),
            },
            headers={"Content-Type": "application/json"},
        )


class LoginConfig(BaseModel):
    role: str
    landing_url: str

    def apply(self):
        try:
            from zango.apps.appauth.models import UserRoleModel

            user_role = UserRoleModel.objects.get(name=self.role)
            config = json.loads(self.model_dump_json())
            del config["role"]
            requests.post(
                f"{TENANT_URL}/login/configure/orm/loginconfig/",
                data={
                    "user_role_id": user_role.pk,
                    "config": config,
                },
                headers={"Content-Type": "application/json"},
            )
        except Exception as e:
            print(e)
