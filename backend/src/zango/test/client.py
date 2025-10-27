from importlib import import_module
from typing import List, Optional, overload

from django_tenants.utils import schema_context

from django.conf import settings
from django.contrib.auth import authenticate, login, logout
from django.http import HttpRequest, SimpleCookie
from django.test import Client, RequestFactory

from zango.apps.appauth.models import AppUserModel, UserRoleModel
from zango.apps.permissions.models import PolicyModel
from zango.core.utils import get_mock_request
from zango.middleware.tenant import ZangoTenantMainMiddleware


class BaseZangoRequestFactory:
    """
    Base class for creating test requests with tenant context.
    Handles tenant-specific request creation and user/role management.
    """

    tm = ZangoTenantMainMiddleware(lambda r: r)

    def __init__(self, tenant, **defaults):
        """Initialize with tenant and optional default request parameters."""
        super().__init__(**defaults)
        self.tenant = tenant
        self.user = None

    def generic(self, *args, **kwargs):
        """Create a generic request with tenant context."""
        kwargs.setdefault("HTTP_HOST", self.tenant.get_primary_domain().domain)
        request = super().generic(*args, **kwargs)
        request.tenant = self.tenant
        if request.tenant.tenant_type == "app":
            request.user = self.user
        return request

    @overload
    @classmethod
    def create_roles(cls, tenant, *, names: List[str]) -> List[int]: ...

    @overload
    @classmethod
    def create_roles(cls, tenant, *, ids: List[int]) -> List[int]: ...

    @classmethod
    def create_roles(
        cls,
        tenant,
        *,
        names: Optional[List[str]] = None,
        ids: Optional[List[int]] = None,
    ) -> List[int]:
        """Create a role with basic permissions."""
        with schema_context(tenant.schema_name):
            ids = []
            for name in names:
                role, created = UserRoleModel.objects.get_or_create(name=name)
                ids.append(role.id)
            return ids

    @classmethod
    def get_role_id(cls, tenant, name: str) -> int:
        """Get a role id."""
        with schema_context(tenant.schema_name):
            role = UserRoleModel.objects.get(name=name)
            return role.id

    @classmethod
    def create_policies(cls, names: List[str]) -> List[int]:
        """Create a policy."""
        with schema_context(cls.tenant.schema_name):
            ids = []
            for name in names:
                policy, created = PolicyModel.objects.get_or_create(name=name)
                ids.append(policy.id)
            return ids

    @classmethod
    def delete_policies(cls, names: List[str]) -> None:
        """Delete a policy."""
        with schema_context(cls.tenant.schema_name):
            for name in names:
                policy = PolicyModel.objects.get(name=name)
                if policy:
                    policy.delete()

    @classmethod
    def create_user(
        cls,
        tenant,
        name: str = "John Doe",
        email: str = "admin@zelthy.com",
        mobile: str = "0000000000",
        password: str = "Zelthy@123",
        roles: Optional[List[str]] = None,
        **extra_fields,
    ) -> AppUserModel:
        """Create a test user with the given parameters."""
        roles = roles or []

        with schema_context(tenant.schema_name):
            if not roles:
                admin_role = cls.create_admin_role(tenant)
                role_ids = [admin_role.id]
            else:
                role_ids = cls.create_roles(tenant, names=roles)

            user_data = {
                "name": name,
                "email": email,
                "mobile": mobile,
                "password": password,
                "role_ids": role_ids,
                "require_verification": False,
                "force_password_reset": False,
                **extra_fields,
            }

            result = AppUserModel.create_user(**user_data)
            if not result["success"]:
                raise RuntimeError(f"Failed to create user: {result['message']}")

            return result["app_user"]

    @staticmethod
    def create_admin_role(tenant, name: str = "Admin") -> UserRoleModel:
        """Create an admin role with basic permissions."""
        with schema_context(tenant.schema_name):
            admin_role = UserRoleModel.objects.create(name=name)

            # Add default allow policy if it exists
            allow_policy = PolicyModel.objects.filter(name="AllowFromAnywhere").first()

            if allow_policy:
                admin_role.policies.add(allow_policy)
                admin_role.save()

            return admin_role


