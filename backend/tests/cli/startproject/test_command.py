import subprocess
import unittest
import os
import shutil
import psycopg2
import sys
from importlib import import_module
import os
import django

class TestProjectCreation(unittest.TestCase):

    @classmethod
    def setUp(cls) -> None:
        cls.project_name = "zel3"
        cls.db_params = {
            'host': 'localhost',
            'port': '5432',
            'database': 'zelthy1',
            'user': 'postgres',
            'password': 'zelthy3pass'
        }
        cls.conn = psycopg2.connect(**cls.db_params)
        cls.cursor = cls.conn.cursor()
    
    def test_creation(self):
        process = subprocess.Popen(
            f'zelthy3 start-project {self.project_name} --db_name={self.db_params["database"]} --db_user={self.db_params["user"]} --db_password={self.db_params["password"]} --db_host="localhost" --db_port="5432"',
            shell=True  # Use shell=True if your command is a string with shell features (e.g., pipes)
        )
        exit_code = process.wait()
        assert exit_code == 0
        shutil.rmtree(f"./{self.project_name}")

    def test_no_project_name(self):
        with self.assertRaises(subprocess.CalledProcessError):
            proc = subprocess.check_call([
            "zelthy3", "start-project",
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    
    # def test_incorrect_db_settings(self):
    #     process = subprocess.Popen(
    #         f'zelthy3 start-project zel3 --db_name="zelth3" --db_user="post" --db_password="pass" --db_host="localhost" --db_port="5432"',
    #         shell=True, stderr=subprocess.PIPE, stdout=subprocess.PIPE  # Use shell=True if your command is a string with shell features (e.g., pipes)
    #     )
    #     exit_code = process.wait()
    #     process.kill()
    #     assert exit_code == 1
      