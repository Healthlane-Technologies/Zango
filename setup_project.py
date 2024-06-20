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

    shutil.copytree("deploy/config", f"{project_dir}/config")
    shutil.copy(
        "deploy/docker_compose.prod.yml", f"{project_dir}/docker-compose.prod.yml"
    )
    if without_db:
        shutil.copy("zelthy3_without_db.yml", f"{project_dir}/docker-compose.yml")
    else:
        shutil.copy(
            "deploy/docker_compose.dev.yml", f"{project_dir}/docker-compose.yml"
        )
    shutil.copy("deploy/dev.dockerfile", f"{project_dir}/dev.dockerfile")
    shutil.copy("deploy/prod.dockerfile", f"{project_dir}/prod.dockerfile")
    shutil.copy("deploy/init.sh", f"{project_dir}/init.sh")


def write_env_file(project_dir, args):
    with open(f"{project_dir}/.env", "w") as f:
        f.write(f"PLATFORM_USERNAME={args.platform_username}\n")
        f.write(f"PLATFORM_USER_PASSWORD={args.platform_user_password}\n")
        f.write(f"PROJECT_NAME={args.project_name}\n")
        f.write(f"POSTGRES_USER=zango_admin\n")
        f.write(f"POSTGRES_PASSWORD=zangopass\n")
        f.write(f"POSTGRES_DB=zango\n")
        f.write(f"POSTGRES_HOST=postgres\n")
        f.write(f"POSTGRES_PORT=5432\n")
        f.write(f"REDIS_HOST=redis\n")
        f.write(f"REDIS_PORT=6379\n")
        if args.platform_domain_url:
            f.write(f"PLATFORM_DOMAIN_URL={args.platform_domain_url}\n")


def build_core():
    try:
        subprocess.run("docker build -t zango .", shell=True, check=True)
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
                signal.SIGINT, lambda sig, frame: print("\nStopping zango environment")
            )
            proc.wait()
        except subprocess.CalledProcessError as e:
            traceback.print_exc()
            print(f"Error: {e}")
        except KeyboardInterrupt:
            pass


def rebuild_core(project_dir):
    try:
        subprocess.run(f"docker build -t zango .", shell=True, check=True)
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
        prog="zango_setup", description="Helps you develop with zango locally"
    )
    parser.add_argument("--project_name", default="", help="The name of the project")
    parser.add_argument(
        "--without_db",
        action="store_true",
        default=False,
        help="Whether to set up without a database",
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
        "--platform_username",
        default="platform_admin@zango.dev",
        help="The platform username",
    )
    parser.add_argument(
        "--platform_user_password",
        default="Zango@123",
        help="The platform user password",
    )
    parser.add_argument("--rebuild_core", action="store_true", default=False)
    parser.add_argument("--platform_domain_url", default="localhost")
    args = parser.parse_args()
    try:
        if args.build_core:
            build_core()
            sys.exit(0)
        if args.project_name == "":
            args.project_name = "zango_project"
        if args.rebuild_core:
            rebuild_core(args.project_dir)
        load_necessary_files(args.project_dir, args.project_name, args.without_db)
        write_env_file(args.project_dir, args)
    except Exception:
        traceback.print_exc()
