from django.contrib.auth.signals import user_logged_in


def user_logged_in_handler(sender, request, user, **kwargs):
    """
    Set the selected role id in the request session when a user logs in
    """
    if request.tenant.tenant_type == "app":
        selected_role_id = getattr(request, "selected_role_id", None)
        if selected_role_id:
            request.session["role_id"] = selected_role_id


# Connect the signal
user_logged_in.connect(user_logged_in_handler)
