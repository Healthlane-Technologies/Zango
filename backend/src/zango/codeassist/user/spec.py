from time import sleep
import requests
import os

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
)
from zango.codeassist.models.forms import Form as FormCodeSpec, FormField, FormMeta
from zango.codeassist.models.detail import (
    Detail as DetailCodeSpec,
    DetailField,
    DetailMeta,
)
from zango.codeassist.models.packages.frame import (
    Frame as FrameCodeSpec,
)
from zango.codeassist.models.models import (
    Model as ModelCodeSpec,
    ModelField as ModelFieldCodeSpec,
)
from zango.codeassist.models.packages.login import LoginConfig
from zango.apps.shared.tenancy.models import TenantModel, Domain


class ModelField(BaseModel):
    name: str
    type: str


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
    detail: Detail = None
    form: Form = None
    table: CrudTable = None
    workflow: WorkFlow = None
    model: str


class UserStories(BaseModel):
    type: str
    stories: List[str]


class CrudUserStories(BaseModel):
    workflow: List[str] = []
    table: List[str] = []
    form: List[str] = []
    detail: List[str] = []


class View(BaseModel):
    type: str
    model: str
    roles: List[str] = []
    user_stories: CrudUserStories | UserStories = []


class Role(BaseModel):
    name: str


class Module(BaseModel):
    name: str
    models: Dict[str, str] = Field(default_factory=dict)
    # migrate_models: bool = False
    views: List[View] = []

    def apply(self):
        crud_views = []
        models_spec = {
            f"{model_name}": ModelCodeSpec.model_validate_json(
                requests.post(
                    f"{os.getenv('ZANGO_CODEASSIST_URL')}/generate-model-spec",
                    json={
                        "name": model_name,
                        "prompt": prompt,
                    },
                    headers={"Content-Type": "application/json"},
                ).text
            )
            for model_name, prompt in self.models.items()
        }
        for view in self.views:
            if view.type == "crud":
                crud_view = CrudViewCodeSpec(
                    name=f"{view.model}CrudView",
                    roles=view.roles,
                    model=view.model,
                    page_title="{{page_title}}",
                    add_btn_title="{{add_btn_title}}",
                )
                crud_view.workflow = WorkFlowCodeSpec(
                    name=f"{view.model}Workflow",
                    user_stories=view.user_stories.workflow,
                )
                crud_view.table = CrudTableCodeSpec(
                    name=f"{view.model}CrudTable",
                    fields=[
                        TableField(
                            name=field.name,
                            type="ModelCol",
                            constraints={},
                        )
                        for field in models_spec[view.model].fields
                    ],
                    row_actions=[],
                    table_actions=[],
                    meta=CrudMeta(
                        model=view.model,
                        detail_class=DetailCodeSpec(
                            name=f"{view.model}Detail",
                            fields=[
                                DetailField(
                                    name=field.name,
                                    type="ModelCol",
                                    constraints={},
                                )
                                for field in models_spec[view.model].fields
                            ],
                            meta=DetailMeta(
                                fields=[
                                    field.name
                                    for field in models_spec[view.model].fields
                                ]
                            ),
                            user_stories=view.user_stories.detail,
                        ),
                        fields=[field.name for field in models_spec[view.model].fields],
                    ),
                    user_stories=view.user_stories.table,
                )
                crud_view.form = FormCodeSpec(
                    name=f"{view.model}Form",
                    fields=[
                        FormField(
                            name=field.name,
                            type="ModelField",
                            constraints={},
                        )
                        for field in models_spec[view.model].fields
                    ],
                    meta=FormMeta(
                        model=view.model,
                        title="{{form_title}}",
                        order=[field.name for field in models_spec[view.model].fields],
                    ),
                    user_stories=view.user_stories.form,
                )

                crud_views.append(crud_view)

        module = ModuleCodeSpec(
            name=self.name,
            path=self.name,
            views=crud_views,
            models=models_spec.values(),
        )
        return module


class Package(BaseModel):
    name: str
    version: str


class AppSpec(BaseModel):
    modules: List[Module]
    app_name: str
    domain: str
    roles: List[str] = Field(default_factory=list)

    def apply(self):
        try:
            TenantModel.objects.get(name=self.app_name)
            print("App already exists, codeassist will not be applied")
            return
        except TenantModel.DoesNotExist:
            pass
        app, task_id = TenantModel.create(
            name=self.app_name,
            schema_name=self.app_name,
            description="",
            tenant_type="app",
            status="staged",
        )

        while app.status == "staged":
            print("Waiting for app to start")
            sleep(1)
            app = TenantModel.objects.get(id=app.id)
            if app.status == "deployed":
                try:
                    domain = Domain.objects.create(domain=self.domain, tenant=app)
                except Exception as e:
                    print(e)
                print("App started successfully, proceeding with codeassist")
                break

        application_spec = ApplicationSpec(
            modules=[module.apply() for module in self.modules],
            app_name=self.app_name,
            domain=self.domain,
            roles=[
                RoleCodeSpec(
                    name=role,
                    policies=[
                        [f"{view.model}CrudViewAccessPolicy", module.name]
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
