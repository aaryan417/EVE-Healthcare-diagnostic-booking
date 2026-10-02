from django.contrib.auth import get_user_model
from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.tokens import RefreshToken

User = get_user_model()


class AuthService:
    """
    Service layer handling authentication logic for EVE Healthcare.
    """

    @staticmethod
    def authenticate_user(email: str, password: str) -> dict:
        """
        Authenticate user using email and password.
        Returns access token, refresh token, and user instance.
        Raises AuthenticationFailed (HTTP 401) with a generic error message if invalid or inactive.
        """
        if not email or not password:
            raise AuthenticationFailed("Invalid email or password.")

        normalized_email = User.objects.normalize_email(email).lower()

        try:
            user = User.objects.get(email__iexact=normalized_email)
        except User.DoesNotExist:
            raise AuthenticationFailed("Invalid email or password.")

        if not user.is_active:
            raise AuthenticationFailed("Invalid email or password.")

        if not user.check_password(password):
            raise AuthenticationFailed("Invalid email or password.")

        refresh = RefreshToken.for_user(user)

        return {
            'user': user,
            'access': str(refresh.access_token),
            'refresh': str(refresh),
        }
