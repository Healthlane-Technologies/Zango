import json
import traceback

from allauth.socialaccount.models import SocialApp
from django_celery_results.models import TaskResult

from django.core.exceptions import ValidationError
from django.db import connection
from django.db.models import Q
from django.utils.decorators import method_decorator

from zango.apps.appauth.mixin import UserAuthConfigValidationMixin
from zango.apps.appauth.models import AppUserModel, UserRoleModel
from zango.apps.dynamic_models.workspace.base import Workspace
from zango.apps.permissions.models import PolicyModel
from zango.apps.shared.tenancy.models import TenantModel, ThemesModel
from zango.apps.shared.tenancy.utils import DATEFORMAT, DATETIMEFORMAT, TIMEZONES
from zango.core.api import (
    TenantMixin,
    ZangoGenericPlatformAPIView,
    get_api_response,
)
from zango.core.api.utils import ZangoAPIPagination
from zango.core.common_utils import set_app_schema_path
from zango.core.permissions import IsPlatformUserAllowedApp
from zango.core.utils import (
    get_country_code_for_tenant,
    get_search_columns,
    validate_phone,
)

from .serializers import (
    AppUserModelSerializerModel,
    SocialAppSerializer,
    TenantSerializerModel,
    ThemeModelSerializer,
    UserRoleSerializerModel,
)
from .utils import extract_app_details_from_zip


class AppViewAPIV1(ZangoGenericPlatformAPIView):
    def get(self, request, *args, **kwargs):
        try:
            action = request.GET.get("action")
            if action == "get_app_creation_status":
                task_id = request.GET.get("task_id")
                try:
                    task = TaskResult.objects.get(task_id=task_id)
                    if task.status == "SUCCESS":
                        result = json.loads(task.result)
                        if result["result"] == "success":
                            return get_api_response(
                                True,
                                {
                                    "message": "App created successfully",
                                    "deployed": True,
                                    "status": "Deployed",
                                },
                                200,
                            )
                        else:
                            return get_api_response(
                                False,
                                {
                                    "message": "App creation failed",
                                    "deployed": False,
                                    "status": "Failed",
                                    "error": result["error"],
                                },
                                500,
                            )
                except TaskResult.DoesNotExist:
                    return get_api_response(
                        True,
                        {
                            "message": "App creating",
                            "deployed": False,
                            "status": "Staged",
                        },
                        200,
                    )
            platform_user = request.user.platform_user
            apps = TenantModel.objects.all().exclude(schema_name="public")

            # Returning Only allowed apps
            if not platform_user.is_superadmin:
                apps = platform_user.apps

            serializer = TenantSerializerModel(apps, many=True)
            success = True
            response = {
                "apps": serializer.data,
                "message": "All apps fetched successfully",
            }
            status = 200
        except Exception as e:
            success = False
            response = {"message": str(e)}
            status = 500

        return get_api_response(success, response, status)

    def post(self, request, *args, **kwargs):
        try:
            data = request.data
            app_template = data.get("app_template", None)
            app_template_name = None
            run_migrations = False
            if app_template:
                app_template_name = str(app_template).split(".")[0]
                _, app_name, run_migrations = extract_app_details_from_zip(app_template)
                data.update(
                    {
                        "name": app_name,
                        "app_template": app_template,
                    }
                )
            app, task_id = TenantModel.create(
                name=data["name"],
                schema_name=data["name"],
                app_template_name=app_template_name,
                description=data.get("description"),
                app_template=app_template,
                tenant_type="app",
                status="staged",
                run_migrations=run_migrations,
            )
            result = {
                "message": "App Launch Initiated Successfully",
                "app_uuid": str(app.uuid),
                "task_id": task_id,
            }
            status = 200
            success = True
        except Exception as e:
            import traceback

            traceback.print_exc()
            # logger.error(traceback.format_exc())
            result = {"message": str(e)}
            status = 500
            success = False
        return get_api_response(success, result, status)


