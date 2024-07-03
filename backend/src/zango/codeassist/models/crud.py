import os
import requests
import json

from pydantic import BaseModel, Field
from typing import List, Dict, Optional

from .base_fields import FieldBase
from .forms import Form
from .workflow import WorkFlow
from .detail import Detail


class TableField(FieldBase):
    pass


class RowAction(BaseModel):
    name: str
    key: str
    description: str
    type: str
    form: str | None
    roles: List[str]


class CrudMeta(BaseModel):
    model: str
    fields: List[str]
    row_selector: Dict[str, str | bool] = Field(default_factory=dict)
    detail_class: Detail | None = None


class CrudTable(BaseModel):
    name: str
    fields: List[TableField]
    meta: CrudMeta
    row_actions: List[RowAction]
    table_actions: List = Field(default_factory=list)
    user_stories: List[str] = Field(default_factory=list)

    def apply(self, tenant, module, models, form_name):
        resp = requests.post(
            f"{os.getenv('ZANGO_CODEASSIST_URL')}/generate-crud-table",
            json={
                "table": json.loads(self.model_dump_json()),
                "models": [json.loads(model.model_dump_json()) for model in models],
                "form": form_name,
            },
        )
        with open(os.path.join("workspaces", tenant, module, "tables.py"), "a+") as f:
            f.write(resp.json()["content"])
            f.write("\n\n")
        if self.meta.detail_class:
            self.meta.detail_class.apply(tenant, module, models)


class CrudView(BaseModel):
    name: str
    page_title: str
    add_btn_title: str
    workflow: WorkFlow | None = None
    table: CrudTable | None = None
    form: Form | None = None
    model: str
    roles: List[str] = Field(default_factory=list)

    def apply(self, tenant, module, models):
        resp = requests.post(
            f"{os.getenv('ZANGO_CODEASSIST_URL')}/generate-crud-view",
            json=self.model_dump(),
        )
        with open(os.path.join("workspaces", tenant, module, "views.py"), "a+") as f:
            f.write(resp.json()["content"])
            f.write("\n\n")

        if self.workflow:
            if self.workflow.user_stories:
                self.workflow.apply(tenant, module, self.model, models)

        if self.form:
            self.form.apply(tenant, module, models)

        if self.table:
            self.table.apply(tenant, module, models, self.form.name)
