import logging

from amsterdam_django_oidc import OIDCAuthenticationBackend as AmsterdamOIDCAuthenticationBackend

LOGGER = logging.getLogger(__name__)


class OIDCAuthenticationBackend(AmsterdamOIDCAuthenticationBackend):
    """Override Amsterdam OIDC authentication."""

    def verify_claims(self, claims):
        """Verify the provided claims to decide if authentication should be allowed."""

        # Verify claims required by default configuration
        scopes = self.get_settings("OIDC_RP_SCOPES", "openid email")
        if "email" in scopes.split():
            return "email" in claims

        return True
