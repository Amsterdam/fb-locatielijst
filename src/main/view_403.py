from django.core.exceptions import PermissionDenied


def permissiondenied403(request):
    raise PermissionDenied