"""
Service layer for authentication business logic.
Handles token generation, email sending, and other authentication-related operations.
"""
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model
from allauth.account.utils import send_email_confirmation
from allauth.account.forms import ResetPasswordForm
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes

User = get_user_model()


def get_tokens_for_user(user):
    """
    Generate JWT access and refresh tokens for a user.
    
    Args:
        user: User instance
        
    Returns:
        dict: Contains 'access' and 'refresh' tokens
    """
    refresh = RefreshToken.for_user(user)
    return {
        'access': str(refresh.access_token),
        'refresh': str(refresh),
    }


def send_verification_email(request, user):
    """
    Send email verification to user.
    
    Args:
        request: HTTP request object
        user: User instance
    """
    send_email_confirmation(request, user)


def send_password_reset_email(request, user):
    """
    Send password reset email to user.
    
    Args:
        request: HTTP request object
        user: User instance
    """
    form = ResetPasswordForm({'email': user.email})
    if form.is_valid():
        form.save(request)


def get_password_reset_url(user, request):
    """
    Generate password reset URL with token.
    
    Args:
        user: User instance
        request: HTTP request object
        
    Returns:
        str: Password reset URL
    """
    token = default_token_generator.make_token(user)
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    
    # Get frontend URL from settings or request
    frontend_url = getattr(request, 'frontend_url', None) or \
                   getattr(request, 'META', {}).get('HTTP_ORIGIN', '')
    
    reset_url = f"{frontend_url}/reset-password/{uid}/{token}/"
    return reset_url

