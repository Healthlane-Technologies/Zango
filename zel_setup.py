import os
import sys
import argparse
import traceback
import shutil
import signal
import subprocess

def load_necessary_files(project_dir, project_name, without_db):
    if not os.path.exists(project_dir):
         os.mkdir(project_dir)
    if without_db:
        shutil.copy("zelthy3_without_db.yml", f"{project_dir}/docker-compose.yml")
    else:
        shutil.copy("zelthy3_with_db.yml", f"{project_dir}/docker-compose.yml")
    shutil.copy("server.dockerfile", f"{project_dir}/server.dockerfile")
    shutil.copy("init.sh", f"{project_dir}/init.sh")

def write_env_file(project_dir, args):
    with open(f"{project_dir}/.env", "w") as f:
        f.write(f"SERVER={args.server}\n")
        f.write(f"PLATFORM_USERNAME={args.platform_username}\n")
        f.write(f"PLATFORM_USER_PASSWORD={args.platform_user_password}\n")
        f.write(f"PROJECT_NAME={args.project_name}\n")


def build_core():
    try:
        subprocess.run("docker build -t zelthy3 .", shell=True, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error: {e}")

def build_project(file):
   try:
       subprocess.run(f"docker compose -f {file} build", shell=True, check=True)
   except subprocess.CalledProcessError as e:
       print(f"Error: {e}")

def setup_dev(project_dir, project_name, without_db, skip_build=False):
    if not skip_build:
        print("Building with db")
        build_project(f"{project_dir}/docker-compose.yml")
    try:
        proc = subprocess.Popen(f"docker compose -f {project_dir}/docker-compose.yml up", shell=True)
        signal.signal(signal.SIGINT, lambda sig, frame: print("\nStopping zelthy environment"))
        proc.wait()
    except subprocess.CalledProcessError as e:
        traceback.print_exc()
        print(f"Error: {e}")
    except KeyboardInterrupt:
        pass
   

def setup_prod():
   pass

if __name__ == "__main__":
   args = sys.argv[1:]
   parser = argparse.ArgumentParser(prog="zelthy_setup", description="Helps you develop with zelthy locally")
   parser.add_argument("--project_name", default="", help="The name of the project")
   parser.add_argument("-env", "--environment", choices=["prod", "dev"], default="dev", help="The environment to set up")
   parser.add_argument("--without_db", action="store_true", default=False, help="Whether to set up without a database")
   parser.add_argument("--skip_build_project", action="store_true", default=False, help="Whether to skip the build step")
   parser.add_argument("--project_dir", default="zproject", help="The project directory")
   parser.add_argument("--build_core", action="store_true", default=False, help="Whether to skip the build step")
   parser.add_argument("--server", default="runserver", help="The server which runs the project")
   parser.add_argument("--platform_username", default="zelthy@mail.com", help="The platform username")
   parser.add_argument("--platform_user_password", default="Zelthy@123", help="The platform user password")
   args = parser.parse_args()
   try:
    if args.project_name == "":
        args.project_name = "zelthy_project"
    load_necessary_files(args.project_dir, args.project_name, args.without_db)
    write_env_file(args.project_dir, args)
    if args.build_core:
        build_core()
    if args.environment == "dev":
        setup_dev(args.project_dir, args.project_name, args.without_db, args.skip_build_project)
   except Exception:
       traceback.print_exc()