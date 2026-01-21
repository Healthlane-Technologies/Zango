from pathlib import Path

from zango.config.settings.base import *  # noqa: F403


BASE_DIR = Path(__file__).resolve().parent.parent


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

SECRET_KEY = "{{secret_key}}"  # Shift this to .env


# INTERNAL_IPS can contain a list of IP addresses or CIDR blocks that are considered internal.
# Both individual IP addresses and CIDR notation (e.g., '192.168.1.1' or '192.168.1.0/24') can be provided.
