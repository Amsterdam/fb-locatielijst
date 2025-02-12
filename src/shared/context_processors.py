from django.conf import settings


def authentication_urls(request):
    return {
        "LOGIN_URL": settings.LOGIN_URL,
        "LOGOUT_URL": settings.LOGOUT_URL,
    }
