
# Django Imports
from django.http import Http404
from django.conf import settings
from django.http import HttpResponse
from django.views.generic import TemplateView

# # Third Party imports
# from braces.views import CsrfExemptMixin

from .models import UserRoleModel


class AppLoginSignupView(TemplateView):

    template_name = 'app_login_signup.html'

    def get_role_configuration(self, request, role_id):

        try:
        
            role = UserRoleModel.objects.get(id=role_id)
            
            return role.config['login_signup_config']

        except UserRoleModel.DoesNotExist:

            raise Http404


    def get_context_data(self, **kwargs):

        context = super(AppLoginSignupView, self).get_context_data(**kwargs)

        role_id = kwargs['role_id']

        config = self.get_role_configuration(self.request, role_id)

        context['favicon_url'] = config['theme']['default'].get('favicon_url', '')
        context['meta_title'] = config['theme']['default'].get('meta_title', 'Zelthy')
        context['env'] = settings.ENV
        context['app_version'] = '1.0.6'
        

        return context



###API

# Direct Package Imports
import json
import uuid
import time
# import redis
import base64
from datetime import datetime
from random import randint

# Django Imports
from django.apps import apps
from django.db.models import Q
from django.http import Http404
from django.db import connection
from django.conf import settings
from django.http import HttpResponse
from django.contrib.auth import login
from django.views.generic import TemplateView

# Third Party imports
# from braces.views import CsrfExemptMixin
from rest_framework.views import APIView

# Shared Code Base Imports
# from global_utils import sc
# from backend.core.mail import ZelthyEmail
# from backend.core.common_utils import randomword
# from backend.core.global_config import COUNTRY_CODES
# from backend.core.tenant_utils import get_company_tenant
# from backend.core.api.generic_views import ZelthySessionAPIView
# from backend.apps.shared.registration.models import TherapyUserRoles, Users

# Tenants Code Base Imports
# from backend.apps.tenants.sms.models import SMSConfig
# from backend.apps.tenants.companyusers.models import CompanyUsers
# from backend.apps.tenants.zemail.models import ZEmailConfigurationModel
# from backend.apps.tenants.user_invitation.models import CodeModel

# Import from same app
# from .utils import validate_email, validate_mobile, check_if_username_email_mobile

USER_AUTH_BACKEND = 'backend.apps.shared.registration.auth_backend.UsersModelBackend'


