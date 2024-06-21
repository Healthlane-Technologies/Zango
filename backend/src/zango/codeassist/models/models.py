from typing import List
from pydantic import BaseModel
import json
import requests
import os

from .base_fields import FieldBase


class ModelField(FieldBase):
    pass


class Model(BaseModel):
    name: str
    fields: List[ModelField]

    def apply(self, tenant, module):
        resp = requests.post(
            f"{os.getenv('ZANGO_CODEASSIST_URL')}/generate-model",
            json=json.loads(self.model_dump_json()),
        )
        with open(os.path.join("workspaces", tenant, module, "models.py"), "a+") as f:
            f.write(resp.json()["content"])
            f.write("\n\n\n")
