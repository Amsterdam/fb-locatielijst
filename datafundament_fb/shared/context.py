from contextvars import ContextVar
from django.contrib.auth.models import AnonymousUser

# ContextVar used in CurrentUserMiddleware to capture and hold the user associated with each request.
# An anonymous user will be the default in case there is no logged in user. 
current_user = ContextVar('current_user', default=AnonymousUser())