class AppDetailViewAPIV1(ZangoGenericPlatformAPIView, TenantMixin):
    permission_classes = (IsPlatformUserAllowedApp,)

    def get_dropdown_options(self):
        options = {}
        options["timezones"] = [{"id": t[0], "label": t[1]} for t in TIMEZONES]
        options["datetime_formats"] = [
            {"id": d[0], "label": d[1]} for d in DATETIMEFORMAT
        ]
        options["date_formats"] = [{"id": d[0], "label": d[1]} for d in DATEFORMAT]
        return options

    def get(self, request, *args, **kwargs):
        try:
            tenant = self.get_tenant(**kwargs)
            include_dropdown_options = request.GET.get("include_dropdown_options")
            serializer = TenantSerializerModel(tenant)
            success = True
            response = {"app": serializer.data}
            if include_dropdown_options:
                response["dropdown_options"] = self.get_dropdown_options()

            status = 200
        except Exception as e:
            success = False
            response = {"message": str(e)}
            status = 500

        return get_api_response(success, response, status)

    def get_branch(self, config, key, default=None):
        branch = config.get("branch", {}).get(key, default)
        return branch if branch else default

    def put(self, request, *args, **kwargs):
        try:
            obj = self.get_tenant(**kwargs)
            serializer = TenantSerializerModel(
                instance=obj,
                data=request.data,
                partial=True,
                context={"request": request},
            )
            if serializer.is_valid():
                serializer.save()
                success = True
                status_code = 200

                result = {
                    "message": "App Settings Updated Successfully",
                    "app_uuid": str(obj.uuid),
                }
            else:
                success = False
                status_code = 400
                if serializer.errors:
                    error_messages = [
                        error[0] for field_name, error in serializer.errors.items()
                    ]
                    error_message = ", ".join(error_messages)
                else:
                    error_message = "Invalid data"

                result = {"message": error_message}
        except Exception as e:
            success = False
            result = {"message": str(e)}
            status_code = 500

        return get_api_response(success, result, status_code)


@method_decorator(set_app_schema_path, name="dispatch")
class UserRoleViewAPIV1(ZangoGenericPlatformAPIView, ZangoAPIPagination, TenantMixin):
    pagination_class = ZangoAPIPagination
    permission_classes = (IsPlatformUserAllowedApp,)

    def get_dropdown_options(self):
        options = {}
        options["policies"] = [
            {"id": t.id, "label": t.name}
            for t in PolicyModel.objects.all().order_by("-modified_at")
        ]
        return options

    def get_queryset(self, search, columns={}):
        name_field_query_mappping = {
            "name": "name__icontains",
            "attached_policies": "policies__name",
            "is_active": "is_active",
        }
        if columns.get("is_active") == "true":
            columns["is_active"] = True
        elif columns.get("is_active") == "false":
            columns["is_active"] = False
        elif columns.get("is_active") == "" or columns.get("is_active") is None:
            name_field_query_mappping.pop("is_active")
        records = UserRoleModel.objects.all().order_by("-modified_at")
        if search == "" and columns == {}:
            return records
        filters = Q()
        for field_name, query in name_field_query_mappping.items():
            if field_name in columns:
                filters &= Q(**{query: columns.get(field_name)})
            else:
                if search:
                    filters |= Q(**{query: search})
        return records.filter(filters).distinct()

    def get(self, request, *args, **kwargs):
        try:
            include_dropdown_options = request.GET.get("include_dropdown_options")
            search = request.GET.get("search", None)
            columns = get_search_columns(request)
            roles = self.get_queryset(search, columns)
            paginated_roles = self.paginate_queryset(roles, request, view=self)
            tenant = self.get_tenant(**kwargs)
            serializer = UserRoleSerializerModel(
                paginated_roles,
                many=True,
                context={"request": request, "tenant": tenant},
            )
            paginated_roles_data = self.get_paginated_response_data(serializer.data)

            success = True
            response = {
                "roles": paginated_roles_data,
                "message": "All roles fetched successfully",
            }
            if include_dropdown_options:
                response["dropdown_options"] = self.get_dropdown_options()
            status = 200
        except Exception as e:
            traceback.print_exc()
            success = False
            response = {"message": str(e)}
            status = 500

        return get_api_response(success, response, status)

    def post(self, request, *args, **kwargs):
        data = request.data
        tenant = self.get_tenant(**kwargs)
        role_serializer = UserRoleSerializerModel(
            data=data, context={"request": request, "tenant": tenant}
        )
        if role_serializer.is_valid():
            success = True
            status_code = 200
            role = role_serializer.save()
            role.is_active = True
            role.save()
            result = {"message": "User Role Created Successfully", "role_id": role.id}
            if role_serializer.data.get("policies", False):
                tenant = TenantModel.objects.get(uuid=kwargs.get("app_uuid"))
                connection.set_tenant(tenant)
                with connection.cursor() as c:
                    ws = Workspace(connection.tenant, request=None, as_systemuser=True)
                    ws.sync_role_policies()
        else:
            success = False
            status_code = 400
            if role_serializer.errors:
                error_messages = [
                    error[0] for field_name, error in role_serializer.errors.items()
                ]
                error_message = ", ".join(error_messages)
            else:
                error_message = "Invalid data"

            result = {"message": error_message}

        return get_api_response(success, result, status_code)


