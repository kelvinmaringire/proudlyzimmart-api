"""
Custom adapters for django-allauth.
Handles account and social account creation with custom logic.
"""
from allauth.account.adapter import DefaultAccountAdapter
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from django.conf import settings
from django.contrib.auth import get_user_model

User = get_user_model()


class CustomAccountAdapter(DefaultAccountAdapter):
    """
    Custom account adapter for django-allauth.
    Handles user account creation and email verification.
    """
    
    def save_user(self, request, user, form, commit=True):
        """
        Save user with custom logic.
        """
        user = super().save_user(request, user, form, commit=False)
        
        # Set email_verified to True by default (no verification required)
        user.email_verified = True
        
        if commit:
            user.save()
        return user
    
    def get_email_confirmation_url(self, request, emailconfirmation):
        """
        Generate custom email confirmation URL.
        This should point to your frontend verification endpoint.
        """
        frontend_url = getattr(settings, 'FRONTEND_URL', 'http://localhost:8080')
        return f"{frontend_url}/verify-email?key={emailconfirmation.key}"
    
    def send_mail(self, template_prefix, email, context):
        """
        Override send_mail to customize email sending.
        """
        # You can customize email templates here
        return super().send_mail(template_prefix, email, context)


class CustomSocialAccountAdapter(DefaultSocialAccountAdapter):
    """
    Custom social account adapter for django-allauth.
    Handles social account creation and linking.
    """
    
    def pre_social_login(self, request, sociallogin):
        """
        Handle pre-social login logic.
        """
        # Auto-verify email for social accounts
        if sociallogin.is_existing:
            return
        
        # Set email_verified to True for social accounts
        if sociallogin.email_addresses:
            user = sociallogin.user
            user.email_verified = True
    
    def populate_user(self, request, sociallogin, data):
        """
        Populate user data from social account.
        """
        user = super().populate_user(request, sociallogin, data)
        
        # Set email_verified to True for social accounts
        user.email_verified = True
        
        return user

