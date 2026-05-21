from django.conf import settings


def authentication_urls(request):
    return {
        "LOGIN_URL": settings.LOGIN_URL,
        "LOGOUT_URL": settings.LOGOUT_URL,
    }


def request_change_form_url(request):
    return {
        "REQUEST_CHANGE_FORM_URL": settings.REQUEST_CHANGE_FORM_URL,
    }