@method_decorator(set_app_schema_path, name="dispatch")
class UserRoleDetailViewAPIV1(ZangoGenericPlatformAPIView, TenantMixin):
    permission_classes = (IsPlatformUserAllowedApp,)

    def get_obj(self, **kwargs):
        obj = UserRoleModel.objects.get(id=kwargs.get("role_id"))
        return obj

    def get(self, request, *args, **kwargs):
        try:
            obj = self.get_obj(**kwargs)
            tenant = self.get_tenant(**kwargs)
            serializer = UserRoleSerializerModel(
                obj,
                context={"request": request, "tenant": tenant},
            )
            success = True
            response = {"role": serializer.data}
            status = 200
        except Exception as e:
            success = False
            response = {"message": str(e)}
            status = 500

        return get_api_response(success, response, status)

    def put(self, request, *args, **kwargs):
        try:
            obj = self.get_obj(**kwargs)
            tenant = self.get_tenant(**kwargs)
            serializer = UserRoleSerializerModel(
                instance=obj,
                data=request.data,
                partial=True,
                context={"request": request, "tenant": tenant},
            )
            if serializer.is_valid():
                serializer.save()
                success = True
                status_code = 200
                result = {
                    "message": "User Role Updated Successfully",
                    "role_id": obj.id,
                }
                tenant = TenantModel.objects.get(uuid=kwargs.get("app_uuid"))
                connection.set_tenant(tenant)
                with connection.cursor() as c:
                    ws = Workspace(connection.tenant, request=None, as_systemuser=True)
                    ws.sync_role_policies()
            else:
                success = False
                status_code = 400
                if serializer.errors:
                    error_messages = [
                        error[0] for field_name, error in serializer.errors.items()
                    ]
                    error_message = ", ".join(error_messages)
                else:
                    error_message = "Invalid data"

                result = {"message": error_message}
        except Exception as e:
            import traceback

            traceback.print_exc()

            success = False
            result = {"message": str(e)}
            status_code = 500

        return get_api_response(success, result, status_code)


