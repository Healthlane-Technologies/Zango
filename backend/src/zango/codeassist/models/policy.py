import os
from typing import List, Optional
from pydantic import BaseModel


class Permission(BaseModel):
    name: str
    type: str


class Statement(BaseModel):
    permissions: List[Permission]


class Policy(BaseModel):
    name: str
    description: Optional[str] = None
    statement: Statement


class Policies(BaseModel):

    policies: List[Policy]

    def apply(self, tenant, module):
        from django.db import connection
        from zango.apps.dynamic_models.workspace.base import Workspace

        with open(
            os.path.join("workspaces", tenant, module, "policies.json"), "w"
        ) as f:
            f.write(f"{self.model_dump_json()}")
        ws = Workspace(connection.tenant, request=None, as_systemuser=True)
        ws.ready()
        ws.sync_policies()
