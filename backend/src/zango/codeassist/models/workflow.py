import os
import json
import requests

from pydantic import BaseModel, Field
from typing import List, Dict
from .forms import Form

from zango.codeassist import URL


class WorkFlowStatus(BaseModel):
    color: str
    label: str


class WorkFlowMeta(BaseModel):
    statuses: Dict[str, WorkFlowStatus]
    model: str
    on_create_status: str


class StatusTransition(BaseModel):
    name: str = Field(default="")
    display_name: str = Field(default="")
    description: str = Field(default="")
    from_status: str = Field(default="")
    to_status: str = Field(default="")
    form: str | None = Field(default=None)
    confirmation_message: str | None = Field(default=None)


class WorkFlow(BaseModel):
    name: str
    status_transitions: List[StatusTransition]
    meta: WorkFlowMeta

    def apply(self, tenant, module):
        resp = requests.post(
            f"{URL}/generate-workflow", json=json.loads(self.model_dump_json())
        )
        with open(
            os.path.join("workspaces", tenant, module, "workflows.py"), "a+"
        ) as f:
            f.write(resp.json()["content"])
            f.write("\n\n")
