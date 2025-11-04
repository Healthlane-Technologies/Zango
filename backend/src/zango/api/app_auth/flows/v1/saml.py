from datetime import timedelta

from allauth.account.models import EmailAddress
from allauth.socialaccount.helpers import complete_social_login
from allauth.socialaccount.models import SocialAccount, SocialLogin
from allauth.socialaccount.providers.base.constants import AuthProcess
from rest_framework.views import APIView

from django.contrib import messages
from django.core import signing
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt

from zango.apps.appauth.models import AppUserModel, SAMLModel, SAMLRequestId
from zango.apps.appauth.saml.utils import SAMLLoginMixin
from zango.core.api import get_api_response


class SAMLLoginViewV1(APIView, SAMLLoginMixin):
    def get(self, request, *args, **kwargs):
        action = request.GET.get("action", "")
        if action == "fetch_config":
            saml_config = SAMLModel.objects.all()
            if saml_config:
                saml_data = {i.id: i.label for i in saml_config}
                return get_api_response(True, saml_data, 200)
            return get_api_response(False, "No saml config", 400)

    def post(self, request, *args, **kwargs):
        saml_config = SAMLModel.objects.filter(id=self.request.data.get("saml_id", 0))
        if saml_config:
            return self.execute_sso_redirect(request, saml_config.first().id)
        else:
            return get_api_response(False, "No saml config", 400)


class ZangoSAMLProvider:
    """
    A minimal provider-like object to interface with allauth's socialaccount system.
    This allows us to use custom SAML authentication while leveraging allauth's
    role selection and authentication flow.
    """

    id = "zango_saml"
    name = "Zango SAML"

    def __init__(self, request, saml_config=None):
        self.request = request
        self.saml_config = saml_config

    @property
    def sub_id(self):
        """Provider identifier for the social account"""
        return self.id


@method_decorator(csrf_exempt, name="dispatch")
class SAMLCallbackViewV1(APIView):
    """
    SAML callback view that integrates with django-allauth's social account flow.

    This view:
    1. Validates the SAML response using Zango's custom SAML validation
    2. Creates a SocialLogin object compatible with allauth
    3. Delegates to allauth's complete_social_login for role selection and authentication
    """

    def get_validation(self):
        """
        Validate the SAML response using existing Zango SAML validation logic.

        Returns:
            dict: Validation result with keys 'is_valid', 'message', and 'email'
        """
        result = {}
        request_id = self.kwargs.get("request_id")
        token = self.kwargs.get("token")
        last_requests = SAMLRequestId.objects.filter(
            request_id=request_id,
            created_at__gte=timezone.now() - timedelta(minutes=10),
        )
        if len(last_requests) > 0:
            try:
                email = signing.loads(token, key=request_id, max_age=300)
                try:
                    cUser = AppUserModel.objects.get(email__iexact=email)
                    if cUser.is_active:
                        result = {"is_valid": True, "message": "", "email": email}
                    else:
                        result = {
                            "is_valid": False,
                            "message": "The user account is not active. Please contact support.",
                            "email": None,
                        }

                except AppUserModel.DoesNotExist:
                    result = {
                        "is_valid": False,
                        "message": "The user is not registered. Please contact support.",
                        "email": None,
                    }
            except signing.SignatureExpired:
                result = {
                    "is_valid": False,
                    "message": "This request has expired. Please try again.",
                    "email": None,
                }
            except signing.BadSignature:
                result = {
                    "is_valid": False,
                    "message": "This request is not valid. Please try again.",
                    "email": None,
                }
        else:
            result = {
                "is_valid": False,
                "message": "This request is not valid or has expired. Please try again.",
                "email": None,
            }
        return result

    def get_email(self):
        """Extract email from the signed token."""
        request_id = self.kwargs.get("request_id")
        token = self.kwargs.get("token")
        try:
            email = signing.loads(token, key=request_id, max_age=300)
            return email
        except Exception:
            return None

    def get_user(self):
        """Get the authenticated user from the database."""
        email = self.get_email()
        if email:
            try:
                user = AppUserModel.objects.get(email__iexact=email)
                return user
            except AppUserModel.DoesNotExist:
                return None
        return None

    def create_sociallogin_from_saml(self, request, user, email):
        """
        Create a SocialLogin object from SAML authentication data.

        This bridges Zango's custom SAML authentication with allauth's social account system.

        Args:
            request: Django request object
            user: AppUserModel instance
            email: User's email address

        Returns:
            SocialLogin: A populated SocialLogin instance ready for allauth processing
        """
        # Create a minimal provider instance
        provider = ZangoSAMLProvider(request)

        # Check if a social account already exists for this user
        try:
            social_account = SocialAccount.objects.get(user=user, provider=provider.id)
        except SocialAccount.DoesNotExist:
            # Create a new social account (unsaved)
            social_account = SocialAccount(
                user=user,
                uid=email,  # Use email as unique identifier
                provider=provider.id,
                extra_data={"email": email, "authentication_method": "saml"},
            )

        # Save the social account
        social_account.save()

        # Create email address object if user has email
        email_addresses = []
        if email:
            email_addresses.append(
                EmailAddress(
                    email=email,
                    verified=True,  # SAML authentication implies email is verified
                    primary=True,
                )
            )

        # Create the SocialLogin object
        sociallogin = SocialLogin(
            user=user,
            account=social_account,
            email_addresses=email_addresses,
            provider=provider,
        )

        # Set state for allauth flow
        sociallogin.state = {
            "process": AuthProcess.LOGIN,
            "scope": "",
            "auth_params": "",
            "headless": True,  # Use allauth headless mode for API responses
        }

        return sociallogin

    def get(self, request, *args, **kwargs):
        """
        Handle the SAML callback GET request.

        Flow:
        1. Validate SAML response using Zango's validation
        2. Get the authenticated user
        3. Create SocialLogin object
        4. Pass to allauth's complete_social_login for role selection and auth
        """
        validation = self.get_validation()

        if not validation["is_valid"]:
            messages.add_message(request, messages.ERROR, validation["message"])
            return get_api_response(
                success=False,
                response_content={
                    "message": validation["message"],
                    "redirect_url": "/login/",
                },
                status=400,
            )

        user = self.get_user()
        if not user:
            messages.add_message(
                request,
                messages.ERROR,
                "Unable to authenticate user. Please contact support.",
            )
            return get_api_response(
                success=False,
                response_content={
                    "message": "Unable to authenticate user.",
                    "redirect_url": "/login/",
                },
                status=400,
            )

        # Create SocialLogin object for allauth integration
        email = validation["email"]
        sociallogin = self.create_sociallogin_from_saml(request, user, email)

        # Delegate to allauth's complete_social_login
        # This will handle:
        # - Saving the social account if it doesn't exist
        # - Role selection (via RoleSelectionStage)
        # - Session setup
        # - MFA if required
        # - Final authentication and redirect
        return complete_social_login(request, sociallogin)
