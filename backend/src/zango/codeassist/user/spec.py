from pydantic import BaseModel, Field
from typing import List, Dict

from zango.codeassist.models.app_spec import (
    ApplicationSpec,
    Module as ModuleCodeSpec,
    Role as RoleCodeSpec,
    Package,
)
from zango.codeassist.models.crud import (
    CrudTable as CrudTableCodeSpec,
    CrudMeta,
    CrudView as CrudViewCodeSpec,
    TableField,
)
from zango.codeassist.models.workflow import (
    WorkFlow as WorkFlowCodeSpec,
    WorkFlowMeta,
    WorkFlowStatus,
    StatusTransition,
)
from zango.codeassist.models.forms import Form as FormCodeSpec, FormField, FormMeta
from zango.codeassist.models.detail import (
    Detail as DetailCodeSpec,
    DetailField,
    DetailMeta,
)
from zango.codeassist.models.packages.frame import (
    Frame as FrameCodeSpec,
    MenuItem,
)
from zango.codeassist.models.models import (
    Model as ModelCodeSpec,
    ModelField as ModelFieldCodeSpec,
)
from zango.codeassist.models.packages.login import LoginConfig


class ModelField(BaseModel):
    name: str
    type: str


class Model(BaseModel):
    name: str
    fields: List[ModelField]


class WorkFlow(BaseModel):
    name: str
    statuses: List[str]
    transitions: List[List[str]]

    """
    on_create_status - it is assumed that the on_create_status will be the first status
    """


class CrudTable(BaseModel):
    name: str
    fields: List[str]
    row_actions: List[str] = Field(default_factory=list)
    table_actions: List[str] = Field(default_factory=list)
    model: str
    detail_class: str


class Form(BaseModel):
    name: str
    fields: List[str]
    model: str


class Detail(BaseModel):
    name: str
    fields: List[str]


class CrudView(BaseModel):
    name: str
    roles: List[str]
    detail: Detail
    form: Form
    table: CrudTable
    workflow: WorkFlow
    model: str


class Frame(BaseModel):
    role: str


class Login(BaseModel):
    role: str
    landing_url: str


class PackageConfigs(BaseModel):
    frame: List[Frame] | None = Field(default_factory=list)
    login: List[Login] | None = Field(default_factory=list)


class Role(BaseModel):
    name: str


class Module(BaseModel):
    name: str
    models: List[Model] = []
    # migrate_models: bool = False
    views: List[CrudView] = []

    def apply(self):
        module = ModuleCodeSpec(
            name=self.name,
            path=self.name,
            views=[
                CrudViewCodeSpec(
                    name=view.name,
                    page_title="",
                    add_btn_title="",
                    workflow=WorkFlowCodeSpec(
                        name=view.workflow.name,
                        status_transitions=[
                            StatusTransition(
                                from_status=transition[0],
                                to_status=transition[1],
                            )
                            for transition in view.workflow.transitions
                        ],
                        meta=WorkFlowMeta(
                            statuses={
                                status: WorkFlowStatus(
                                    color="",
                                    label="",
                                )
                                for status in view.workflow.statuses
                            },
                            model="",
                            on_create_status="",
                        ),
                    ),
                    table=CrudTableCodeSpec(
                        name=view.table.name,
                        fields=[
                            TableField(name=field, type="", constraints={})
                            for field in view.table.fields
                        ],
                        row_actions=[],
                        table_actions=[],
                        meta=CrudMeta(
                            model=view.table.model,
                            detail_class=DetailCodeSpec(
                                name=view.detail.name,
                                fields=[
                                    DetailField(name=field, type="", constraints={})
                                    for field in view.detail.fields
                                ],
                                meta=DetailMeta(fields=view.detail.fields),
                            ),
                            fields=view.table.fields,
                            row_selector={},
                        ),
                    ),
                    form=FormCodeSpec(
                        name=view.form.name,
                        fields=[
                            FormField(name=field, type="", constraints={})
                            for field in view.form.fields
                        ],
                        meta=FormMeta(
                            model=view.form.model, title="", order=view.form.fields
                        ),
                    ),
                    model=view.model,
                )
                for view in self.views
            ],
            models=[
                ModelCodeSpec(
                    name=model.name,
                    fields=[
                        ModelFieldCodeSpec(
                            name=field.name,
                            type=field.type,
                            constraints={},
                        )
                        for field in model.fields
                    ],
                )
                for model in self.models
            ],
        )
        return module


class AppSpec(BaseModel):
    modules: List[Module]
    tenant: str
    requirement_spec: str
    user_stories: List[str]
    package_configs: PackageConfigs | None = PackageConfigs()
    roles: List[Role] = Field(default_factory=list)
    packages: List[Package] = Field(default_factory=list)

    def apply(self):

        application_spec = ApplicationSpec(
            modules=[module.apply() for module in self.modules],
            tenant=self.tenant,
            package_configs={
                "frame": [
                    FrameCodeSpec(
                        role=package_config.role,
                    )
                    for package_config in self.package_configs.frame
                ],
                "login": [
                    LoginConfig(
                        role=package_config.role, landing_url=package_config.landing_url
                    )
                    for package_config in self.package_configs.login
                ],
            },
            roles=[
                RoleCodeSpec(
                    name=role.name,
                    policies=[
                        [f"{view.name}AccessPolicy", module.name]
                        for module in self.modules
                        for view in module.views
                        if role.name in view.roles
                    ],
                )
                for role in self.roles
            ],
            packages=self.packages,
        )

        application_spec.apply()
