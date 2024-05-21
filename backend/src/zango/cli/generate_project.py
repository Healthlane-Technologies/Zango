import click
import json
import dotenv

from django.conf import settings

settings.configure()

from zango.codeassist.models.app_spec import ApplicationSpec

import os
import sys
import django
from pathlib import Path

# Determine the base directory of the Django project
BASE_DIR = Path(__file__).resolve().parent.parent
environment = dotenv.load_dotenv(BASE_DIR.parent / ".env")

# Add the base directory to the Python path
sys.path.append(str(BASE_DIR))

print("The project name is : ", os.environ.get("PROJECT_NAME"))

# Set the DJANGO_SETTINGS_MODULE environment variable
os.environ.setdefault(
    "DJANGO_SETTINGS_MODULE", f"{os.environ.get('PROJECT_NAME')}.settings"
)

# Initialize Django
django.setup()


@click.command("generate-project")
@click.argument("tenant")
def generate_project(tenant):
    # resp = requests.get(
    #     f"https://e0312d0b4f18e54cb6e44831ce6bf350.serveo.net"
    # ).json()["content"]
    # print("The response content is : ", json.loads(resp))
    resp = """
        {
            "modules":[
                {
                    "name":"PatientModule",
                    "path":"PatientModule",
                    "settings":{
                        "version":"1.0",
                        "modules":[
                        {
                            "name":"PatientModule",
                            "path":"PatientModule"
                        },
                        {
                            "name":"AppointmentModule",
                            "path":"appointment_module"
                        },
                        {
                            "name":"BillingModule",
                            "path":"billing_module"
                        }
                        ],
                        "app_routes":[
                        {
                            "module":"PatientModule",
                            "re_path":"^patients/",
                            "url":"patient_urls"
                        },
                        {
                            "module":"AppointmentModule",
                            "re_path":"^appointments/",
                            "url":"appointment_urls"
                        },
                        {
                            "module":"BillingModule",
                            "re_path":"^billing/",
                            "url":"billing_urls"
                        }
                        ]
                    },
                    "models":[
                        {
                        "name":"Patient",
                        "fields":[
                            {
                                "name":"first_name",
                                "type":"CharField",
                                "constraints":[
                                    {
                                    "max_length":50
                                    }
                                ]
                            },
                            {
                                "name":"last_name",
                                "type":"CharField",
                                "constraints":[
                                    {
                                    "max_length":50
                                    }
                                ]
                            },
                            {
                                "name":"date_of_birth",
                                "type":"DateField",
                                "constraints":[
                                    
                                ]
                            },
                            {
                                "name":"gender",
                                "type":"CharField",
                                "constraints":[
                                    {
                                    "choices":[
                                        "Male",
                                        "Female",
                                        "Other"
                                    ]
                                    }
                                ]
                            },
                            {
                                "name":"contact_number",
                                "type":"CharField",
                                "constraints":[
                                    {
                                    "max_length":15
                                    }
                                ]
                            }
                        ]
                        },
                        {
                        "name":"Appointment",
                        "fields":[
                            {
                                "name":"patient",
                                "type":"ForeignKey",
                                "constraints":[
                                    {
                                    "to":"Patient"
                                    }
                                ]
                            },
                            {
                                "name":"appointment_date",
                                "type":"DateTimeField",
                                "constraints":[
                                    
                                ]
                            },
                            {
                                "name":"description",
                                "type":"TextField",
                                "constraints":[
                                    
                                ]
                            }
                        ]
                        },
                        {
                        "name":"Billing",
                        "fields":[
                            {
                                "name":"appointment",
                                "type":"ForeignKey",
                                "constraints":[
                                    {
                                        "to":"Appointment"
                                    }
                                ]
                            },
                            {
                                "name":"amount",
                                "type":"DecimalField",
                                "constraints":[
                                    {
                                            "max_digits":10,
                                            "decimal_places":2
                                    }
                                ]
                            },
                            {
                                "name":"status",
                                "type":"CharField",
                                "constraints":[
                                    {
                                        "choices":[
                                            "Paid",
                                            "Unpaid",
                                            "Pending"
                                        ]
                                    }
                                ]
                            }
                        ]
                        }
                    ],
                    "migrate_models": true
                }
            ],
            "tenant":"CodeAssist"
        }
        """
    parse_resp = ApplicationSpec.model_validate(json.loads(resp))
    parse_resp.apply()
