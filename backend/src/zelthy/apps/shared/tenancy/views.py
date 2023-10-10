import os
from zelthy.core.generic_views.base import ZelthySessionPlatformTemplateView
from zelthy.apps.permissions.models import PolicyModel
from zelthy.apps.appauth.models import AppUserModel, UserRoleModel

class DynamicPanelView(ZelthySessionPlatformTemplateView):
    """
    View to render the Dynamic Panel accessible only to platform users.
    """

    template_name = "dynamic_panel.html"

import random
import string

def generate_random_word(length=8):
    letters = string.ascii_lowercase  # using only lowercase letters
    return ''.join(random.choice(letters) for i in range(length))


from zelthy.apps.shared.tenancy.models import TenantModel
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.http import JsonResponse
from django.conf import settings
import json
import openai
openai.api_key = "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"
model="gpt-4"

from zelthy.core.common_utils import set_app_schema_path



@method_decorator(set_app_schema_path, name="dispatch")
@method_decorator(csrf_exempt, name='dispatch')
class CodeAssistView(ZelthySessionPlatformTemplateView):

    template_name = "code_assist.html"

    def get_app_obj(self, **kwargs):
        obj = TenantModel.objects.get(uuid=kwargs.get("app_uuid"))
        return obj
    
    def get_settings_path(self, **kwargs):
        obj = self.get_app_obj(**kwargs)
        path = str(settings.BASE_DIR) + f"/workspaces/{obj.name}/settings.json"
        return path


    def get_settings(self, **kwargs):
        # obj = self.get_app_obj(**kwargs)
        # path = str(settings.BASE_DIR) + f"/workspaces/{obj.name}/settings.json"
        path = self.get_settings_path(**kwargs)
        with open(path) as f:
            settings_json = json.load(f)
        return settings_json

    def post(self, request, *args, **kwargs):
        from .prompts import basic_prompt, models_prompt, crud_prompt
        knowledge_bases = {
            '1': 'basics',
            '2': 'models',
            '3': 'crud',
            '4': 'frames',
            '5': 'login_signup',
            '6': 'generic'
        }
        settings_json = self.get_settings(**kwargs)
        data = json.loads(request.body.decode('utf-8'))
        action = data['action']
        
        if action == 'get_assist':
            query_type = data['knowledge_base']
            query = knowledge_bases[query_type]
            if query == 'basics':
                message = data['message'] + f"The settings.json is {json.dumps(settings_json)}"
            else:
                message = data['message']
            if query == "basics":
                sys_prompt = basic_prompt
            elif query == "models":
                sys_prompt =  models_prompt
            elif query == "crud":
                sys_prompt = crud_prompt
            response = openai.ChatCompletion.create(          
                model="gpt-4",
                messages=[
                     # {
                    # "role": "system",
                    # "content": "You are the engine powering Zelthy CodeAssist bot. Zelthy is a App Development Platform built on Django. You will asked various questions by the Bot and you will be answering as\nper your knowledge base. The responses you send will be used by the Bot to perform actions so you have to be very precise and alwats follow the rules.\n\nApp Dev on Zelthy starts by creating modules. Modules are folders in codebase of the app where models.py, views.py, urls.py etc are maintained, just like “apps” in Django. When you are asked \nto create a new module on Zelthy Platform, you will typically be provided with the existing settings.json file. Your response should be a json of the below format:\n{“action”: “CreateModule”, “module”: <NameofModule>, “path”: <PathofModule>, “settings.json”: {\"version\":\"1.0.0\",\"modules\":[{\"name\":\"customers\",\"path\":\"customers\"},{\"name\":\"estimates\",\"path\":\"estimates\"},{\"name\":\"projects\",\"path\":\"projects\"}],\"app_routes\":[{\"re_path\":\"^customers/\",\"module\":\"customers\",\"url\":\"urls\"},{\"re_path\":\"^estimates/\",\"module\":\"estimates\",\"url\":\"urls\"},{\"re_path\":\"^projects/\",\"module\":\"projects\",\"url\":\"urls\"}],\"plugin_routes\":[{\"re_path\":\"^frame/\",\"plugin\":\"frame\",\"url\":\"urls\"}]}}\n\nFor example, if the question is “I want to create a module `currency`. The current settings.json is {\"version\":\"1.0.0\",\"modules\":[{\"name\":\"customers\",\"path\":\"customers\"},{\"name\":\"estimates\",\"path\":\"estimates\"},{\"name\":\"projects\",\"path\":\"projects\"}],\"app_routes\":[{\"re_path\":\"^customers/\",\"module\":\"customers\",\"url\":\"urls\"},{\"re_path\":\"^estimates/\",\"module\":\"estimates\",\"url\":\"urls\"},{\"re_path\":\"^projects/\",\"module\":\"projects\",\"url\":\"urls\"}],\"plugin_routes\":[{\"re_path\":\"^frame/\",\"plugin\":\"frame\",\"url\":\"urls\"}]}. Your response should be {“action”: “createModule”, “settings.json”: {\"version\":\"1.0.0\",\"modules\":[{\"name\":\"customers\",\"path\":\"customers\"},{\"name\":\"estimates\",\"path\":\"estimates\"},{\"name\":\"projects\",\"path\":\"projects\"},{\"name\":\"currency\",\"path\":\"currency\"}],\"app_routes\":[{\"re_path\":\"^customers/\",\"module\":\"customers\",\"url\":\"urls\"},{\"re_path\":\"^estimates/\",\"module\":\"estimates\",\"url\":\"urls\"},{\"re_path\":\"^projects/\",\"module\":\"projects\",\"url\":\"urls\"},{\"re_path\":\"^currency/\",\"module\":\"currency\",\"url\":\"urls\"}],\"plugin_routes\":[{\"re_path\":\"^frame/\",\"plugin\":\"frame\",\"url\":\"urls\"}]}}\n\nIf the module was already existing in the provided settings.json your response should be\n {“action”: “ModuleAlreadyExist”}\n\nThe module name must not have any special charecter and should start with an alphabet. If that rule is not followed, your response should be\n {“action”: “InvalidModuleName”}\nYou can also expect the path name to be provided explicitly or app route to be provided explicitly, in which case you should adjust your response accordingly. \n\n\nAnother common task while developing apps is to implement models. Models are similar to Django models with some tweaks. Models are typically created in models.py file inside the desired module. A few things to remember with regards to models in Zelthy. \nA model class will always subclass DynamicModelBase and not models.Model like in Django (Import for DynamicModelBase: from zelthy.apps.dynamic_models.models import DynamicModelBase)\nmodels.ForeignKey and models.OneToOneField is replaced by ZForeignKey and ZOneToOneField (Import: from zelthy.apps.dynamic_models.fields import ZForeignKey, ZOneToOneField)\nManyToManyField is not supported currently.\nZFileField replaces FileField of Django (Import: from zelthy.core.storage_utils import ZFileField)\nAll other Django fields are used normally\n\nWhen you are asked the question to create model, you can expect the already existing models.py file if any. In case the models.py is already existing you can append the file with the code for the new model \nFor example, if the question is “I want to create a model to store doctors in my module doctors. The existing models file content is \"\"\"\\nfrom django.db import models\\nfrom zelthy.apps.dynamic_models.models import DynamicModelBase\\n\\nclass Hospital(DynamicModelBase): \\n name = models.CharField(max_length=255)\\n city = models.CharField(max_length=50, blank=True)\\n\\n def __str__(self):\\n return self.name\\n””\". Your response should be  {\"action\":\"createModel\",\"module\":\"doctors\",\"models.py\":\"fromdjango.dbimportmodels\\nfromzelthy.apps.dynamic_models.modelsimportDynamicModelBase\\nfromzelthy.apps.dynamic_models.fieldsimportZForeignKey\\n\\nclassHospital(DynamicModelBase):\\nname=models.CharField(max_length=255)\\ncity=models.CharField(max_length=50,blank=True)\\n\\ndef__str__(self):\\nreturnself.name\\n\\nclassDoctors(DynamicModelBase):\\nSPECIALIZATION_CHOICES=[\\n('cardiology','Cardiology'),\\n('dermatology','Dermatology'),\\n('neurology','Neurology'),\\n#...addmorespecializationsasneeded\\n]\\n\\nname=models.CharField(max_length=255)\\nspecialization=models.CharField(max_length=50,choices=SPECIALIZATION_CHOICES)\\nphone_number=models.CharField(max_length=15,blank=True,null=True)\\nemail=models.EmailField(blank=True,null=True)\\nhospital=ZForeignKey(Hospital,null=True,blank=True)\\n\\ndef__str__(self):\\nreturnself.name\"}\n\n\nCRUD interfaces can also be created with ease on the Zelthy Platform. CRUD interfaces are created following a specific pattern in Zelthy. For this, a view is created, supported by a table class and a form class. Finally the route to the view is provided in the urls.py. For e.g. if you are provided a model \"\"\"\\nclass Customer(DynamicModelBase):\\n    name = models.CharField(max_length=200)\\n    address = models.CharField(max_length=300, blank=True)\\n    contact_person = models.CharField(max_length=200)\\n    phone = models.CharField(max_length=20)\\n    email = models.EmailField(max_length=200)\\n    currency = models.CharField(max_length=20)\\n    accounts_customer_id = models.CharField(max_length=200, unique=True)\\n\\n    def __str__(self):\\n        return self.name\\n”\"” and asked to create the crud interface in the customers module, your response should be {\"action\":\"createCrud\",\"module\":\"customers\",\"forms.py\":\"\\n\\nfrom ..plugins.crud.forms import BaseForm\\nfrom ..plugins.crud.form_fields import ModelField\\nfrom .models import Customer\\n\\nclass \
                    # CustomerForm(BaseForm):\\n  name=ModelField(placeholder=\\\"EnterName\\\",required=True,required_msg=\\\"Thisfieldisrequired.\\\")\\n  address=ModelField(placeholder=\\\"EnterAddress\\\",required=False)\\n  contact_person=ModelField(placeholder=\\\"EnterContactPerson\\\",required=True,required_msg=\\\"Thisfield1isrequired.\\\")\\n  phone=ModelField(placeholder=\\\"EnterPhone\\\",required=True,required_msg=\\\"Thisfieldisrequired.\\\",initial=\\\"+91\\\")\\n  email=ModelField(placeholder=\\\"EnterEmail\\\",required=True,required_msg=\\\"Thisfieldisrequired.\\\")\\n  currency=ModelField(placeholder=\\\"SelectCurrency\\\",required=True,required_msg=\\\"Thisfieldisrequired.\\\")\\n  accounts_customer_id=ModelField(placeholder=\\\"EnterAccountsCustomerID\\\",required=True,required_msg=\\\"Thisfieldisrequired.\\\",pattern=\\\"^[a-zA-Z0-9]*$\\\",pattern_msg=\\\"OnlyAlphanumericcharactersareallowed.\\\")\\n\\n  class Meta:\\n    model=Customer\\n\",\"tables.py\":\"\\nfrom django.db.models importQ\\nfrom zelthy.apps.dynamic_models.table.base import ModelTable\\nfrom zelthy.apps.dynamic_models.table.column import ModelCol,StringCol,NumericCol,SelectCol\\nfrom .models import Customer\\nfrom .forms import CustomerForm\\n\\nclass CustomerTable(ModelTable):\\n  id=ModelCol(display_as='ID',sortable=True,searchable=True)\\n  name=ModelCol(display_as='Name',sortable=True,searchable=True)\\n  address=ModelCol(display_as='Address',sortable=False,searchable=True)\\n  contact_person=ModelCol(display_as='ContactPerson',sortable=True,searchable=True)\\n  phone=ModelCol(display_as='Phone',sortable=False,searchable=True)\\n  email=ModelCol(display_as='Email',sortable=False,searchable=True)\\n  currency=ModelCol(display_as='Currency',sortable=True,searchable=True)\\n  accounts_customer_id=ModelCol(display_as='AccountsCustomerID',sortable=True,searchable=True)\\n\\n  table_actions=[]\\n  row_actions=[\\n{\\n\\\"name\\\":\\\"Edit\\\",\\n\\\"key\\\":\\\"edit\\\",\\n\\\"description\\\":\\\"Edit Customer\\\",\\n\\\"type\\\":\\\"form\\\",\\n\\\"form\\\":CustomerForm,#Specifytheformtouseforediting\\n\\\"roles\\\":[\\\"AnonymousUsers\\\"]#Specify roles that can perform the action\\n}\\n]\\n\\n  class Meta:\\n    model=Customer\\nfields=['id','name','address','contact_person','phone','email','currency','accounts_customer_id']\\n    row_selector={'enabled':True,'multi':False}\\n\",\"views.py\":\"\\nfrom ..plugins.crud.base import BaseCrudView\\nfrom .tables import CustomerTable\\nfrom .forms import CustomerForm\\n\\n\\nclass CustomerCrudView(BaseCrudView):\\n  page_title=\\\"CustomerRecords\\\"\\n  add_btn_title=\\\"Add New Customer\\\"\\n  table=CustomerTable\\n  form=CustomerForm\\n\\n  def has_add_perm(self,request):\\n    return True\\n\",\"urls.py\":\"\\nfrom django.urls import path\\nfrom .views import CustomerCrudView\\n\\nurlpatterns=[\\npath('customer/',CustomerCrudView.as_view(),name='customer_crud'),\\n]\\n\",\"policy\":[{\"name\":\"CustomersCrudView_AllAccess\",\"statement\":{\"permissions\":[{\"name\":\"customers.views.CustomerCrudView\",\"type\":\"view\"},{\"name\":\"Customer\",\"type\":\"model\",\"actions\":[\"view\",\"edit\",\"create\"],\"records\":{\"field\":\"id\",\"value\":1,\"operation\":\"gte\"}}]}}]}\\nIf you are requested for help with creation of user roles, you response should be {\"action\": \"createUser\", \"email\": \"Email ID provided by the user\", \"name\": \"optional name provided by the user\", \"phone\": \"optional phone number provided by the user\"}\n If you are requested to help with mapping of user role to a user, your response should be {\"action\": \"mapRole\", \"email\": \"Email ID provided by the user\", \"role_name\": \"role name provided by the user\"}\n If you are requested to help with mapping of a policy to a user role, your response should be {\"action\": \"mapPolicy\", \"role_name\": \"role name provided by the user\", \"policy\": \"policy name provided by the user\\n If you are requested to help with setting up of frame for a user role, your response should be {\"action\": \"setupFrame\", \"role_name\": \"role name provided by the user\", \"menu\": # \"menu as list of dict with keys for url and name\"}. For e.g. if menu indicated by the user is display name \"My Patients\" and path \"\patients\all_patients\" then menu would be [{\"url\": \"\patients\all_patients\", \"icon\": \"\", \"name\": \"My Patients\"}]"
                    # },
                    {
                        "role": "system",
                        "content": sys_prompt

                    },
                    {
                    "role": "user",
                    "content": message
                    }
                ],
                temperature=0,
                max_tokens=2000,
                top_p=0.18,
                frequency_penalty=0,
                presence_penalty=0
            )
            print(response)
            try:
                response_msg = json.loads(response['choices'][0]['message']['content'])
            except Exception as e:
                print("e1", e)
                response_msg = response['choices'][0]['message']['content']
            try:                
                action = response_msg.get('action', None)
            except:
                action = None
            print("Action", action)
            if action:
                if action == 'CreateModule':
                    assist_msg = [{
                                    "content": f"Great! I am ready to help you create your `{response_msg['path']}` module.<br> For this I will be creating a new directory named `{response_msg['path']}` and will also register your module. Your new settings.json will be", 
                                    "type": "text"},
                                  {"content": f"{response_msg['settings.json']}", "type": "code", "code": "json"}
                                ]
                    # assist_msg =  {response_msg['settings.json']}. "
                    allow_execution = True
                    exection_json = {"execution":"createModule", "dir": response_msg['path'], "settings.json": response_msg['settings.json']}
                elif action == 'createModel':
                    assist_msg = [{
                                "content":f"Sure! I am ready to help you create your requested model.<br> For this I will be adding the model's class in the module's models.py file. The proposed model's class is <br>",
                                "type": "text"},
                                {
                                "content": f"{response_msg['models.py']}",
                                "type": "code",
                                "code": "python"
                                }]
                    allow_execution = True
                    exection_json = {"execution":"createModel", "module": response_msg['module'], "models.py": response_msg['models.py']}
                elif action == 'createCrud':
                    assist_msg = [{
                        "content": f"Sure! I am ready to help you create your requested crud interface.<br> For this I will be creating or appending the views.py, forms.py, tables.py and urls.py files. The proposed changes are <br> ",
                        "type": "text"
                        },
                        {
                          "content": f"#forms.py: \n{response_msg['forms.py']}\n#<br> tables.py: \n{response_msg['tables.py']}\n#views.py: \n{response_msg['views.py']}\n#urls.py:\n{response_msg['urls.py']}",
                          "type": "code",
                          "code": "python"    
                        }
                    ]
                    allow_execution = True
                    exection_json = {"execution":"createCrud", "module": response_msg['module'], "forms.py": response_msg['forms.py'], "tables.py": response_msg['tables.py'], "views.py": response_msg['views.py'], "urls.py": response_msg['urls.py'], 'policy': response_msg['policy']}
                
                elif action == 'createRole':
                    assist_msg = [{
                        "content": f"Sure! I am ready to help you create the user role",
                        "type": "text"}]
                    allow_execution = True
                    exection_json = {"execution":"createRole", "role_name": response_msg['role_name']}
                elif action == 'createUser':
                    password = generate_random_word()
                    assist_msg = [{
                        "content": f"Sure! I am ready to help you create your requested user.<br> Should I go ahead and create a user with email {response_msg['email']} and password {password}",
                        "type": "text"}
                    ]
                    allow_execution = True
                    exection_json = {"execution":"createUser", "email": response_msg['email'], "password": password, "name": response_msg['name']}
                
                elif action == 'mapRole':
                    assist_msg = [{
                        "content": f"Sure! I am ready to help you map the user to the requested role.",
                        "type": "text"}
                    ]
                    allow_execution = True
                    exection_json = {"execution":"mapRole", "role_name": response_msg['role_name'], "email": response_msg['email']}

                elif action == 'mapPolicy':
                    assist_msg = [{
                        "content": f"Sure! I am ready to help you map the user to the requested role.",
                        "type": "text"}
                    ]
                    allow_execution = True
                    exection_json = {"execution":"mapPolicy", "role_name": response_msg['role_name'], "policy": response_msg['policy']}

                
                # elif action == 'setupFrame':
                #     assist_msg = f"Sure! I am ready to help you with setting up of the frame for the requested user role"
                #     allow_execution = True
                #     exection_json = {"execution":"mapPolicy", "role_name": response_msg['role_name'], "policy": response_msg['policy']}




            else:
                assist_msg = [{"content": response_msg, "type": "text"}]
                allow_execution = False
                exection_json = None
            return JsonResponse({'message': assist_msg, 'allow_execution': allow_execution, 'exection_json': exection_json})

        elif action == 'execute':
            exection_json = data['execute_json']
            execution = exection_json['execution']
            if execution == 'createModule':
                execute = self.createModule(exection_json, **kwargs)
            elif execution == 'createModel':
                execute = self.createModel(exection_json, **kwargs)
            elif execution == 'createCrud':
                execute = self.createCrud(exection_json, **kwargs)
            elif execution == 'createUser':
                execute = self.createUser(exection_json, **kwargs)
            elif execution == 'createRole':
                execute = self.createRole(exection_json, **kwargs)
            elif execution == 'mapRole':
                execute = self.mapRole(exection_json, **kwargs)
            elif execution == 'mapPolicy':
                execute = self.mapPolicy(exection_json, **kwargs)

            # assist_msg = 'Executed Successfully!'
            return JsonResponse({'message': execute[1]})
        
    def createModule(self, exection_json, **kwargs):
        app_obj = self.get_app_obj(**kwargs)
        module_path = str(settings.BASE_DIR) + f"/workspaces/{app_obj.name}/" + exection_json['dir']
        try:
            try:                
                os.mkdir(module_path)
                settings_path = self.get_settings_path(**kwargs)
                with open(settings_path, "w") as f:
                    f.write(json.dumps(exection_json['settings.json'], indent=4))
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
        model_path = str(settings.BASE_DIR) + f"/workspaces/{app_obj.name}/{execution_json['module']}/models.py"
        with open(model_path, 'a') as f:
            f.write(execution_json['models.py'])
        return (True, "Succesfully executed")

    def createCrud(self, execution_json, **kwargs):
        app_obj = self.get_app_obj(**kwargs)
        views_path = str(settings.BASE_DIR) + f"/workspaces/{app_obj.name}/{execution_json['module']}/views.py"
        forms_path = str(settings.BASE_DIR) + f"/workspaces/{app_obj.name}/{execution_json['module']}/forms.py"
        tables_path = str(settings.BASE_DIR) + f"/workspaces/{app_obj.name}/{execution_json['module']}/tables.py"
        urls_path = str(settings.BASE_DIR) + f"/workspaces/{app_obj.name}/{execution_json['module']}/urls.py"
        with open(views_path, 'a') as f:
            f.write(execution_json['views.py'])
        with open(forms_path, 'a') as f:
            f.write(execution_json['forms.py'])
        with open(tables_path, 'a') as f:
            f.write(execution_json['tables.py'])
        with open(urls_path, 'a') as f:
            f.write(execution_json['urls.py'])
        policy = execution_json['policy']
        PolicyModel.objects.get_or_create(name=policy[0]['name'], statement=policy[0]['statement'], is_active=True)
        return (True, "Succesfully executed")
        

    def createUser(self, execution_json, **kwargs):

        try:
            if AppUserModel.objects.filter(email=execution_json['email']).exists():
                return (False, f"This email ID is already taken")
            user = AppUserModel.objects.create(email=execution_json['email'], name=execution_json['name'], is_active=True)
            user.set_password(execution_json['password'])
            user.save()
            return (True, "Succesfully executed")
        except Exception as e:
            return (False, f"Error encountered while creating user: {str(e)}")
    
    def createRole(self, execution_json, **kwargs):
        if UserRoleModel.objects.filter(name__icontains=execution_json['role_name']).exists():
            return (False, f"User Role with this name already exists!")
        role = UserRoleModel.objects.create(name=execution_json['role_name'], is_active=True)
        return (True, "Succesfully executed")

    def mapRole(self, execution_json, **kwargs):
        user = AppUserModel.objects.filter(email__icontains=execution_json['email']).first()
        if not user:
            return (False, f"There is no user with the provided email ID {execution_json['email']}")
        role = UserRoleModel.objects.filter(name__icontains=execution_json['role_name']).first()
        if not role:
            return (False, f"There is no role matching the name provided {execution_json['role_name']}")
        user.roles.add(role)
        user.save()
        return (True, "Succesfully executed")
    
    def mapPolicy(self, execution_json, **kwargs):
        role = UserRoleModel.objects.filter(name__icontains=execution_json['role_name']).first()
        if not role:
            return (False, f"There is no role with the provided name {execution_json['role_name']}")
        policy = PolicyModel.objects.filter(name__icontains=execution_json['policy']).first()
        if not policy:
            return (False, f"There is no policy matching the name provided policy name {execution_json['policy']}")
        role.policies.add(policy)
        role.save()
        return (True, "Succesfully executed")