"""
Custom adapters for django-allauth.
Handles account and social account creation with custom logic.
"""
from allauth.account.adapter import DefaultAccountAdapter
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from django.conf import settings


class CustomAccountAdapter(DefaultAccountAdapter):
    """Custom account adapter for django-allauth with email verification."""
    
    def save_user(self, request, user, form, commit=True):
        """Save user with email verification enabled by default."""
        user = super().save_user(request, user, form, commit=False)
        user.email_verified = True
        
        if commit:
            user.save()
        return user
    
    def get_email_confirmation_url(self, request, emailconfirmation):
        """Generate custom email confirmation URL pointing to frontend."""
        frontend_url = getattr(settings, 'FRONTEND_URL', 'http://localhost:8080')
        return f"{frontend_url}/verify-email?key={emailconfirmation.key}"


class CustomSocialAccountAdapter(DefaultSocialAccountAdapter):
    """Custom social account adapter for django-allauth with email verification."""
    
    def pre_social_login(self, request, sociallogin):
        """Set email_verified for new social accounts."""
        if sociallogin.is_existing:
            return
        
        if sociallogin.email_addresses:
            sociallogin.user.email_verified = True
    
    def populate_user(self, request, sociallogin, data):
        """Populate user data from social account with email verification."""
        user = super().populate_user(request, sociallogin, data)
        user.email_verified = True
        return user

