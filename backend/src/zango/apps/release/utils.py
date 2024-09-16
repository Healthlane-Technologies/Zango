from packaging.version import InvalidVersion, Version


def is_version_greater(version1, version2):
    try:
        v1 = Version(version1)
        v2 = Version(version2)
        return v1 > v2
    except InvalidVersion as e:
        print(f"Invalid version: {e}")
        return False
