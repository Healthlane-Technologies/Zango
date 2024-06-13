from pydantic import BaseModel
import requests
import json
import os
from typing import List

from .base_fields import FieldBase

from zango.codeassist import URL


class FormField(FieldBase):
    pass


class FormMeta(BaseModel):
    model: str
    title: str
    order: List[str]


class Form(BaseModel):
    name: str
    fields: List[FormField]
    meta: FormMeta
    user_stories: List[str] = []

    def apply(self, tenant, module, models):
        resp = requests.post(
            f"{URL}/generate-form",
            json={
                "form": self.model_dump(),
                "models": [model.model_dump() for model in models],
            },
        )
        with open(os.path.join("workspaces", tenant, module, "forms.py"), "a+") as f:
            f.write(resp.json()["content"])
            f.write("\n\n")