@method_decorator(set_app_schema_path, name="dispatch")
class UserViewAPIV1(
    ZangoGenericPlatformAPIView,
    ZangoAPIPagination,
    TenantMixin,
    UserAuthConfigValidationMixin,
):
    pagination_class = ZangoAPIPagination
    permission_classes = (IsPlatformUserAllowedApp,)

    def get_dropdown_options(self):
        options = {}
        options["roles"] = [
            {"id": t.id, "label": t.name}
            for t in UserRoleModel.objects.all().exclude(
                name__in=["AnonymousUsers", "SystemUsers"]
            )
        ]
        return options

    def get_queryset(self, search, columns={}):
        name_field_query_mappping = {
            "user_name": "name__icontains",
            "email": "email__icontains",
            "user_id": "id__icontains",
            "mobile": "mobile__icontains",
            "roles_access": "roles__name__icontains",
            "is_active": "is_active",
        }
        if columns.get("is_active") == "true":
            columns["is_active"] = True
        elif columns.get("is_active") == "false":
            columns["is_active"] = False
        elif columns.get("is_active") == "" or columns.get("is_active") is None:
            name_field_query_mappping.pop("is_active")
        records = AppUserModel.objects.all().order_by("-modified_at")
        if search == "" and columns == {}:
            return records
        filters = Q()
        for field_name, query in name_field_query_mappping.items():
            if field_name in columns:
                filters &= Q(**{query: columns[field_name]})
            else:
                if search:
                    filters |= Q(**{query: search})
        return records.filter(filters).distinct()

    def get(self, request, *args, **kwargs):
        try:
            include_dropdown_options = request.GET.get("include_dropdown_options")
            search = request.GET.get("search", None)
            columns = get_search_columns(request)
            app_users = self.get_queryset(search, columns)
            app_users = self.paginate_queryset(app_users, request, view=self)
            serializer = AppUserModelSerializerModel(
                app_users,
                many=True,
                context={"request": request, "tenant": self.get_tenant(**kwargs)},
            )
            app_users_data = self.get_paginated_response_data(serializer.data)
            app_tenant = self.get_tenant(**kwargs)
            success = True
            response = {
                "users": app_users_data,
                "message": "Users fetched successfully",
                "pn_country_code": get_country_code_for_tenant(app_tenant),
            }
            if include_dropdown_options:
                response["dropdown_options"] = self.get_dropdown_options()
            status = 200

        except Exception as e:
            success = False
            response = {"message": str(e)}
            status = 500

        return get_api_response(success, response, status)

    def validate_password_passed(self, tenant_auth_config, user_auth_config, password):
        login_methods = tenant_auth_config.get("login_methods")
        if login_methods.get("password", {}).get("enabled", False):
            if not password:
                raise ValidationError("Password is required for password based login")

    def post(self, request, *args, **kwargs):
        data = request.data
        try:
            role_ids = data.getlist("roles")
            if data.get("mobile"):
                if not validate_phone(data["mobile"]):
                    result = {"message": "Invalid mobile number"}
                    return get_api_response(False, result, 400)
            app_tenant = self.get_tenant(**kwargs)
            creation_result = AppUserModel.create_user(
                name=data["name"],
                email=data["email"],
                mobile=data["mobile"],
                password=data["password"],
                role_ids=role_ids,
                require_verification=False,
                tenant=app_tenant,
            )
            success = creation_result["success"]
            result = {"message": creation_result["message"]}
            status = 200 if success else 400

        except ValidationError as e:
            result = {"message": str(e)}
            status = 400
            success = False

        except Exception as e:
            result = {"message": str(e)}
            status = 500
            success = False
        return get_api_response(success, result, status)


@method_decorator(set_app_schema_path, name="dispatch")
class UserDetailViewAPIV1(ZangoGenericPlatformAPIView, TenantMixin):
    permission_classes = (IsPlatformUserAllowedApp,)

    def get_obj(self, **kwargs):
        obj = AppUserModel.objects.get(id=kwargs.get("user_id"))
        return obj

    def get(self, request, *args, **kwargs):
        try:
            obj = self.get_obj(**kwargs)
            serializer = AppUserModelSerializerModel(obj)
            success = True
            response = {
                "user": serializer.data,
                "pn_country_code": f"+{obj.mobile.country_code}",
            }
            status = 200
        except Exception as e:
            success = False
            response = {"message": str(e)}
            status = 500

        return get_api_response(success, response, status)

    def put(self, request, *args, **kwargs):
        data = request.data
        try:
            if data.get("mobile"):
                if not validate_phone(data["mobile"]):
                    result = {"message": "Invalid mobile number"}
                    return get_api_response(False, result, 400)
            obj = self.get_obj(**kwargs)
            update_result = AppUserModel.update_user(
                obj, request.data, tenant=self.get_tenant(**kwargs)
            )
            success = update_result["success"]
            message = update_result["message"]
            status_code = 200 if success else 400
            if status_code != 400:
                if request.data.get("auth_config"):
                    auth_config = json.loads(request.data["auth_config"])
                    ser = AppUserModelSerializerModel(
                        instance=obj, data={"auth_config": auth_config}, partial=True
                    )
                    if ser.is_valid():
                        ser.save()
                    else:
                        if ser.errors:
                            error_messages = [
                                error[0] for field_name, error in ser.errors.items()
                            ]
                            error_message = ", ".join(error_messages)
                        else:
                            error_message = "Invalid data"

                        result = {"message": error_message}
                        return get_api_response(False, result, 400)
            result = {
                "message": message,
                "user_id": obj.id,
            }
        except Exception as e:
            success = False
            result = {"message": str(e)}
            status_code = 500

        return get_api_response(success, result, status_code)


