import json
import os
import zipfile


def extract_app_details_from_zip(template_zip):
    settings_filename = "settings.json"
    try:
        with zipfile.ZipFile(template_zip, "r") as zip_file:
            # Check if the settings file exists in the zip
            zip_name = str(template_zip).split(".")[0]

            # List all files in the zip
            all_files = zip_file.namelist()

            # Find the settings file path
            settings_path = None
            for file_path in all_files:
                if file_path == os.path.join(zip_name, settings_filename):
                    settings_path = file_path
                    break

            if not settings_path:
                raise FileNotFoundError(
                    f"{settings_filename} not found in the zip file."
                )

            # Read the contents of the settings file
            with zip_file.open(settings_path) as settings_file:
                settings_content = settings_file.read()

            # Parse the JSON content
            settings = json.loads(settings_content)
            return (
                settings.get("version", None),
                settings.get("app_name", None),
                "nice app",
            )

    except zipfile.BadZipFile:
        print(f"Error: {template_zip} is not a valid zip file.")
    except json.JSONDecodeError:
        print(f"Error: {settings_filename} is not a valid JSON file.")
    except Exception as e:
        print(f"An error occurred: {str(e)}")

    return None, None, None


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
