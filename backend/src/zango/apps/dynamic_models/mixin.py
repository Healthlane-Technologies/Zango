from django.core.exceptions import ValidationError

from zango.apps.appauth.models import AppUserModel, UserRoleModel


class DynamicModelMixin:
    """
    Mixin class providing dynamic model functionalities and utility methods.
    """

    def create_app_user(
        self,
        name,
        email,
        mobile,
        password,
        role_name,
        force_password_reset=True,
        require_verification=True,
    ):
        """
        Creates a new app user and associates them with the current object, mapping them to the specified role.

        Args:
            name (str): The name of the user.
            email (str): The email address of the user.
            mobile (str): The mobile number of the user.
            password (str): The password for the user account.
            role_name (str): The name of the role to be assigned to the user.
            force_password_reset (bool): If True, the user will be required to reset their password on first login. Default is True.
            require_verification (bool): If True, the user will be required to verify their account. Default is True.

        Returns:
            dict: A dictionary containing:
                - "success" (bool): Indicates if the user creation was successful.
                - "message" (str): A message providing additional details about the operation.
                - "app_user" (AppUserModel or None): The created user instance if successful, otherwise None.

        Raises:
            ValidationError: If the specified role does not exist.

        Notes:
            The `app_objects` mapping is created with the given role with the current object.
        """
        app_objects = {}
        role_ids = []

        try:
            user_role = UserRoleModel.objects.get(name=role_name)
            app_objects.update({str(user_role.id): str(self.object_uuid)})
            role_ids.append(user_role.id)
        except UserRoleModel.DoesNotExist:
            raise ValidationError(f"User Role {role_name} does not exist")

        return AppUserModel.create_user(
            name,
            email,
            mobile,
            password,
            role_ids,
            force_password_reset=force_password_reset,
            require_verification=require_verification,
            app_objects=app_objects,
        )