class ThemeViewAPIV1(ZangoGenericPlatformAPIView):
    permission_classes = (IsPlatformUserAllowedApp,)

    def get_app_tenant(self):
        tenant_obj = TenantModel.objects.get(uuid=self.kwargs["app_uuid"])
        return tenant_obj

    def get(self, request, *args, **kwargs):
        try:
            app_tenant = self.get_app_tenant()
            themes = ThemesModel.objects.filter(tenant=app_tenant).order_by(
                "-modified_at"
            )

            serializer = ThemeModelSerializer(themes, many=True)

            success = True
            response = {
                "themes": serializer.data,
                "message": "All themes fetched successfully",
            }
            status = 200
        except Exception as e:
            success = False
            response = {"message": str(e)}
            status = 500

        return get_api_response(success, response, status)

    def post(self, request, *args, **kwargs):
        data = request.data
        data._mutable = True
        app_tenant = self.get_app_tenant()
        data["tenant"] = app_tenant.id
        data._mutable = False
        theme_serializer = ThemeModelSerializer(
            data=data, context={"app_tenant": app_tenant}
        )
        if theme_serializer.is_valid():
            success = True
            status_code = 200
            theme = theme_serializer.save()
            result = {"message": "Theme Created Successfully", "theme_id": theme.id}
        else:
            success = False
            status_code = 400
            print(theme_serializer.errors)
            if theme_serializer.errors:
                error_messages = [
                    error[0] for field_name, error in theme_serializer.errors.items()
                ]
                error_message = ", ".join(error_messages)
            else:
                error_message = "Invalid data"

            result = {"message": error_message}

        return get_api_response(success, result, status_code)


class ThemeDetailViewAPIV1(ZangoGenericPlatformAPIView):
    permission_classes = (IsPlatformUserAllowedApp,)

    def get_obj(self, **kwargs):
        obj = ThemesModel.objects.get(
            tenant__uuid=kwargs.get("app_uuid"), id=kwargs.get("theme_id")
        )
        return obj

    def get_app_tenant(self):
        tenant_obj = TenantModel.objects.get(uuid=self.kwargs["app_uuid"])
        return tenant_obj

    def get(self, request, *args, **kwargs):
        try:
            obj = self.get_obj(**kwargs)
            serializer = ThemeModelSerializer(obj)
            success = True
            response = {"theme": serializer.data}
            status = 200
        except Exception as e:
            success = False
            response = {"message": str(e)}
            status = 500

        return get_api_response(success, response, status)

    def put(self, request, *args, **kwargs):
        try:
            obj = self.get_obj(**kwargs)
            data = request.data
            data._mutable = True
            app_tenant = self.get_app_tenant()
            data["tenant"] = app_tenant.id
            data._mutable = False

            serializer = ThemeModelSerializer(instance=obj, data=data, partial=True)
            if serializer.is_valid():
                serializer.save()
                success = True
                status_code = 200
                result = {
                    "message": "Theme Updated Successfully",
                    "theme_id": obj.id,
                }
            else:
                success = False
                status_code = 400
                if serializer.errors:
                    error_messages = [
                        error[0] for field_name, error in serializer.errors.items()
                    ]
                    error_message = ", ".join(error_messages)
                else:
                    error_message = "Invalid data"

                result = {"message": error_message}
        except Exception as e:
            success = False
            result = {"message": str(e)}
            status_code = 500

        return get_api_response(success, result, status_code)


