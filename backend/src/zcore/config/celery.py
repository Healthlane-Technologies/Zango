import os
from celery import Celery

# Fetching project name
current_project_dir = os.getcwd()
project_name = os.path.basename(current_project_dir)

# Setting the Django settings module to the current project's settings
os.environ.setdefault("DJANGO_SETTINGS_MODULE", f"{project_name}.settings")

# Creating a Celery application instance
app = Celery("zelthy")

# Configuring the Celery app using the Django settings
app.config_from_object("django.conf:settings", namespace="CELERY")

# Discovering and registering task modules
app.autodiscover_tasks()
