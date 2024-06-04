import os
import json
import requests

from pydantic import BaseModel
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
    name: str
    display_name: str
    description: str
    from_status: str
    to_status: str
    form: str | None = None
    confirmation_message: str | None = None


class WorkFlow(BaseModel):
    name: str
    status_transitions: List[StatusTransition]
    meta: WorkFlowMeta

    def apply(self, tenant, module):
        resp = requests.post(f"{URL}/generate-workflow", json=json.loads(self.json()))
        with open(
            os.path.join("workspaces", tenant, module, "workflows.py"), "a+"
        ) as f:
            f.write(resp.json()["content"])
            f.write("\n\n")
