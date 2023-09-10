from django.contrib.auth.signals import user_logged_in

def user_logged_in_handler(sender, request, user, **kwargs):
    # Your logic to get the user's role ID. This is just a placeholder.
    # Adjust this line depending on how you've structured your models.
    role_id = 1
    request.session['role_id'] = role_id

# Connect the signal
user_logged_in.connect(user_logged_in_handler)
