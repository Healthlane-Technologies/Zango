import json
import os
import zipfile

from packaging.specifiers import SpecifierSet
from packaging.version import Version

import zango


def extract_app_details_from_zip(template_zip):
    settings_filename = "settings.json"
    migration_gen_path = "migrations/generate.txt"
    try:
        with zipfile.ZipFile(template_zip, "r") as zip_file:
            # Check if the settings file exists in the zip
            zip_name = str(template_zip).split(".")[0]

            # List all files in the zip
            all_files = zip_file.namelist()

            # Find the settings file path
            settings_path = next(
                (path for path in all_files if settings_filename in path), None
            )
            run_migrations = next(
                (True for path in all_files if migration_gen_path in path), False
            )

            if not settings_path:
                raise FileNotFoundError(
                    f"{settings_filename} not found in the zip file."
                )

            # Read the contents of the settings file
            with zip_file.open(settings_path) as settings_file:
                settings_content = settings_file.read()
                print("Settings content:", settings_content)

            # Parse the JSON content
            settings = json.loads(settings_content)
            if settings.get("zango_version"):
                zango_version = settings["zango_version"]
                installed_zango_version = Version(zango.__version__)
                specifier = SpecifierSet(zango_version)
                if installed_zango_version not in specifier:
                    raise Exception(
                        f"Zango version {installed_zango_version} is not compatible with {zango_version}"
                    )
            return (settings["version"], settings["app_name"], run_migrations)

    except zipfile.BadZipFile:
        raise Exception(f"Error: {template_zip} is not a valid zip file.")
    except json.JSONDecodeError:
        raise Exception(f"Error: {settings_filename} is not a valid JSON file.")
    except KeyError:
        raise Exception(f"Error: version or app_name not found in {settings_filename}.")
    except Exception as e:
        raise Exception(f"An error occurred: {str(e)}")


def extract_zip_to_temp_dir(app_template):
    # Create a temporary directory
    temp_dir = os.getcwd()

    try:
        # Extract the zip file to the temporary directory
        with zipfile.ZipFile(app_template, "r") as zip_ref:
            zip_ref.extractall(temp_dir)

        # Return the path of the temporary directory
        return temp_dir
    except Exception as e:
        # If an error occurs, remove the temporary directory and re-raise the exception
        os.rmdir(temp_dir)
        raise e