class LoginSignupV2APIView(APIView):


    def get_role_configuration(self, request, role_id):

        try:
        
            role = UserRoleModel.objects.get(id=role_id)
            
            return role.config['login_signup_config']

        except UserRoleModel.DoesNotExist:

            raise Http404

    
    def get_data_from_redis(self, request_id, data_key, step_key):
        r = redis.Redis(host=settings.REDIS_HOST, port=settings.REDIS_PORT, db=0)

        val = r.hgetall(request_id)

        if not val:
            return False, "No Data Saved"

        if step_key:
            stepper_data = val.get(step_key)


            if not stepper_data:
                return False, "Data step not yet executed"

            else:
                stepper_data = eval(stepper_data)
        else:
            stepper_data = val

        target_data = stepper_data.get(data_key)

        if data_key in stepper_data:
            return True, target_data
        return False, "Target Data not saved"


    def get_consent_data(self, request_id):

        consent_data = {}

        consent_keys = ['ip_address', 'agent', 'consent_text', 'consent_datetime']

        for consent_key in consent_keys:
            consent_tuple = self.get_data_from_redis(request_id, consent_key, "submit_consent")
            if consent_tuple[0]:
                consent_data.update({
                    consent_key: consent_tuple[1]        
                })

        return consent_data


    def del_session(self, key):
        r = redis.Redis(host=settings.REDIS_HOST, port=settings.REDIS_PORT, db=0)
        r.delete(key)
        return


    def complete_signup(self, request, email, mobile, role_id, cuser_id, consent_data, request_id):

        try:

            company_tenant = get_company_tenant(request.tenant)

            cu = None
            user = None

            config = self.get_role_configuration(request, role_id)
            code = None

            if config['steps']['code']:
                code_tuple = self.get_data_from_redis(request_id, "code", None)
                if code_tuple[0]:
                    code = code_tuple[1]
                else:
                    return {
                        "code": 1,
                        "success": False,
                        "message": "Invalid User Invitation. Please Contact Customer care if the issue persists.",
                        "request_id": request_id
                    }


            with sc(company_tenant.name):

                if cuser_id:
                    cu = CompanyUsers.objects.get(id=cuser_id)
                    cu.email = email
                    cu.primary_phone = mobile
                    cu.save()
                    user = cu.user
                    th_role = TherapyUserRoles.objects.get(id=role_id)
                    user.therapy_roles.add(th_role)
                    user.save()
                    consent_json = cu.consent_json
                    if consent_json:
                        consent_json.update({
                                request.tenant.name: consent_data
                            })
                    else:
                        consent_json = {
                            request.tenant.name: consent_data
                        }
                    cu.consent_json = consent_json
                    cu.save()
                    self.login_into_the_system(request, cu.id, role_id, request_id)

                    response =  {
                        'code': 1,
                        'message': 'Signup Successful'
                    }
                else:
                    password = randomword(6)
                    res = CompanyUsers.create_companyuser(
                        '',
                        email,
                        mobile,
                        password,
                        [role_id],
                        request.tenant,
                        False,
                        False
                    )
                    if res.get('cuser'):
                        cu = res.get('cuser')
                        cu.consent_json = {
                            request.tenant.name: consent_data
                        }
                        user = cu.user
                        cu.save()
                        self.login_into_the_system(request, cu.id, role_id, request_id)

                    response = res

            if response.get('code') == 1 and code:
                code_result = CodeModel.utilize_code(code, user, role_id=role_id)
                if code_result[0]:
                    code_obj = code_result[1]
                    modelObj = code_obj.object_fk
                    print(modelObj)
                    # field_name = config['steps']['code']['object_code']['field']
                    modelObj.user = user
                    modelObj.save()
                    print('here')
                    # setattr(modelObj, field_name, )

            return response

        except Exception as e:
            print(str(e))
            import sys, os
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            print(exc_type, fname, exc_tb.tb_lineno)
            return {
                "success": False,
                "error": str(e),
                "line": exc_tb.tb_lineno

            }


    def login_into_the_system(self, request, cuser_id, role_id, request_id):

        try:

            th_role = TherapyUserRoles.objects.get(id=role_id)

            company_tenant = get_company_tenant(request.tenant)

            with sc(company_tenant.name):
                cu = CompanyUsers.objects.get(id=cuser_id)

                self.del_session(request_id)

                cu.user.switch_therapy_role(
                                th_role, request)
                login(
                    request, cu.user, backend=USER_AUTH_BACKEND)

            return {
                'success': True
            }
        except Exception as e:
            print(str(e))
            import sys, os
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            print(exc_type, fname, exc_tb.tb_lineno)

            return {
                'success': False,
                "message": "Something went wrong"
            }


    def send_login_otp(self, request, role_id, data, request_id):

        # Take username from redis of verify_username

        username_tuple = self.get_data_from_redis(request_id, "username", "verify_username")
        if username_tuple[0]:
            username = username_tuple[1]
        else:
            return {
                "success": False,
                "message": username_tuple[1],
                "request_id": request_id
            }, 400


        config = self.get_role_configuration(request, role_id)

        username_type = check_if_username_email_mobile(username)

        configuration_type = 'login_otp'

        otp = "111111" if settings.ENV == "dev" else str(randint(100000, 999999))

        if username_type == "email":

            email_config = config['triggers'][configuration_type]['email']

            email_config_id = email_config['config_id']

            email_body = email_config['message'].format(username=username, otp=otp)

            email_subject = email_config['subject']

            email_config_model = ZEmailConfigurationModel.objects.get(id=email_config_id)  

            config_name = email_config_model.label

            from_email = email_config_model.from_email

            template = 'generic_email_template.html'

            context = {
                'email_body':email_body
                }

            html_body={
                    'template': template,
                    'context': context, 
                    'request': request
                    }

            to_email = username

            email = ZelthyEmail(
                            subject=email_subject,
                            html_body=html_body,
                            from_email=from_email,
                            to=[to_email]
                            )

            email.send_email(request.tenant, config_name)
        else:

            try:

                sms_config = config['triggers'][configuration_type]['sms']

                sms_body = sms_config['message'].format(username=username, otp=otp)

                sms_config_id = sms_config['config_id']

                to_phone = str(username)

                SMS = SMSConfig.objects.get(id=sms_config_id)

                SMS.send_sms(to_phone, sms_body)

            except Exception as e:

                print(str(e))

                print('Exception in sending sms')

        # key = str(uuid.uuid4())
        r = redis.Redis(host=settings.REDIS_HOST, port=settings.REDIS_PORT, db=0)
        key = hash(request_id+"-login_otp")

        r.hmset(key, {
            'expiry': int(time.time())+15*60, # 15 mins expiry
            'otp': otp
        })

        return {
            "success": True,
            "next": "verify_login_otp",
            "request_id": request_id
        }, 200


    def verify_login_otp(self, request, role_id, data, request_id):

        username_tuple = self.get_data_from_redis(request_id, "username", "verify_username")
        if username_tuple[0]:
            username = username_tuple[1]
        else:
            return {
                "success": False,
                "message": username_tuple[1],
                "request_id": request_id
            }, 400

        otp = data.get('otp')

        if not otp:
            return {
                "success": False,
                "message": "Invalid OTP",
                "request_id": request_id
            }, 400

        key = hash(request_id+"-login_otp")
        
        r = redis.Redis(host=settings.REDIS_HOST, port=settings.REDIS_PORT, db=0)
        val = r.hgetall(key)

        if not val:
            return {
                "success": False,
                "request_id": request_id,
                "message": "Invalid OTP"
            }, 400

        else:
            try:
                stored_otp = val['otp']

                expiry = val['expiry']

                if str(stored_otp) == str(otp):
                    if int(time.time()) < int(expiry):
                        self.del_session(key)
                        cuser_id_tuple = self.get_data_from_redis(request_id, "cuser_id", "verify_username")
                        if cuser_id_tuple[0]:
                            cuser_id = cuser_id_tuple[1]
                        else:
                            return {
                                "success": False,
                                "message": cuser_id_tuple[1],
                                "request_id": request_id
                            }, 400
                        result = self.login_into_the_system(request, cuser_id, role_id, request_id)
                        return {
                            "success": True,
                            "next": "done",
                            "request_id": request_id
                        }, 200
                    else:
                        self.del_session(key)
                        return {
                            "success": False,
                            "message": "OTP expired...Please try resend otp or try login again",
                            "request_id": request_id
                        }, 400
                else:
                    return {
                        "success": False,
                        "message": "Invalid OTP",
                        "request_id": request_id
                    }, 400
            except Exception as e:
                print(str(e))
                return {
                        "success": False,
                        "message": "Invalid OTP",
                        "request_id": request_id
                    }, 400


    def check_cat_user(self, request, user, request_id):
        connection.set_tenant(request.tenant)  
        with connection.cursor() as c:
            if user.get_category_user():
                return {
                    "success": False,
                    "message": "User is Deactivated...Kindly contact support for any queries",
                    "request_id": request_id
                }
            else:
                return {
                    'success': True
                }


    def validate_process_username_verification(self, request, role_id, data, request_id):

        # this will be the first step for all further proccesses so we will generate a request id here and use it over the course

        username = data.get('username')

        if not username:
            return {
                "success": False,
                "message": "Please Enter Username",
                "request_id": request_id
            }, 400

        config = self.get_role_configuration(request, role_id)

        username_type = check_if_username_email_mobile(username)

        username_types = config['steps']['auth']['username']

        if username_type not in username_types:
            return {
                "success": False,
                "message": username_type+" is not allowed" if username_type else "Please Enter Valid username",
                "request_id": request_id
            }, 400


        validation_dict = {
            'email': validate_email,
            'primary_phone': validate_mobile
        }

        try:
            is_valid, message = validation_dict[username_type](username)
            if is_valid:
                filter_query = {
                    username_type: username
                }
                company_tenant = get_company_tenant(request.tenant)
                with sc(company_tenant.name):
                    try:
                        cu = CompanyUsers.objects.get(**filter_query)
                        user = cu.user
                        th_roles = user.therapy_roles.filter(id=role_id)
                        if th_roles.exists():
                            return {
                                "success": True,
                                "next": "send_login_otp",
                                "message": "User Exists..We will procceed with login for "+username_type,
                                "request_id": request_id,
                                "username": username,
                                "cuser_id": cu.id
                            }, 200
                        return_res = self.check_cat_user(request, user, request_id)
                        if not return_res['success']:
                            return return_res, 400
                        if config['steps']['auth'].get('can_signup', True):
                            return_res = {
                                "success": True,
                                "next": "signup_username",
                                "message": "User Does not Exists..We will procceed with signup"+username_type,
                                "request_id": request_id,
                                "username": username
                            }

                            if config['steps']['consent']['enabled']:
                                return_res.update({
                                    'consent_text': config['steps']['consent']['consent_text'],
                                    'on_username_page': config['steps']['consent']['on_username_page']
                                })

                            return return_res, 200
                        else:
                            return {
                                "success": False,
                                "message": "Invalid Username",
                                "request_id": request_id
                            }, 400
                    except CompanyUsers.DoesNotExist:
                        if config['steps']['auth'].get('can_signup', True):
                            return_res = {
                                "success": True,
                                "next": "signup_username",
                                "message": "User Does not Exists..We will procceed with signup"+username_type,
                                "request_id": request_id,
                                "username": username
                            }

                            if config['steps']['consent']['enabled']:
                                return_res.update({
                                    'consent_text': config['steps']['consent']['consent_text'],
                                    'on_username_page': config['steps']['consent']['on_username_page']
                                })

                            return return_res, 200
                        else:
                            return {
                                "success": False,
                                "message": "Invalid Username",
                                "request_id": request_id
                            }, 400
            else:
                return {
                    "success": False,
                    "message": message,
                    "request_id": request_id
                }, 400

        except Exception as e:
            print(str(e))
            return {
                "success": False,
                "message": "Invalid Username",
                "request_id": request_id
            }, 400


    def verify_alternate_username(self, request, role_id, data, request_id):
        
        username_tuple = self.get_data_from_redis(request_id, "username", "signup_username")
        if username_tuple[0]:
            username = username_tuple[1]
        else:
            return {
                "success": False,
                "message": username_tuple[1],
                "request_id": request_id
            }, 400

        alternate_username = data.get('alternate_username')
        
        cuser_id_tuple = self.get_data_from_redis(request_id, "cuser_id", "signup_username")
        if cuser_id_tuple[0]:
            cuser_id = cuser_id_tuple[1]
        else:
            return {
                "success": False,
                "message": cuser_id_tuple[1],
                "request_id": request_id
            }, 400

        config = self.get_role_configuration(request, role_id)

        username_type = check_if_username_email_mobile(username)

        alternate_username_type = check_if_username_email_mobile(alternate_username)

        alternate_username_types = config['steps']['alternate_username']['mandatory'] + config['steps']['alternate_username']['optional']


        if alternate_username_types and alternate_username_type not in alternate_username_types:
            return {
                "success": False,
                "message": alternate_username_type+" is not allowed" if alternate_username_type else "Please Enter a valid alternate username",
                "request_id": request_id
            }, 400

        if config['steps']['alternate_username']['mandatory'] and (alternate_username_type not in config['steps']['alternate_username']['mandatory'] and username_type not in config['steps']['alternate_username']['mandatory']):
            return {
                "success": False,
                "message": alternate_username_type+" is not allowed" if alternate_username_type else "Please Enter a valid alternate username",
                "request_id": request_id
            }, 400

        if not alternate_username:
            # create or add role to company user
            if username_type == 'email':
                email = username
                modile = ''
            else:
                email = ''
                mobile = username

            consent_data = self.get_consent_data(request_id)

            self.complete_signup(request, email, mobile, role_id, cuser_id, consent_data, request_id)
            return {
                "success": True,
                "request_id": request_id,
                "next": "done",
                "message": "Signup Success"
            }, 200

        validation_dict = {
            'email': validate_email,
            'primary_phone': validate_mobile
        }
        signup_user = False
        try:
            is_valid, message = validation_dict[alternate_username_type](alternate_username)
            if is_valid:
                code = None

                if config['steps']['code']:

                    # if data.get('code') or 
                    code_tuple = self.get_data_from_redis(request_id, "code", None)
                    if code_tuple[0]:
                        code = code_tuple[1]
                    else:
                        code = data.get('code')

                    if not code:
                        return {
                            "success": False,
                            "message": "Invalid User Invitation. Please Contact Customer care if the issue persists.",
                            "request_id": request_id
                        }, 400
                    verify_code_kwargs = {
                        alternate_username_type: alternate_username,
                        username_type: username
                    }
                    code_result = CodeModel.verify_code(code, role_id=role_id, **verify_code_kwargs)

                    if not code_result[0]:
                        return {
                            "success": False,
                            "request_id": request_id,
                            "message": code_result[1]
                        }, 400
                filter_query = {
                    alternate_username_type: alternate_username
                }
                company_tenant = get_company_tenant(request.tenant)

                with sc(company_tenant.name):
                    try:
                        cu = CompanyUsers.objects.get(**filter_query)
                        signup_user = False
                    except CompanyUsers.DoesNotExist:
                        signup_user = True

                    if signup_user:
                        return_res = {
                            "success": True,
                            "next": "send_alternate_username_otp",
                            "message": "User eligible for signing up with alternate username",
                            "request_id": request_id,
                            "alternate_username": alternate_username
                        }

                        return return_res, 200

                    else:
                        return {
                            "success": False,
                            "message": "User Already Exists...Try using different username",
                            "request_id": request_id
                        }, 400

            else:
                return {
                    "success": False,
                    "message": message,
                    "request_id": request_id
                }, 400

        except Exception as e:
            print(str(e))
            import sys, os
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            print(exc_type, fname, exc_tb.tb_lineno)
            return {
                "success": False,
                "message": "Invalid Username",
                "request_id": request_id
            }, 400


    def signup_username(self, request, role_id, data, request_id):

        username = data.get('username')

        if not username:
            return {
                "success": False,
                "message": "Please Enter Username",
                "request_id": request_id
            }, 400

        config = self.get_role_configuration(request, role_id)

        username_type = check_if_username_email_mobile(username)

        username_types = config['steps']['auth']['username']

        if username_type not in username_types:
            return {
                "success": False,
                "message": username_type+" is not allowed" if username_type else "Please Enter Valid username",
                "request_id": request_id
            }, 400

        validation_dict = {
            'email': validate_email,
            'primary_phone': validate_mobile
        }

        code = None

        if config['steps']['code']:

            # if data.get('code') or 
            code_tuple = self.get_data_from_redis(request_id, "code", None)
            if code_tuple[0]:
                code = code_tuple[1]
            else:
                code = data.get('code')

            if not code:
                return {
                    "success": False,
                    "message": "Invalid User Invitation. Please Contact Customer care if the issue persists.",
                    "request_id": request_id
                }, 400
            verify_code_kwargs = {
                username_type: username
            }
            code_result = CodeModel.verify_code(code, role_id=role_id, **verify_code_kwargs)

            if not code_result[0]:
                return {
                    "success": False,
                    "request_id": request_id,
                    "message": code_result[1]
                }, 400


        signup_user = False
        cuser_id = 0
        try:
            is_valid, message = validation_dict[username_type](username)
            if is_valid:
                filter_query = {
                    username_type: username
                }
                company_tenant = get_company_tenant(request.tenant)

                with sc(company_tenant.name):
                    try:
                        cu = CompanyUsers.objects.get(**filter_query)
                        user = cu.user
                        th_roles = user.therapy_roles.filter(therapy=request.tenant.therapy)
                        if th_roles.exists():
                            signup_user = False
                        else:
                            signup_user = True
                        cuser_id = cu.id
                    except CompanyUsers.DoesNotExist:
                        signup_user = True

                    if signup_user:
                        return_res = {
                            "success": True,
                            "next": "submit_consent",
                            "message": "User eligible for signing up",
                            "request_id": request_id,
                            "cuser_id": cuser_id,
                            "username": username
                        }

                        if code:
                            return_res.update({
                                    'code': code
                                })

                        if config['steps']['consent']['enabled']:
                            return_res.update({
                                'consent_text': config['steps']['consent']['consent_text'],
                                'on_username_page': config['steps']['consent']['on_username_page']
                            })
                        return return_res, 200

                    else:
                        return {
                            "success": False,
                            "message": "User Already Exists...Try using different username",
                            "request_id": request_id
                        }, 400

            else:
                return {
                    "success": False,
                    "message": message,
                    "request_id": request_id
                }, 400

        except Exception as e:
            print(str(e))
            return {
                "success": False,
                "message": "Invalid Username",
                "request_id": request_id
            }, 400


    def submit_consent(self, request, role_id, data, request_id):

        # username = data['username']
        username_tuple = self.get_data_from_redis(request_id, "username", "signup_username")
        if username_tuple[0]:
            username = username_tuple[1]
        else:
            return {
                "success": False,
                "message": username_tuple[1],
                "request_id": request_id
            }, 400

        config = self.get_role_configuration(request, role_id)

        consent_text = config['steps']['consent']['consent_text']

        # getting ip address
        agent = request.META.get('HTTP_USER_AGENT', '')
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')

        return {
            "success": True,
            "next": "send_signup_otp",
            "ip_address": ip,
            "agent": agent,
            "consent_text": consent_text,
            "consent_datetime": datetime.today().strftime('%Y-%m-%d %H:%M:%s'),
            "request_id": request_id
        }, 200


    def send_signup_otp(self, request, role_id, data, request_id):

        username_tuple = self.get_data_from_redis(request_id, "username", "signup_username")
        if username_tuple[0]:
            username = username_tuple[1]
        else:
            return {
                "success": False,
                "message": username_tuple[1],
                "request_id": request_id
            }, 400

        config = self.get_role_configuration(request, role_id)

        username_type = check_if_username_email_mobile(username)

        configuration_type = 'signup_otp'

        otp = "111111" if settings.ENV == "dev" else str(randint(100000, 999999))

        if username_type == "email":

            email_config = config['triggers'][configuration_type]['email']

            email_config_id = email_config['config_id']

            email_body = email_config['message'].format(username=username, otp=otp)

            email_subject = email_config['subject']

            email_config_model = ZEmailConfigurationModel.objects.get(id=email_config_id)  

            config_name = email_config_model.label

            from_email = email_config_model.from_email

            template = 'generic_email_template.html'

            context = {
                'email_body':email_body
                }

            html_body={
                    'template': template,
                    'context': context, 
                    'request': request
                    }

            to_email = username

            email = ZelthyEmail(
                            subject=email_subject,
                            html_body=html_body,
                            from_email=from_email,
                            to=[to_email]                          
                            )

            email.send_email(request.tenant, config_name)
        else:

            try:

                sms_config = config['triggers'][configuration_type]['sms']

                sms_body = sms_config['message'].format(username=username, otp=otp)

                sms_config_id = sms_config['config_id']

                to_phone = str(username)

                SMS = SMSConfig.objects.get(id=sms_config_id)

                SMS.send_sms(to_phone, sms_body)

            except Exception as e:

                print(str(e))

                print('Exception in sending sms')



        # otp = str(randint(100000, 999999))

        # key = str(uuid.uuid4())
        r = redis.Redis(host=settings.REDIS_HOST, port=settings.REDIS_PORT, db=0)
        key = hash(request_id+"-signup_otp")

        r.hmset(key, {
            'expiry': int(time.time())+15*60, # 15 mins expiry
            'otp': otp
        })


        return {
            "success": True,
            "next": "verify_signup_otp",
            "request_id": request_id
        }, 200


    def verify_signup_otp(self, request, role_id, data, request_id):

        otp = data.get('otp')

        username_tuple = self.get_data_from_redis(request_id, "username", "signup_username")
        if username_tuple[0]:
            username = username_tuple[1]
        else:
            return {
                "success": False,
                "message": username_tuple[1],
                "request_id": request_id
            }, 400

        cuser_id_tuple = self.get_data_from_redis(request_id, "cuser_id", "signup_username")
        if cuser_id_tuple[0]:
            cuser_id = cuser_id_tuple[1]
        else:
            return {
                "success": False,
                "message": cuser_id_tuple[1],
                "request_id": request_id
            }, 400


        if not otp:
            return {
                "success": False,
                "request_id": request_id,
                "message": "Invalid OTP"
            }, 400

        key = hash(request_id+"-signup_otp")

        config = self.get_role_configuration(request, role_id)
        username_type = check_if_username_email_mobile(username)

        if username_type == 'email':
            to_get_alternate_username_type = "primary_phone"
        else:
            to_get_alternate_username_type = "email"
        
        r = redis.Redis(host=settings.REDIS_HOST, port=settings.REDIS_PORT, db=0)
        val = r.hgetall(key)

        print(val)

        if not val:
            print('here')
            return {
                "success": False,
                "request_id": request_id,
                "message": "Invalid OTP"
            }, 400

        else:
            try:

                stored_otp = val['otp']
                expiry = val['expiry']

                if str(stored_otp) == str(otp):
                    if int(time.time()) < int(expiry):
                        self.del_session(key)

                        # here send configuration for alternate username

                        if config['steps']['alternate_username']['enabled']:

                            can_skip_alternate_username = False

                            if not config['steps']['alternate_username']['mandatory']:
                                can_skip_alternate_username = True
                            else:
                                if len(config['steps']['alternate_username']['mandatory']) == 1 and username_type in config['steps']['alternate_username']['mandatory']:
                                    can_skip_alternate_username = True

                            if can_skip_alternate_username:
                                code = None

                                if config['steps']['code']:
                                    code_tuple = self.get_data_from_redis(request_id, "code", None)
                                    if code_tuple[0]:
                                        code = code_tuple[1]
                                    else:
                                        return {
                                            "code": 1,
                                            "success": False,
                                            "message": "Invalid User Invitation. Please Contact Customer care if the issue persists.",
                                            "request_id": request_id
                                        }

                                    code_result = CodeModel.verify_code(code, role_id=role_id)

                                    if code_result[0]:
                                        code_obj = code_result[1]
                                        category_obj = code_obj.object_fk
                                        if category_obj:
                                            if getattr(category_obj, to_get_alternate_username_type):
                                                can_skip_alternate_username = False
                                    else:
                                        return {
                                            "success": False,
                                            "request_id": request_id,
                                            "message": code_result[1]
                                        }, 400


                            return {
                                "success": True,
                                "next": "verify_alternate_username",
                                "request_id": request_id,
                                "alternate_username_configs": config['steps']['alternate_username'],
                                "can_skip_alternate_username": can_skip_alternate_username,
                                "to_get_alternate_username_type": to_get_alternate_username_type
                            }, 200
                        else:
                            if username_type == 'email':
                                email = username
                                modile = ''
                            else:
                                email = ''
                                mobile = username

                            consent_data = self.get_consent_data(request_id)
                            self.complete_signup(request, email, mobile, role_id, cuser_id, consent_data, request_id)
                            return {
                                "success": True,
                                "request_id": request_id,
                                "next": "done",
                                "message": "Signup Success"
                            }
                    else:
                        self.del_session(key)
                        return {
                            "success": False,
                            "message": "OTP expired...Please try resend otp or try login again",
                            "request_id": request_id
                        }, 400
                else:
                    return {
                        "success": False,
                        "message": "Invalid OTP",
                        "request_id": request_id
                    }, 400
            except Exception as e:
                print(str(e))
                return {
                        "success": False,
                        "message": "Invalid OTP",
                        "request_id": request_id
                    }, 400


    def send_alternate_username_otp(self, request, role_id, data, request_id):

        alternate_username_tuple = self.get_data_from_redis(request_id, "alternate_username", "verify_alternate_username")
        if alternate_username_tuple[0]:
            alternate_username = alternate_username_tuple[1]
        else:
            return {
                "success": False,
                "message": alternate_username_tuple[1],
                "request_id": request_id
            }, 400

        config = self.get_role_configuration(request, role_id)

        alternate_username_type = check_if_username_email_mobile(alternate_username)

        configuration_type = 'alternate_username_otp'

        otp = "111111" if settings.ENV == "dev" else str(randint(100000, 999999))

        if alternate_username_type == "email":

            email_config = config['triggers'][configuration_type]['email']

            email_config_id = email_config['config_id']

            email_body = email_config['message'].format(username=alternate_username, otp=otp)

            email_subject = email_config['subject']

            email_config_model = ZEmailConfigurationModel.objects.get(id=email_config_id)  

            config_name = email_config_model.label

            from_email = email_config_model.from_email

            template = 'generic_email_template.html'

            context = {
                'email_body':email_body
                }

            html_body={
                    'template': template,
                    'context': context, 
                    'request': request
                    }

            to_email = alternate_username

            email = ZelthyEmail(
                            subject=email_subject,
                            html_body=html_body,
                            from_email=from_email,
                            to=[to_email]                            
                            )

            email.send_email(request.tenant, config_name)
        else:

            try:

                sms_config = config['triggers'][configuration_type]['sms']

                sms_body = sms_config['message'].format(username=alternate_username, otp=otp)

                sms_config_id = sms_config['config_id']

                to_phone = str(alternate_username)

                SMS = SMSConfig.objects.get(id=sms_config_id)

                SMS.send_sms(to_phone, sms_body)

            except Exception as e:

                print(str(e))

                print('Exception in sending sms')

        
        # key = str(uuid.uuid4())
        r = redis.Redis(host=settings.REDIS_HOST, port=settings.REDIS_PORT, db=0)
        key = hash(request_id+"-alternate_username_otp")

        r.hmset(key, {
            'expiry': int(time.time())+15*60, # 15 mins expiry
            'otp': otp
        })

        return {
            "success": True,
            "next": "verify_alternate_username_otp",
            "request_id": request_id
        }, 200


    def verify_alternate_username_otp(self, request, role_id, data, request_id):

        username_tuple = self.get_data_from_redis(request_id, "username", "signup_username")
        if username_tuple[0]:
            username = username_tuple[1]
        else:
            return {
                "success": False,
                "message": username_tuple[1],
                "request_id": request_id
            }, 400

        alternate_username_tuple = self.get_data_from_redis(request_id, "alternate_username", "verify_alternate_username")
        if alternate_username_tuple[0]:
            alternate_username = alternate_username_tuple[1]
        else:
            return {
                "success": False,
                "message": alternate_username_tuple[1],
                "request_id": request_id
            }, 400

        otp = data.get('otp')

        config = self.get_role_configuration(request, role_id)

        if not otp:
            return {
                "success": False,
                "message": "Invalid OTP",
                "request_id": request_id
            }, 400

        cuser_id_tuple = self.get_data_from_redis(request_id, "cuser_id", "signup_username")
        if cuser_id_tuple[0]:
            cuser_id = cuser_id_tuple[1]
        else:
            return {
                "success": False,
                "message": cuser_id_tuple[1],
                "request_id": request_id
            }, 400

        alternate_username_type = check_if_username_email_mobile(alternate_username)

        username_type = check_if_username_email_mobile(username)

        email = ''
        mobile = ''

        if username_type == "email":
            email = username
        else:
            mobile = username

        if alternate_username_type == "email":
            email =  alternate_username
        else:
            mobile = alternate_username


        key = hash(request_id+"-alternate_username_otp")
        
        r = redis.Redis(host=settings.REDIS_HOST, port=settings.REDIS_PORT, db=0)
        val = r.hgetall(key)

        if not val:
            return {
                "success": False,
                "request_id": request_id,
                "message": "Invalid OTP"
            }, 400

        else:
            try:

                stored_otp = val['otp']
                expiry = val['expiry']

                if str(stored_otp) == str(otp):
                    if int(time.time()) < int(expiry):
                        self.del_session(key)

                        consent_data = self.get_consent_data(request_id)
                        self.complete_signup(request, email, mobile, role_id, cuser_id, consent_data, request_id)

                        return {
                            "success": True,
                            "next": "done",
                            "request_id": request_id,
                        }, 200
                    else:
                        self.del_session(key)
                        return {
                            "success": False,
                            "message": "OTP expired...Please try resend otp or try login again",
                            "request_id": request_id
                        }, 400
                else:
                    return {
                        "success": False,
                        "message": "Invalid OTP",
                        "request_id": request_id
                    }, 400
            except Exception as e:
                print(str(e))
                import sys, os
                exc_type, exc_obj, exc_tb = sys.exc_info()
                fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
                print(exc_type, fname, exc_tb.tb_lineno)
                return {
                        "success": False,
                        "message": "Invalid OTP",
                        "request_id": request_id
                    }, 400


    def skip_alternate_username(self, request, role_id, data, request_id):

        username_tuple = self.get_data_from_redis(request_id, "username", "signup_username")

        if username_tuple[0]:
            username = username_tuple[1]
        else:
            return {
                "success": False,
                "message": username_tuple[1],
                "request_id": request_id
            }, 400

        username_type = check_if_username_email_mobile(username)

        config = self.get_role_configuration(request, role_id)

        cuser_id_tuple = self.get_data_from_redis(request_id, "cuser_id", "signup_username")
        if cuser_id_tuple[0]:
            cuser_id = cuser_id_tuple[1]
        else:
            return {
                "success": False,
                "message": cuser_id_tuple[1],
                "request_id": request_id
            }, 400

        consent_data = self.get_consent_data(request_id)

        email = ''
        mobile = ''

        if username_type == "email":
            email = username
        else:
            mobile = username

        if not config['steps']['alternate_username']['mandatory']:

            result = self.complete_signup(request, email, mobile, role_id, cuser_id, consent_data, request_id)

            return {
                'success': True,
                'next': "done",
                'message': 'Alternate Username step skipped Successfully',
                'request_id': request_id
            }, 200

        else:
            if len(config['steps']['alternate_username']['mandatory']) == 1 and username_type in config['steps']['alternate_username']['mandatory']:

                result = self.complete_signup(request, email, mobile, role_id, cuser_id, consent_data, request_id)

                return {
                    'success': True,
                    'next': "done",
                    'message': 'Alternate Username step skipped Successfully',
                    'request_id': request_id
                }, 200

        return {
            'success': False,
            'message': 'Cannot Skip Alternate Username Step',
            'request_id': request_id
        }, 400


    def move_back(self, request, role_id, data, request_id):

        r = redis.Redis(host=settings.REDIS_HOST, port=settings.REDIS_PORT, db=0)

        val = r.hgetall(request_id)

        if not val:
            return {
                'success': False,
                'message': 'Back operation not possible',
                'request_id': request_id,
            }, 400
            
        else:
            try:
                current_next = val['next_step']
            except:
                return {
                    'success': False,
                    'message': 'Back operation not possible',
                    'request_id': request_id,
                }, 400

        back_step_map = {
            'verify_username': None,
            'send_login_otp': 'verify_username',
            'verify_login_otp': 'send_login_otp',
            'resend_login_otp': 'verify_username',
            'signup_username': 'verify_username',
            'submit_consent': 'signup_username',
            'send_signup_otp': 'signup_username',
            'verify_signup_otp': 'send_signup_otp',                    
            'resend_signup_otp': 'signup_username',
            'verify_alternate_username': 'verify_signup_otp',
            'send_alternate_username_otp': 'verify_alternate_username',
            'verify_alternate_username_otp': 'send_alternate_username_otp',
            'resend_alternate_username_otp': 'verify_alternate_username',
        }

        return {
            'next': back_step_map[current_next],
            'success': True,
            'request_id': request_id
        }, 200


    def post(self, request, *args, **kwargs):

        role_id = kwargs['role_id']

        data = request.data

        request_id = data.get('request_id', None)

        if not 'step' in data:
            return HttpResponse(json.dumps({
                'success': False,
                'message': 'Invalid step',
                'request_id': request_id
            }), status=400)
            # return Failed HttpResponse

        
        if not request_id:
            return HttpResponse(json.dumps({
                'success': False,
                'message': 'Invalid Request ID',
                'request_id': request_id
            }), status=400)

        r = redis.Redis(host=settings.REDIS_HOST, port=settings.REDIS_PORT, db=0)

        val = r.hgetall(request_id)

        steps_mapper = {
            'verify_username': self.validate_process_username_verification,
            'send_login_otp': self.send_login_otp,
            'verify_login_otp': self.verify_login_otp,
            'resend_login_otp': self.send_login_otp,
            'signup_username': self.signup_username,
            'submit_consent': self.submit_consent,
            'send_signup_otp': self.send_signup_otp,
            'verify_signup_otp': self.verify_signup_otp,                    
            'resend_signup_otp': self.send_signup_otp,
            'verify_alternate_username': self.verify_alternate_username,
            'send_alternate_username_otp': self.send_alternate_username_otp,
            'verify_alternate_username_otp': self.verify_alternate_username_otp,
            'resend_alternate_username_otp': self.send_alternate_username_otp,
            'skip_alternate_username': self.skip_alternate_username,
            'back_step': self.move_back
        }


        if data.get('username'):
            data['username'] = data['username'].lower()
        
        if data.get('alternate_username'):
            data['alternate_username'] = data['alternate_username'].lower()

        result = steps_mapper[data['step']](request, role_id, data, request_id)

        if result[1] == 200:

            if not val:

                r.hmset(request_id, {
                    data['step']: result[0],
                    "next_step": result[0].get('next')
                })
            else:
                val.update({
                        data['step']: result[0],
                        "next_step": result[0].get('next')
                    })
                r.hmset(request_id, val)


        return HttpResponse(json.dumps(result[0]), status=result[1])


    def get(self, request, *args, **kwargs):

        role_id = kwargs['role_id']

        code = request.GET.get('code')

        if code:
            try:
                code = base64.b64decode(code)
            except:
                raise Exception('Invalid Code')

        config = self.get_role_configuration(self.request, role_id)

        login_methods = config['steps']['auth']['methods']
        username_types = config['steps']['auth']['username']

        fe_config = {
            'methods': login_methods
        }

        # ['oidc', 'sso', 'otp', 'password']

        fe_config = {
            'username_types': username_types
        }
        request_id = uuid.uuid4().hex
        fe_config['request_id'] = request_id

        fe_config['theme_config'] = config['theme']['default']

        # r = redis.Redis(host=settings.REDIS_HOST, port=settings.REDIS_PORT, db=0)

        # val = r.hgetall(request_id)
        val = None

        # if not val:
        #     fe_config['redirect_to_login_page'] = True

        # if code:
        #     if not val:

        #         r.hmset(request_id, {
        #             'code': code
        #         })
        #     else:
        #         val.update({
        #                 'code': code
        #             })
        #         r.hmset(request_id, val)

        # try:
        #     fe_config['country_code'] = "+" + COUNTRY_CODES[settings.PHONENUMBER_DEFAULT_REGION]
        # except:
        #     fe_config['country_code'] = "+91"


        return HttpResponse(json.dumps(fe_config), status=200)


