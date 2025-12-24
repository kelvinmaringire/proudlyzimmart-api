"""
Custom adapters for django-allauth.
Handles account and social account creation with custom logic.
"""
from allauth.account.adapter import DefaultAccountAdapter
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from django.conf import settings
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes


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
        frontend_url = getattr(settings, 'FRONTEND_URL', 'http://localhost:9000')
        return f"{frontend_url}/verify-email?key={emailconfirmation.key}"
    
    def get_password_reset_url(self, request, user):
        """Generate custom password reset URL pointing to frontend."""
        frontend_url = getattr(settings, 'FRONTEND_URL', 'http://localhost:9000')
        token = default_token_generator.make_token(user)
        uidb64 = urlsafe_base64_encode(force_bytes(user.pk))
        return f"{frontend_url}/password/reset/key/{uidb64}-{token}/"
    
    def render_mail(self, template_prefix, email, context, headers=None):
        """Override email rendering to use custom password reset URL."""
        if template_prefix == 'account/email/password_reset_key':
            frontend_url = getattr(settings, 'FRONTEND_URL', 'http://localhost:9000')
            user = context.get('user')
            
            if user:
                uidb64 = urlsafe_base64_encode(force_bytes(user.pk))
                
                if 'key' in context:
                    token = context['key']
                    context['password_reset_url'] = f"{frontend_url}/password/reset/key/{uidb64}-{token}/"
                elif 'uid' in context and 'token' in context:
                    uidb64 = context['uid']
                    token = context['token']
                    context['password_reset_url'] = f"{frontend_url}/password/reset/key/{uidb64}-{token}/"
                elif 'password_reset_url' in context:
                    current_url = context['password_reset_url']
                    if current_url and 'localhost:8002' in current_url or '/accounts/password/reset/' in current_url:
                        if 'key' in context:
                            token = context['key']
                        else:
                            token = default_token_generator.make_token(user)
                        context['password_reset_url'] = f"{frontend_url}/password/reset/key/{uidb64}-{token}/"
        
        return super().render_mail(template_prefix, email, context, headers)


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

