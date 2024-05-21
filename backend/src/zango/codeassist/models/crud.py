import os
import requests
import json

from pydantic import BaseModel, Field
from typing import List, Dict, Optional

from .base_fields import FieldBase
from .forms import Form
from .workflow import WorkFlow
from .detail import Detail

from zango.codeassist import URL


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
    row_selector: Dict[str, str | bool]
    detail_class: Detail | None = None


class CrudTable(BaseModel):
    name: str
    fields: List[TableField]
    meta: CrudMeta
    row_actions: List[RowAction]
    table_actions: List = Field(default_factory=list)

    def apply(self, tenant, module):
        resp = requests.post(
            f"{URL}/generate-crud-table",
            json=json.loads(self.model_dump_json()),
        )
        with open(os.path.join("workspaces", tenant, module, "tables.py"), "a+") as f:
            f.write(resp.json()["content"])
            f.write("\n\n")
        if self.meta.detail_class:
            self.meta.detail_class.apply(tenant, module)


class CrudView(BaseModel):
    name: str
    page_title: str
    add_btn_title: str
    workflow: WorkFlow | None = None
    table: CrudTable
    form: Form | None = None
    model: str

    def apply(self, tenant, module):
        resp = requests.post(
            f"{URL}/generate-crud-view",
            json=json.loads(self.model_dump_json()),
        )
        with open(os.path.join("workspaces", tenant, module, "views.py"), "a+") as f:
            f.write(resp.json()["content"])
            f.write("\n\n")
        if self.workflow:
            self.workflow.apply(tenant, module)
        if self.form:
            self.form.apply(tenant, module)
        self.table.apply(tenant, module)
