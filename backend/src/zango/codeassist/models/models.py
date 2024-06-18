from typing import List
from pydantic import BaseModel
import json
import requests
import os
import subprocess

from .base_fields import FieldBase

from zango.codeassist import URL


class ModelField(FieldBase):
    pass


class Model(BaseModel):
    name: str
    fields: List[ModelField]

    def apply(self, tenant, module):
        print(
            f"Applying model {self.name} for tenant {tenant} and module {module}",
            self.model_dump_json(),
        )
        resp = requests.post(
            f"{URL}/generate-model",
            json=json.loads(self.model_dump_json()),
        )
        with open(os.path.join("workspaces", tenant, module, "models.py"), "a+") as f:
            f.write(resp.json()["content"])
            f.write("\n\n\n")
