import json

from typing import Any, Dict, Optional

import requests

from celery import shared_task
from requests.exceptions import RequestException, Timeout

from django.core.exceptions import ObjectDoesNotExist
from django.db import connection

from zango.apps.appauth.models import AppUserModel, UserRoleModel, generate_otp
from zango.apps.shared.tenancy.models import TenantModel
from zango.core.utils import (
    get_auth_priority,
    get_mock_request,
    get_package_url,
)


class OTPConfig:
    """Configuration for OTP sending"""

    def __init__(
        self,
        method: str,
        otp_type: str,
        message: str,
        tenant_id: int,
        email: Optional[str] = None,
        phone: Optional[str] = None,
        user_id: Optional[int] = None,
        request_data: Optional[Dict[str, Any]] = None,
        user_role_id: Optional[int] = None,
        subject: Optional[str] = None,
        code: Optional[str] = None,
        hook: Optional[str] = None,
        config_key: Optional[str] = None,
        extra_data: Optional[Dict[str, Any]] = None,
    ):
        self.method = method
        self.otp_type = otp_type
        self.message = message
        self.tenant_id = tenant_id
        self.email = email
        self.phone = phone
        self.user_id = user_id
        self.request_data = request_data
        self.user_role_id = user_role_id
        self.subject = subject
        self.code = code
        self.hook = hook
        self.config_key = config_key
        self.extra_data = extra_data


class OTPSendError(Exception):
    """Custom exception for OTP sending errors"""

    pass


