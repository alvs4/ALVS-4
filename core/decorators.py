from django.contrib.auth.decorators import user_passes_test

def role_required(*allowed_roles):
    return user_passes_test(
        lambda u: u.is_authenticated and u.tipo in allowed_roles,
        login_url='login',
    )