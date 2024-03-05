from zelthy.core.utils import get_current_request


def set_created_modified_by(sender, instance, **kwargs):
    req = get_current_request()
    if req and req.user and req.user.__class__.__name__ == "AppUserModel":
        user = req.user
    else:
        user = None
    if not instance.pk:
        instance.created_by = user
    else:
        instance.modified_by = user
    return
