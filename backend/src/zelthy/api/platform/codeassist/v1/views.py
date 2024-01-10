import json
import os
import importlib

from django.utils.decorators import method_decorator
from django.conf import settings

from zelthy.core.common_utils import set_app_schema_path
from zelthy.core.api import get_api_response, ZelthyGenericPlatformAPIView

from zelthy.apps.permissions.models import PolicyModel
from zelthy.apps.appauth.models import AppUserModel, UserRoleModel
from zelthy.apps.shared.tenancy.models import TenantModel

from .utils import lambda_invocation


@method_decorator(set_app_schema_path, name="dispatch")
class ConversationViewAPIV1(ZelthyGenericPlatformAPIView):
    def get_app_obj(self, **kwargs):
        obj = TenantModel.objects.get(uuid=kwargs.get("app_uuid"))
        return obj

    def get_settings_path(self, **kwargs):
        obj = self.get_app_obj(**kwargs)
        path = str(settings.BASE_DIR) + f"/workspaces/{obj.name}/settings.json"
        return path

    def get_settings(self, **kwargs):
        path = self.get_settings_path(**kwargs)
        with open(path) as f:
            settings_json = json.load(f)
        return settings_json

    def process_user_message(self, data, message, **kwargs):
        if data.get("action_data", {}).get("knowledge_base") == "basics":
            settings_json = self.get_settings(**kwargs)
            message = message + f" The settings.json is {json.dumps(settings_json)}"

        return message

    def post(self, request, app_uuid, *args, **kwargs):
        request_data = request.data

        data = json.loads(request_data["data"])
        data.update({"app_uuid": app_uuid, "user_id": str(request.user.id)})

        # action = data["action"]
        # if action in ["create_conversation", "update_conversation"]:
        #     data["action_data"]["message"] = self.process_user_message(
        #         data, data["action_data"]["message"], app_uuid=app_uuid
        #     )

        response_data = lambda_invocation(data)
        response = response_data["response"]
        return get_api_response(True, response, 200)


