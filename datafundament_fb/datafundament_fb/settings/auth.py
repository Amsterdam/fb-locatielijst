from django.http import HttpResponseRedirect
from django.urls import reverse

def oidc_login(request, **kwargs):
    oidc_authentication_init = reverse("oidc_authentication_init")
    redirect = f'{oidc_authentication_init}?next={request.GET.get("next", "")}'
    return HttpResponseRedirect(redirect)

def oidc_logout(request, **kwargs):
    return HttpResponseRedirect(reverse('oidc_logout'))