class ZangoRequestFactory(BaseZangoRequestFactory, RequestFactory):
    """RequestFactory with Zango tenant support."""

    pass


class ZangoClient(BaseZangoRequestFactory, Client):
    """Test client with Zango tenant and authentication support."""

    def __init__(self, tenant, **defaults):
        """Initialize with tenant and optional default request parameters."""
        super().__init__(tenant, **defaults)
        self._session = None

    @property
    def session(self):
        """Lazy session initialization."""
        if self._session is None:
            engine = import_module(settings.SESSION_ENGINE)
            self._session = engine.SessionStore()
        return self._session

    def logout(self) -> None:
        """Log out the user by removing the cookies and session object."""
        if hasattr(self, "user"):
            request = HttpRequest()
            request.session = self.session
            request.user = self.user
            logout(request)
            self.user = None
        self.cookies = SimpleCookie()

    def _login(self, user, backend: str = None) -> None:
        """Log in the specified user."""
        request = get_mock_request(session=self.session)
        login(request, user, backend)
        request.session.save()
        self._set_session_cookie()

    def login(self, username: str, password: str) -> bool:
        """Authenticate and log in a user with the given credentials."""
        request = get_mock_request(session=self.session, tenant=self.tenant)
        user = authenticate(request, username=username, password=password)

        if user:
            self._login(user)
            self.user = user
            return True
        return False

    def _set_session_cookie(self) -> None:
        """Set the session cookie in the client."""
        session_cookie = settings.SESSION_COOKIE_NAME
        self.cookies[session_cookie] = self.session.session_key
        self.cookies[session_cookie].update(
            {
                "max-age": None,
                "path": "/",
                "domain": settings.SESSION_COOKIE_DOMAIN,
                "secure": settings.SESSION_COOKIE_SECURE or None,
                "expires": None,
            }
        )


class AuthenticatedTestClient(ZangoClient):
    """Test client with authentication helpers for testing authenticated endpoints."""

    def __init__(
        self,
        tenant,
        user=None,
        password: str = "Zelthy@123",
        role_name: str = None,
        **user_kwargs,
    ):
        """
        Initialize with optional user and authentication details.

        Args:
            tenant: The tenant to use for the test client
            user: Optional user to authenticate as (will be created if not provided)
            password: Password for authentication (default: "Zelthy@123")
            role_name: Optional role name to assign to the user
            **user_kwargs: Additional arguments to pass when creating a new user
        """
        super().__init__(tenant)
        self._password = password
        self.tenant = tenant

        if user is not None:
            self.authenticate(user, role_name=role_name, password=password)
        elif user_kwargs:
            self.create_and_authenticate_user(role_name=role_name, **user_kwargs)

    def authenticate(
        self, user, role_name: str = None, password: str = None
    ) -> "AuthenticatedTestClient":
        """
        Authenticate the test client with the given user.

        Args:
            user: The user to authenticate as
            role_name: Optional role name to set in the session
            password: Optional password (defaults to instance password)

        Returns:
            self for method chaining

        Raises:
            ValueError: If authentication fails
        """
        self.user = user
        password = password or self._password

        if not self.login(username=user.email, password=password):
            raise ValueError(f"Authentication failed for user {user.email}")

        if role_name:
            self._set_user_role(role_name)

        return self

    def create_and_authenticate_user(
        self, role_name: str = None, **user_kwargs
    ) -> "AuthenticatedTestClient":
        """
        Create and authenticate a new user.

        Args:
            role_name: Optional role name to assign to the user
            **user_kwargs: Arguments to pass to create_user

        Returns:
            self for method chaining
        """
        user = self.create_user(self.tenant, **user_kwargs)
        return self.authenticate(user, role_name=role_name)

    def _set_user_role(self, role_name: str) -> None:
        """Set the user's role in the session."""
        if not hasattr(self, "user") or not self.user:
            return

        with schema_context(self.tenant.schema_name):
            role_id = (
                self.user.roles.filter(name=role_name)
                .values_list("id", flat=True)
                .first()
            )

            if role_id is not None:
                self.session["role_id"] = role_id
                self.session.save()