class OTPService:
    """Service class to handle OTP operations"""

    SUPPORTED_METHODS = {"email", "sms"}
    SUPPORTED_OTP_TYPES = {"two_factor_auth", "login_code", "reset_password"}
    REQUEST_TIMEOUT = 30

    def __init__(self, config: OTPConfig):
        self.config = config
        self.tenant = None
        self.user = None
        self.user_role = None
        self.request = None

    def _validate_config(self) -> None:
        """Validate the configuration parameters"""
        if self.config.method not in self.SUPPORTED_METHODS:
            raise OTPSendError(f"Unsupported method: {self.config.method}")

        if self.config.otp_type not in self.SUPPORTED_OTP_TYPES:
            raise OTPSendError(f"Unsupported OTP type: {self.config.otp_type}")

        if not any([self.config.user_id, self.config.email, self.config.phone]):
            raise OTPSendError(
                "At least one of user_id, email, or phone must be provided"
            )

    def _setup_tenant(self) -> None:
        """Setup tenant and database connection"""
        try:
            self.tenant = TenantModel.objects.get(id=self.config.tenant_id)
            connection.set_tenant(self.tenant)
        except ObjectDoesNotExist:
            raise OTPSendError(f"Tenant with id {self.config.tenant_id} not found")

    def _setup_user(self) -> None:
        """Setup user based on provided identifiers"""
        try:
            if self.config.user_id:
                self.user = AppUserModel.objects.get(id=self.config.user_id)
            elif self.config.email:
                self.user = AppUserModel.objects.get(email=self.config.email)
            elif self.config.phone:
                self.user = AppUserModel.objects.get(mobile=self.config.phone)
        except ObjectDoesNotExist:
            raise OTPSendError("User not found with provided identifiers")

    def _setup_user_role(self) -> None:
        """Setup user role if provided"""
        if self.config.user_role_id:
            try:
                self.user_role = UserRoleModel.objects.get(id=self.config.user_role_id)
            except ObjectDoesNotExist:
                raise OTPSendError(
                    f"User role with id {self.config.user_role_id} not found"
                )

    def _setup_request(self) -> None:
        """Setup mock request object"""
        request_data = self.config.request_data or {}
        self.request = get_mock_request(path=request_data.get("path"))
        self.request.META = {"HTTP_HOST": self.tenant.get_primary_domain()}
        self.request.user = self.user

    def _get_policy_config(self, policy_name: str) -> Dict[str, Any]:
        """Get policy configuration for the given policy name"""
        return get_auth_priority(
            policy=policy_name,
            request=self.request,
            user=self.user,
            user_role=self.user_role,
            tenant=self.tenant,
        )

    def _send_email(self, message: str, url: str) -> None:
        """Send OTP via email"""
        if not self.user.email:
            raise OTPSendError("User email not available")

        payload = {
            "body": message,
            "to": self.user.email,
            "subject": self.config.subject or "OTP Verification",
        }

        # Add config_key if specified
        if self.config.config_key:
            payload["config_key"] = self.config.config_key

        try:
            response = requests.post(url, data=payload, timeout=self.REQUEST_TIMEOUT)
            response.raise_for_status()
        except Timeout:
            raise OTPSendError("Email service request timed out")
        except RequestException as e:
            raise OTPSendError(f"Failed to send email: {str(e)}")

    def _send_sms(self, message: str, url: str) -> None:
        """Send OTP via SMS"""
        if not self.user.mobile:
            raise OTPSendError("User mobile number not available")

        payload = {"message": message, "to": str(self.user.mobile)}

        # Add config_key if specified
        if self.config.config_key:
            payload["key"] = self.config.config_key

        # Add extra_data if specified
        if self.config.extra_data:
            if isinstance(self.config.extra_data, str):
                self.config.extra_data = json.loads(self.config.extra_data)
            payload["extra_data"] = self.config.extra_data

        try:
            response = requests.post(url, data=payload, timeout=self.REQUEST_TIMEOUT)
            response.raise_for_status()
        except Timeout:
            raise OTPSendError("SMS service request timed out")
        except RequestException as e:
            raise OTPSendError(f"Failed to send SMS: {str(e)}")

    def _get_service_url(self, method_config: Dict[str, Any], service_type: str) -> str:
        """Get service URL for email or SMS"""
        # Use hook if provided
        if self.config.hook:
            return self.config.hook

        # Otherwise, use URL from method config or generate default
        url = method_config.get("url")
        if not url:
            endpoint = f"{service_type}/api/?action=send"
            url = get_package_url(self.request, endpoint, "communication")
        return url

    def _handle_two_factor_auth(self) -> None:
        """Handle two-factor authentication OTP"""
        policy = self._get_policy_config("two_factor_auth")

        if not policy.get("required", False):
            return

        if not self.config.code:
            otp = generate_otp(self.config.otp_type, self.user)
            message = self.config.message.format(code=otp)
        else:
            message = self.config.message.format(code=self.config.code)

        if self.config.method == "email":
            email_config = policy.get("email", {})
            url = self._get_service_url(email_config, "email")
            self._send_email(message, url)
        elif self.config.method == "sms":
            sms_config = policy.get("sms", {})
            url = self._get_service_url(sms_config, "sms")
            self._send_sms(message, url)

    def _handle_login_code(self) -> None:
        """Handle login code OTP"""
        policy = self._get_policy_config("login_methods")

        if not policy.get("otp", {}).get("enabled", False):
            return

        if not self.config.code:
            otp = generate_otp(self.config.otp_type, self.user)
            message = self.config.message.format(code=otp)
        else:
            message = self.config.message.format(code=self.config.code)

        if self.config.method == "email":
            email_config = policy.get("email", {})
            url = self._get_service_url(email_config, "email")
            self._send_email(message, url)
        elif self.config.method == "sms":
            sms_config = policy.get("sms", {})
            url = self._get_service_url(sms_config, "sms")
            self._send_sms(message, url)

    def _handle_reset_password(self) -> None:
        password_policy = self._get_policy_config("password_policy")
        password_reset_policy = password_policy.get("reset", {})
        if not password_reset_policy.get("by_code", False):
            return

        if not self.config.code:
            otp = generate_otp(self.config.otp_type, self.user)
            message = self.config.message.format(code=otp)
        else:
            message = self.config.message.format(code=self.config.code)

        if self.config.method == "email":
            email_config = password_reset_policy.get("email", {})
            url = self._get_service_url(email_config, "email")
            self._send_email(message, url)
        elif self.config.method == "sms":
            sms_config = password_reset_policy.get("sms", {})
            url = self._get_service_url(sms_config, "sms")
            self._send_sms(message, url)

    def send_otp(self) -> Dict[str, Any]:
        """Main method to send OTP"""
        try:
            self._validate_config()
            self._setup_tenant()
            self._setup_user()
            self._setup_user_role()
            self._setup_request()

            if self.config.otp_type == "two_factor_auth":
                self._handle_two_factor_auth()
            elif self.config.otp_type == "login_code":
                self._handle_login_code()
            elif self.config.otp_type == "reset_password":
                self._handle_reset_password()
            return {
                "success": True,
                "message": "OTP sent successfully",
                "method": self.config.method,
                "otp_type": self.config.otp_type,
            }

        except OTPSendError as e:
            import traceback

            return {
                "success": False,
                "message": str(e),
                "error_type": "OTP_SEND_ERROR",
                "traceback": traceback.format_exc(),
            }
        except Exception as e:
            import traceback

            return {
                "success": False,
                "message": "An unexpected error occurred while sending OTP",
                "error_type": "UNEXPECTED_ERROR",
                "traceback": traceback.format_exc(),
            }


