import requests
import json

from typing import List
from pydantic import BaseModel, Field

from zango.core.utils import get_package_url


class GenericLoginConfig(BaseModel):
    card_color: str = Field(default="#FFFFFF")
    card_title: str = Field(default="")
    header_text: str = Field(default="")
    corner_radius: int = Field(default=4)
    logo_placement: str = Field(default="topLeft")
    paragraph_text: str = Field(default="")
    card_text_color: str = Field(default="#6c747d")
    background_color: str = Field(default="#5048ED")
    paragraph_text_color: str = Field(default="#FFFFFF")

    def apply(self):
        resp = requests.post(
            get_package_url(None, "configure/orm/generic_login_config/", "login"),
            data={
                "config": json.loads(self.model_dump_json()),
            },
            headers={"Content-Type": "application/json"},
        )


class LoginConfig(BaseModel):
    role: str
    landing_url: str = Field(default="/frame/router")

    def apply(self):
        try:
            from zango.apps.appauth.models import UserRoleModel

            user_role = UserRoleModel.objects.get(name=self.role)
            config = json.loads(self.model_dump_json())
            del config["role"]
            resp = requests.get(
                get_package_url(
                    None,
                    f'configure/orm/login_config/?filters={{"user_role_id": {user_role.pk} }}&first=true',
                    "login",
                ),
                headers={"Content-Type": "application/json"},
            ).json()
            if not resp["success"] or len(resp["response"]) == 0:
                resp = requests.post(
                    get_package_url(None, "configure/orm/login_config/", "login"),
                    data={
                        "user_role_id": user_role.pk,
                        "config": config,
                    },
                    headers={"Content-Type": "application/json"},
                )
        except Exception as e:
            import traceback

            traceback.print_exc()
