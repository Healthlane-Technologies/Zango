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

    shutil.copytree("config", f"{project_dir}/config")
    shutil.copy("zelthy3_prod.yml", f"{project_dir}/docker-compose.prod.yml")
    if without_db:
        shutil.copy("zelthy3_without_db.yml", f"{project_dir}/docker-compose.yml")
    else:
        shutil.copy("zelthy3_with_db.yml", f"{project_dir}/docker-compose.yml")
    shutil.copy("dev.dockerfile", f"{project_dir}/dev.dockerfile")
    shutil.copy("prod.dockerfile", f"{project_dir}/prod.dockerfile")
    shutil.copy("init.sh", f"{project_dir}/init.sh")


def write_env_file(project_dir, args):
    with open(f"{project_dir}/.env", "w") as f:
        f.write(f"PLATFORM_USERNAME={args.platform_username}\n")
        f.write(f"PLATFORM_USER_PASSWORD={args.platform_user_password}\n")
        f.write(f"PROJECT_NAME={args.project_name}\n")
        f.write(f"POSTGRES_USER=zelthy_admin\n")
        f.write(f"POSTGRES_PASSWORD=zelthy3pass\n")
        f.write(f"POSTGRES_DB=zelthy\n")
        f.write(f"POSTGRES_HOST=postgres\n")
        f.write(f"POSTGRES_PORT=5432\n")
        f.write(f"REDIS_HOST=redis")


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


# def substitute_env(project_dir):
#     for file in ["docker-compose.yml", "docker-compose.prod.yml", "server.dockerfile", "nginx.conf"]:
#         with tempfile.NamedTemporaryFile(delete=False) as temp:
#             subprocess.run(f"envsubst < {project_dir}/{file}", shell=True, check=True, stdout=temp)
#             temp_path = temp.name

#         os.replace(temp_path, f'{project_dir}/{file}')


def setup_project(project_dir, project_name, without_db, start=False):
    # substitute_env(project_dir)
    if start:
        try:
            proc = subprocess.Popen(
                f"docker compose -f {project_dir}/docker-compose.yml up", shell=True
            )
            signal.signal(
                signal.SIGINT, lambda sig, frame: print("\nStopping zelthy environment")
            )
            proc.wait()
        except subprocess.CalledProcessError as e:
            traceback.print_exc()
            print(f"Error: {e}")
        except KeyboardInterrupt:
            pass


def rebuild_core(project_dir):
    try:
        subprocess.run(f"docker build -t zelthy3 .", shell=True, check=True)
        subprocess.run(
            f"docker compose -f {project_dir}/docker-compose.yml build",
            shell=True,
            check=True,
        )
        sys.exit(0)
    except subprocess.CalledProcessError as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    args = sys.argv[1:]
    parser = argparse.ArgumentParser(
        prog="zelthy_setup", description="Helps you develop with zelthy locally"
    )
    parser.add_argument("--project_name", default="", help="The name of the project")
    parser.add_argument(
        "--without_db",
        action="store_true",
        default=False,
        help="Whether to set up without a database",
    )
    parser.add_argument(
        "--skip_build_project",
        action="store_true",
        default=False,
        help="Whether to skip the build step",
    )
    parser.add_argument(
        "--project_dir", default="zproject", help="The project directory"
    )
    parser.add_argument(
        "--build_core",
        action="store_true",
        default=False,
        help="Whether to skip the build step",
    )
    parser.add_argument(
        "--platform_username", default="zelthy@mail.com", help="The platform username"
    )
    parser.add_argument(
        "--platform_user_password",
        default="Zelthy@123",
        help="The platform user password",
    )
    parser.add_argument("--start", action="store_true", default=False)
    parser.add_argument("--rebuild_core", action="store_true", default=False)
    args = parser.parse_args()
    try:
        if args.build_core:
            build_core()
            sys.exit(0)
        if args.project_name == "":
            args.project_name = "zelthy_project"
        if args.rebuild_core:
            rebuild_core(args.project_dir)
        load_necessary_files(args.project_dir, args.project_name, args.without_db)
        write_env_file(args.project_dir, args)
        setup_project(args.project_dir, args.project_name, args.without_db, args.start)
    except Exception:
        traceback.print_exc()
