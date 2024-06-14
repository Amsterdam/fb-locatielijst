from contextvars import ContextVar
from django.contrib.auth.models import AnonymousUser

current_user = ContextVar('current_user', default=AnonymousUser())