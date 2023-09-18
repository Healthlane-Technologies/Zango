import re


def replace_placeholders_in_file(filename, replacements):
    """
    Replaces placeholders in a file with specified values.

    Args:
        filename (str): The name of the file to perform the replacements on.
        replacements (dict): A dictionary containing the placeholders as keys and their corresponding values as values.
        Ex.,
        {
            "{{name}}": "John",
            "{{age}}": "30"
        }
    """
    with open(filename, "r") as file:
        content = file.read()

    for placeholder, value in replacements.items():
        content = content.replace(placeholder, value)

    with open(filename, "w") as file:
        file.write(content)
