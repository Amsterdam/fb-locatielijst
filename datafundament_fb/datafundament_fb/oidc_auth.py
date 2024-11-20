from mozilla_django_oidc.auth import OIDCAuthenticationBackend


class OIDCAuthenticationBackend(OIDCAuthenticationBackend):
    def verify_claims(self, claims):
        print('CLAIMS', claims)
        return super(OIDCAuthenticationBackend, self).verify_claims(claims)