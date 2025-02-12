from .context import current_user


class CurrentUserMiddleware:
    """
    Middleware to capture the logged in user associated with a request and save the user in a context var.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        current_user.set(request.user)
        response = self.get_response(request)
        return response
