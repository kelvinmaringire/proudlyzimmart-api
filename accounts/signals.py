"""
Signal handlers for accounts app.
Handles email verification status updates and other user-related events.
"""
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from allauth.account.signals import email_confirmed

User = get_user_model()


@receiver(email_confirmed)
def update_user_email_verified(sender, request, email_address, **kwargs):
    """
    Update user's email_verified status when email is confirmed.
    
    Args:
        sender: Signal sender
        request: HTTP request object
        email_address: EmailAddress instance
        **kwargs: Additional keyword arguments
    """
    user = email_address.user
    user.email_verified = True
    user.save(update_fields=['email_verified'])

