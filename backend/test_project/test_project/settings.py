from pathlib import Path

from zango.config.settings.base import *  # noqa: F403


BASE_DIR = Path(__file__).resolve().parent.parent

environ.Env.read_env(os.path.join(BASE_DIR, ".env"))


class AttrDict(dict):
    """
    A dictionary subclass for managing global settings with attribute-style access.

    This class allows getting and setting items in the global namespace
    using both attribute and item notation.
    """

    def __getattr__(self, item):
        return globals()[item]

    def __setattr__(self, item, value):
        globals()[item] = value

    def __setitem__(self, key, value):
        globals()[key] = value


# Call setup_settings to initialize the settings
settings_result = setup_settings(AttrDict(vars()), BASE_DIR)

# Setting Overrides
# Any settings that need to be overridden or added should be done below this line
# to ensure they take effect after the initial setup

SECRET_KEY = "django-insecure-3uvu-m1-#a7sm8f#nr@p@&e6t70^q67uzfz^rmn7nyd*8)jc*4"  # pragma: allowlist secret
TEST_MIGRATION_RUNNING = True
PROJECT_NAME = "test_project"

# To change the media storage to S3 you can use the BACKEND class provided by the default storage
# To change the static storage to S3 you can use the BACKEND class provided by the staticfiles storage
# STORAGES = {
#     "default": {"BACKEND": "zango.core.storage_utils.S3MediaStorage"},
#     "staticfiles": {"BACKEND": "zango.core.storage_utils.S3StaticStorage"},
# }


# INTERNAL_IPS can contain a list of IP addresses or CIDR blocks that are considered internal.
# Both individual IP addresses and CIDR notation (e.g., '192.168.1.1' or '192.168.1.0/24') can be provided.
