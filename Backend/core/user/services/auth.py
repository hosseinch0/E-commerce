from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.tokens import RefreshToken


def get_tokens_for_user(user):
    """
    Issue an access/refresh token pair for an active persisted user.
    """
    if user is None or user.pk is None:
        raise AuthenticationFailed("A persisted user is required.")

    if not user.is_active:
        raise AuthenticationFailed("This user account is inactive.")

    refresh = RefreshToken.for_user(user)

    return {
        "refresh": str(refresh),
        "access": str(refresh.access_token),
    }
