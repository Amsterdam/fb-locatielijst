from threading import local
from django.contrib.auth.models import User, AnonymousUser

_thread_local = local()

class CurrentUserMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # set request.user, otherwise anonymoususer
        _thread_local.current_user = getattr(request, 'user', AnonymousUser())
        response = self.get_response(request)
        return response

def get_current_user():
    return getattr(_thread_local, 'current_user', AnonymousUser())

def set_current_user(user):
        _thread_local.current_user = user
