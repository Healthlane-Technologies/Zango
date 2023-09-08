import unittest
import subprocess
import os
import django
import sys
import shutil

class TestDataBase(unittest.TestCase):

    @classmethod
    def setUpClass(cls) -> None:
        cls.project_name = "zel3"
        cls.db_params = {
            'host': 'localhost',
            'port': '5432',
            'database': 'zelthy1',
            'user': 'postgres',
            'password': 'zelthy3pass'
        }
        process = subprocess.Popen(
            f'zelthy3 start-project {cls.project_name} --db_name={cls.db_params["database"]} --db_user={cls.db_params["user"]} --db_password={cls.db_params["password"]} --db_host={cls.db_params["host"]} --db_port={cls.db_params["port"]}',
            shell=True  # Use shell=True if your command is a string with shell features (e.g., pipes)
        )
        exit_code = process.wait()
        sys.path.insert(0, cls.project_name)
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', f'{cls.project_name}.settings')
        django.setup()
    
    def test_db_settings(self):
        expected = {
                "NAME": self.db_params["database"],
                "USER": self.db_params["user"],
                "PASSWORD": self.db_params["password"],
                "HOST": self.db_params["host"],
                "PORT": self.db_params["port"],
        }
        from django.conf import settings
        for key, val in expected.items():
            assert settings.DATABASES["default"][key] == val
    
    def test_root_url_conf(self):
        expected = f"{self.project_name}.urls_tenants"
        from django.conf import settings
        assert settings.ROOT_URLCONF == expected
    
    def test_wsgi_application(self):
        expected = f"{self.project_name}.wsgi.application"
        from django.conf import settings
        assert settings.WSGI_APPLICATION == expected
    
    def test_directory_structure(self):
        assert os.path.exists(f"./{self.project_name}/{self.project_name}")
        assert os.path.exists(f"./{self.project_name}/manage.py")
        assert os.path.exists(f"./{self.project_name}/{self.project_name}/settings.py")

    @classmethod
    def tearDownClass(cls) -> None:
        shutil.rmtree(f"./{cls.project_name}")
    