@method_decorator(set_app_schema_path, name="dispatch")
class ExecutionViewAPIV1(ZelthyGenericPlatformAPIView):
    def get_app_obj(self, **kwargs):
        obj = TenantModel.objects.get(uuid=kwargs.get("app_uuid"))
        return obj

    def get_settings_path(self, **kwargs):
        obj = self.get_app_obj(**kwargs)
        path = str(settings.BASE_DIR) + f"/workspaces/{obj.name}/settings.json"
        return path

    def get_settings(self, **kwargs):
        path = self.get_settings_path(**kwargs)
        with open(path) as f:
            settings_json = json.load(f)
        return settings_json

    def post(self, request, *args, **kwargs):
        request_data = request.data
        execution_data = json.loads(request_data["data"])

        execution = execution_data["execution"]

        if execution == "createModule":
            execute = self.createModule(execution_data, **kwargs)
        elif execution == "createModel":
            execute = self.createModel(execution_data, **kwargs)
        elif execution == "updateModel":
            execute = self.updateModel(execution_data, **kwargs)
        elif execution == "createCrud":
            execute = self.createCrud(execution_data, **kwargs)
        elif execution == "updateCrudTable":
            execute = self.updateCrudTable(execution_data, **kwargs)
        elif execution == "createUser":
            execute = self.createUser(execution_data, **kwargs)
        elif execution == "createRole":
            execute = self.createRole(execution_data, **kwargs)
        elif execution == "mapRole":
            execute = self.mapRole(execution_data, **kwargs)
        elif execution == "mapPolicy":
            execute = self.mapPolicy(execution_data, **kwargs)
        elif execution == "createCustomCode":
            execute = self.createCustomCode(execution_data, **kwargs)
        elif execution == "setupFrame":
            execute = self.setupFrame(execution_data, **kwargs)

        # assist_msg = 'Executed Successfully!'
        return get_api_response(
            success=execute[0], response_content={"message": execute[1]}, status=200
        )

    def createModule(self, execution_data, **kwargs):
        app_obj = self.get_app_obj(**kwargs)
        module_path = (
            str(settings.BASE_DIR)
            + f"/workspaces/{app_obj.name}/"
            + execution_data["dir"]
        )
        try:
            try:
                os.mkdir(module_path)
                settings_path = self.get_settings_path(**kwargs)
                with open(settings_path, "w") as f:
                    f.write(json.dumps(execution_data["settings.json"], indent=4))
                return (True, "Succesfully executed")
            except FileExistsError:
                return (False, f"Directory {module_path} already exists")
            except OSError as error:
                return (False, f"Error creating directory {module_path}: {error}")
        except Exception as e:
            os.rmdir(module_path)
            return (False, str(e))

    def createModel(self, execution_json, **kwargs):
        app_obj = self.get_app_obj(**kwargs)
        model_path = (
            str(settings.BASE_DIR)
            + f"/workspaces/{app_obj.name}/{execution_json['module']}/models.py"
        )
        with open(model_path, "a") as f:
            f.write(execution_json["models.py"])
        return (True, "Succesfully executed")

    def updateModel(self, execution_json, **kwargs):
        app_obj = self.get_app_obj(**kwargs)
        model_path = (
            str(settings.BASE_DIR)
            + f"/workspaces/{app_obj.name}/{execution_json['module']}/models.py"
        )
        with open(model_path, "w") as f:
            f.write(execution_json["models.py"])
        return (True, "Succesfully executed")

    def createCrud(self, execution_json, **kwargs):
        app_obj = self.get_app_obj(**kwargs)
        views_path = (
            str(settings.BASE_DIR)
            + f"/workspaces/{app_obj.name}/{execution_json['module']}/views.py"
        )
        forms_path = (
            str(settings.BASE_DIR)
            + f"/workspaces/{app_obj.name}/{execution_json['module']}/forms.py"
        )
        tables_path = (
            str(settings.BASE_DIR)
            + f"/workspaces/{app_obj.name}/{execution_json['module']}/tables.py"
        )
        urls_path = (
            str(settings.BASE_DIR)
            + f"/workspaces/{app_obj.name}/{execution_json['module']}/urls.py"
        )
        with open(views_path, "a") as f:
            f.write(execution_json["views.py"])
        with open(forms_path, "a") as f:
            f.write(execution_json["forms.py"])
        with open(tables_path, "a") as f:
            f.write(execution_json["tables.py"])
        with open(urls_path, "a") as f:
            f.write(execution_json["urls.py"])
        policy = execution_json["policy"]
        PolicyModel.objects.get_or_create(
            name=policy[0]["name"], statement=policy[0]["statement"], is_active=True
        )
        return (True, "Succesfully executed")

    def updateCrudTable(self, execution_json, **kwargs):
        app_obj = self.get_app_obj(**kwargs)
        tables_path = (
            str(settings.BASE_DIR)
            + f"/workspaces/{app_obj.name}/{execution_json['module']}/tables.py"
        )

        with open(tables_path, "w") as f:
            f.write(execution_json["tables.py"])

        return (True, "Succesfully executed")

    def createUser(self, execution_json, **kwargs):
        try:
            if AppUserModel.objects.filter(email=execution_json["email"]).exists():
                return (False, f"This email ID is already taken")
            user = AppUserModel.objects.create(
                email=execution_json["email"],
                name=execution_json["name"],
                is_active=True,
            )
            user.set_password(execution_json["password"])
            user.save()
            return (True, "Succesfully executed")
        except Exception as e:
            return (False, f"Error encountered while creating user: {str(e)}")

    def createRole(self, execution_json, **kwargs):
        if UserRoleModel.objects.filter(
            name__icontains=execution_json["role_name"]
        ).exists():
            return (False, f"User Role with this name already exists!")
        role = UserRoleModel.objects.create(
            name=execution_json["role_name"], is_active=True
        )
        return (True, "Succesfully executed")

    def mapRole(self, execution_json, **kwargs):
        user = AppUserModel.objects.filter(
            email__icontains=execution_json["email"]
        ).first()
        if not user:
            return (
                False,
                f"There is no user with the provided email ID {execution_json['email']}",
            )
        role = UserRoleModel.objects.filter(
            name__icontains=execution_json["role_name"]
        ).first()
        if not role:
            return (
                False,
                f"There is no role matching the name provided {execution_json['role_name']}",
            )
        user.roles.add(role)
        user.save()
        return (True, "Succesfully executed")

    def mapPolicy(self, execution_json, **kwargs):
        role = UserRoleModel.objects.filter(
            name__icontains=execution_json["role_name"]
        ).first()
        if not role:
            return (
                False,
                f"There is no role with the provided name {execution_json['role_name']}",
            )
        policy = PolicyModel.objects.filter(
            name__icontains=execution_json["policy"]
        ).first()
        if not policy:
            return (
                False,
                f"There is no policy matching the name provided policy name {execution_json['policy']}",
            )
        role.policies.add(policy)
        role.save()
        return (True, "Succesfully executed")

    def setupFrame(self, execution_json, **kwargs):
        app_obj = self.get_app_obj(**kwargs)
        frame_mod_path = f"workspaces.{app_obj.name}.packages.frame.configure.models"
        frame_mod = importlib.import_module(frame_mod_path)

        frame_model_class = frame_mod.FramesModel
        user_role = UserRoleModel.objects.filter(
            name__iexact=execution_json["role_name"]
        ).first()
        if not user_role:
            return (False, "There is no role with the provided role name")

        if frame_model_class.objects.filter(user_role=user_role).exists():
            return (False, f"Frames already exists for {user_role.name}")

        frame_model_class.objects.create(
            user_role=user_role, config=execution_json["frame_config"]
        )

        return (True, "Succesfully executed")

    def createCustomCode(self, execution_json, **kwargs):
        app_obj = self.get_app_obj(**kwargs)
        views_path = (
            str(settings.BASE_DIR)
            + f"/workspaces/{app_obj.name}/{execution_json['module']}/views.py"
        )
        urls_path = (
            str(settings.BASE_DIR)
            + f"/workspaces/{app_obj.name}/{execution_json['module']}/urls.py"
        )
        template_path = (
            str(settings.BASE_DIR)
            + f"/workspaces/{app_obj.name}/{execution_json['module']}/templates/{execution_json['template_name']}"
        )
        with open(views_path, "a") as f:
            f.write(execution_json["views.py"])
        with open(urls_path, "a") as f:
            f.write(execution_json["urls.py"])
        with open(template_path, "a") as f:
            f.write(execution_json["template.html"])
        policy = execution_json["policy"]
        PolicyModel.objects.get_or_create(
            name=policy[0]["name"], statement=policy[0]["statement"], is_active=True
        )
        return (True, "Succesfully executed")