@method_decorator(set_app_schema_path, name="dispatch")
class OAuthProvidersViewAPIV1(ZangoGenericPlatformAPIView):
    permission_classes = (IsPlatformUserAllowedApp,)

    def get(self, request, *args, **kwargs):
        try:
            # Since set_app_schema_path handles tenant isolation,
            # we can directly query SocialApp objects
            providers = SocialApp.objects.all()
            serializer = SocialAppSerializer(providers, many=True)

            # Transform the data to match frontend expectations
            oauth_providers = {}
            for provider_data in serializer.data:
                provider_name = provider_data["provider"]
                oauth_providers[provider_name] = {
                    "enabled": provider_data.get("enabled", False),
                    "client_id": provider_data.get("client_id", ""),
                    "client_secret": "",  # Don't send secret in GET response
                }

            success = True
            response = {"oauth_providers": oauth_providers}
            status = 200
        except Exception as e:
            success = False
            response = {"message": str(e)}
            status = 500

        return get_api_response(success, response, status)

    def put(self, request, *args, **kwargs):
        try:
            # Parse oauth_providers data from request
            oauth_providers_str = request.data.get("oauth_providers")
            if not oauth_providers_str:
                return get_api_response(
                    False, {"message": "oauth_providers data is required"}, 400
                )

            try:
                oauth_providers = json.loads(oauth_providers_str)
            except json.JSONDecodeError:
                return get_api_response(
                    False, {"message": "Invalid JSON format for oauth_providers"}, 400
                )

            success_count = 0
            errors = []

            # Process each provider
            for provider_name, provider_config in oauth_providers.items():
                try:
                    enabled = provider_config.get("enabled", False)
                    client_id = provider_config.get("client_id", "")
                    client_secret = provider_config.get("client_secret", "")

                    if enabled and client_id and client_secret:
                        # Create or update the provider
                        social_app, created = SocialApp.objects.update_or_create(
                            provider=provider_name,
                            defaults={
                                "name": f"{provider_name.title()}",
                                "client_id": client_id,
                                "secret": client_secret,
                                "enabled": True,
                                "settings": {},
                            },
                        )
                        success_count += 1

                    else:
                        # Handle disabled providers or providers without credentials
                        try:
                            social_app = SocialApp.objects.get(provider=provider_name)
                            if not enabled:
                                # If provider exists but is disabled, update enabled field to False
                                social_app.enabled = False
                                social_app.save()
                            elif enabled and (not client_id or not client_secret):
                                # If enabled but missing credentials, disable it
                                social_app.enabled = False
                                social_app.save()
                            success_count += 1
                        except SocialApp.DoesNotExist:
                            # If disabled and doesn't exist, nothing to do
                            if not enabled:
                                pass
                            else:
                                # If trying to enable but missing credentials, create disabled entry
                                if not client_id or not client_secret:
                                    SocialApp.objects.create(
                                        provider=provider_name,
                                        name=f"{provider_name.title()}",
                                        client_id=client_id,
                                        secret=client_secret,
                                        enabled=False,
                                        settings={},
                                    )
                                    success_count += 1

                except Exception as provider_error:
                    errors.append(f"{provider_name}: {str(provider_error)}")

            if errors:
                return get_api_response(
                    False, {"message": f"Errors occurred: {'; '.join(errors)}"}, 400
                )

            success = True
            response = {
                "message": f"OAuth providers updated successfully. {success_count} providers processed."
            }
            status = 200

        except Exception as e:
            import traceback

            traceback.print_exc()
            success = False
            response = {"message": str(e)}
            status = 500

        return get_api_response(success, response, status)
