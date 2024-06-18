#from contextlib import contextmanager
from contextvars import ContextVar

# ContextVar used in CurrentUserMiddleware to capture and hold the user associated with each request.
# An anonymous user will be the default in case there is no logged in user. 
current_user = ContextVar('current_user', default=None)

# @contextmanager
# def set_current_user(user=None):
#     """Set current_user to a specified user or None for the duration of this context"""
#     token = current_user.set(user)
#     try:
#         yield
#     finally:
#         try:
#             current_user.reset(token)
#         except LookupError:
#             pass

def set_current_user(user=None):
    """Decorator to set current_user to a specified user or None for the duration of this context"""
    def actual_set_user(func):
        def wrapper_set_user(*args, **kwargs):
            token = current_user.set(user)
            func(*args, **kwargs)
            try:
                current_user.reset(token)
            except LookupError:
                pass
        return wrapper_set_user
    return actual_set_user