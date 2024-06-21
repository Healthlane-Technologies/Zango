import os
import requests

from pydantic import BaseModel, Field
from typing import List, Dict


class WorkFlowStatus(BaseModel):
    color: str
    label: str


class WorkFlowMeta(BaseModel):
    statuses: Dict[str, WorkFlowStatus]
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
    status_transitions: List[StatusTransition] = []
    user_stories: List[str] = []

    def apply(self, tenant, module, workflow_model, models):
        with open("workflow.json", "w") as f:
            f.write(self.model_dump_json())
        resp = requests.post(
            f"{os.getenv('ZANGO_CODEASSIST_URL')}/generate-workflow-v2",
            json={
                "workflow": self.model_dump(),
                "workflow_model": workflow_model,
                "models": [model.model_dump() for model in models],
            },
        )
        with open(
            os.path.join("workspaces", tenant, module, "workflows.py"), "a+"
        ) as f:
            f.write(resp.json()["content"])
            f.write("\n\n")
