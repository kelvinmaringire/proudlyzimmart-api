"""
Service layer for authentication business logic.
Handles token generation, email sending, and other authentication-related operations.
"""
from rest_framework_simplejwt.tokens import RefreshToken
from allauth.account.utils import send_email_confirmation
from allauth.account.forms import ResetPasswordForm


def get_tokens_for_user(user):
    """Generate JWT access and refresh tokens for a user."""
    refresh = RefreshToken.for_user(user)
    return {
        'access': str(refresh.access_token),
        'refresh': str(refresh),
    }


def send_verification_email(request, user):
    """Send email verification to user."""
    send_email_confirmation(request, user)


def send_password_reset_email(request, user):
    """Send password reset email to user."""
    form = ResetPasswordForm({'email': user.email})
    if form.is_valid():
        form.save(request)