@shared_task
def send_otp(
    method: str,
    otp_type: str,
    message: str,
    tenant_id: int,
    email: Optional[str] = None,
    phone: Optional[str] = None,
    user_id: Optional[int] = None,
    request_data: Optional[Dict[str, Any]] = None,
    user_role_id: Optional[int] = None,
    subject: Optional[str] = None,
    code: Optional[str] = None,
    config_key: Optional[str] = None,
    hook: Optional[str] = None,
    extra_data: Optional[Dict[Any, Any]] = None,
) -> Dict[str, Any]:
    """
    Celery task to send OTP via email or SMS.

    Args:
        method: Communication method ('email' or 'sms')
        otp_type: Type of OTP ('two_factor_auth' or 'login_code')
        message: Base message to send
        tenant_id: ID of the tenant
        email: User email (optional)
        phone: User phone (optional)
        user_id: User ID (optional)
        request_data: Additional request data (optional)
        user_role_id: User role ID (optional)
        subject: Email subject (optional)

    Returns:
        Dict containing success status and message
    """
    config = OTPConfig(
        method=method,
        otp_type=otp_type,
        message=message,
        tenant_id=tenant_id,
        email=email,
        phone=phone,
        user_id=user_id,
        request_data=request_data,
        user_role_id=user_role_id,
        subject=subject,
        code=code,
        hook=hook,
        config_key=config_key,
        extra_data=extra_data,
    )

    service = OTPService(config)
    result = service.send_otp()

    return result


@shared_task
def send_email(
    to: str,
    subject: str,
    body: str,
    tenant_id: int,
    email_hook: Optional[str] = None,
    config_key: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Simple celery task to send email.

    Args:
        to: Email recipient address
        subject: Email subject
        body: Email body content
        tenant_id: ID of the tenant

    Returns:
        Dict containing success status and message
    """
    try:
        # Setup tenant
        tenant = TenantModel.objects.get(id=tenant_id)
        connection.set_tenant(tenant)

        # Setup request
        request = get_mock_request()
        request.META = {"HTTP_HOST": tenant.get_primary_domain()}

        # Get email service URL
        if not email_hook:
            endpoint = "email/api/?action=send"
            email_hook = get_package_url(request, endpoint, "communication")

        # Send email
        payload = {"body": body, "to": to, "subject": subject}
        if config_key:
            payload["config_key"] = config_key

        response = requests.post(email_hook, data=payload, timeout=30)
        response.raise_for_status()

        return {
            "success": True,
            "message": "Email sent successfully",
        }

    except Exception as e:
        return {
            "success": False,
            "message": f"Failed to send email: {str(e)}",
        }


@shared_task
def send_sms(
    to: str,
    message: str,
    tenant_id: int,
    sms_hook: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Simple celery task to send SMS.

    Args:
        to: Phone number recipient
        message: SMS message content
        tenant_id: ID of the tenant
        sms_hook: Optional SMS service URL

    Returns:
        Dict containing success status and message
    """
    try:
        # Setup tenant
        tenant = TenantModel.objects.get(id=tenant_id)
        connection.set_tenant(tenant)

        # Setup request
        request = get_mock_request()
        request.META = {"HTTP_HOST": tenant.get_primary_domain()}

        # Get SMS service URL
        if not sms_hook:
            endpoint = "sms/api/?action=send"
            sms_hook = get_package_url(request, endpoint, "communication")

        # Send SMS
        payload = {
            "message": message,
            "to": to,
        }

        response = requests.post(sms_hook, data=payload, timeout=30)
        response.raise_for_status()

        return {
            "success": True,
            "message": "SMS sent successfully",
        }

    except Exception as e:
        return {
            "success": False,
            "message": f"Failed to send SMS: {str(e)}",
        }
