from pydantic import BaseModel, Field
from typing import List, Dict

from zango.codeassist.models.app_spec import (
    ApplicationSpec,
    Module as ModuleCodeSpec,
    Role as RoleCodeSpec,
    PackageConfigs,
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


# class Model(BaseModel):
#     name: str
#     fields: List[ModelField]
#     user_stories: List[str] = []


class WorkFlow(BaseModel):
    name: str
    statuses: List[str]
    transitions: List[List[str]]
    user_stories: List[str] = []

    """
    on_create_status - it is assumed that the on_create_status will be the first status
    """


class CrudTable(BaseModel):
    name: str
    row_actions: List[str] = Field(default_factory=list)
    table_actions: List[str] = Field(default_factory=list)
    detail_class: str
    user_stories: List[str] = []


class Form(BaseModel):
    name: str
    user_stories: List[str] = []


class Detail(BaseModel):
    name: str
    user_stories: List[str] = []


class CrudView(BaseModel):
    name: str
    roles: List[str]
    detail: Detail
    form: Form
    table: CrudTable
    workflow: WorkFlow
    model: str


class Role(BaseModel):
    name: str


class Module(BaseModel):
    name: str
    models: Dict[str, List[ModelField]] = Field(default_factory=dict)
    # migrate_models: bool = False
    views: List[CrudView] = []

    def apply(self):
        module = ModuleCodeSpec(
            name=self.name,
            path=self.name,
            views=[
                CrudViewCodeSpec(
                    name=view.name,
                    page_title="{{title}}",
                    add_btn_title="{{add_btn_title}}",
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
                            on_create_status=view.workflow.statuses[0],
                        ),
                        user_stories=view.workflow.user_stories,
                    ),
                    table=CrudTableCodeSpec(
                        name=view.table.name,
                        fields=[
                            TableField(
                                name=field.name,
                                type="{{table_field_type}}",
                                constraints={},
                            )
                            for field in self.models[view.model]
                        ],
                        row_actions=[],
                        table_actions=[],
                        meta=CrudMeta(
                            model=view.model,
                            detail_class=DetailCodeSpec(
                                name=view.detail.name,
                                fields=[
                                    DetailField(
                                        name=field.name,
                                        type="{{detail_field_type}}",
                                        constraints={},
                                    )
                                    for field in self.models[view.model]
                                ],
                                meta=DetailMeta(
                                    fields=[
                                        field.name for field in self.models[view.model]
                                    ]
                                ),
                            ),
                            fields=[field.name for field in self.models[view.model]],
                            row_selector={},
                        ),
                        user_stories=view.table.user_stories,
                    ),
                    form=FormCodeSpec(
                        name=view.form.name,
                        fields=[
                            FormField(
                                name=field.name,
                                type="{{form_field_type}}",
                                constraints={},
                            )
                            for field in self.models[view.model]
                        ],
                        meta=FormMeta(
                            model=view.model,
                            title="{{form_title}}",
                            order=[field.name for field in self.models[view.model]],
                        ),
                        user_stories=view.form.user_stories,
                    ),
                    model=view.model,
                )
                for view in self.views
            ],
            models=[
                ModelCodeSpec(
                    name=model,
                    fields=[
                        ModelFieldCodeSpec(
                            name=field.name,
                            type=field.type,
                            constraints={},
                        )
                    ],
                )
                for model, fields in self.models.items()
                for field in fields
            ],
        )
        return module


class Package(BaseModel):
    name: str
    version: str


class AppSpec(BaseModel):
    modules: List[Module]
    app_name: str
    roles: List[str] = Field(default_factory=list)

    def apply(self):

        application_spec = ApplicationSpec(
            modules=[module.apply() for module in self.modules],
            app_name=self.app_name,
            roles=[
                RoleCodeSpec(
                    name=role,
                    policies=[
                        [f"{view.name}AccessPolicy", module.name]
                        for module in self.modules
                        for view in module.views
                        if role in view.roles
                    ],
                )
                for role in self.roles
            ],
            package_configs=PackageConfigs(
                frame=[
                    FrameCodeSpec(
                        role=role,
                    )
                    for role in self.roles
                ],
                login=[
                    LoginConfig(
                        role=role,
                    )
                    for role in self.roles
                ],
            ),
        )

        application_spec.apply()


app_spec = AppSpec(
    app_name="CodeAssist",
    modules=[
        Module(
            name="users",
            models={
                "User": [ModelField(name="name", type="string")],
                "Role": [ModelField(name="name", type="string")],
            },
            views=[
                CrudView(
                    name="UserCrudView",
                    roles=["admin"],
                    workflow=WorkFlow(
                        name="users_workflow",
                        statuses=["active", "inactive"],
                        transitions=[["active", "inactive"], ["inactive", "active"]],
                        user_stories=[
                            "User can be active if the user name is not john",
                        ],
                    ),
                    table=CrudTable(
                        name="users_table",
                        row_actions=[],
                        table_actions=[],
                        model="User",
                        detail_class="users_detail",
                    ),
                    form=Form(name="users_form", user_stories=[]),
                    model="User",
                    detail=Detail(name="users_detail", user_stories=[]),
                )
            ],
        ),
    ],
    roles=[
        "admin",
    ],
)

app_spec.apply()
