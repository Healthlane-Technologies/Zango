from typing import List
from pydantic import BaseModel
import requests
import json
import os

from .base_fields import FieldBase

from zango.codeassist import URL


class DetailField(FieldBase):
    pass


class DetailMeta(BaseModel):
    fields: List[str]


class Detail(BaseModel):
    name: str
    fields: List[DetailField]
    meta: DetailMeta
    user_stories: List[str] = []

    def apply(self, tenant, module, models):
        resp = requests.post(f"{URL}/generate-detail", json=self.model_dump())
        with open(os.path.join("workspaces", tenant, module, "details.py"), "a+") as f:
            f.write(resp.json()["content"])
            f.write("\n\n\n")
