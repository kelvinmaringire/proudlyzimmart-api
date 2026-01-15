from django.conf import settings
from django.core.mail import send_mail
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from wagtail.models import Site

from .models import CoreSiteSettings
from .serializers import CoreSiteSettingsSerializer, ContactSubmissionSerializer


class CoreSettingsView(APIView):
    """Return site-wide core settings content."""

    permission_classes = [permissions.AllowAny]

    def get(self, request):
        site = Site.find_for_request(request) or Site.objects.first()
        if not site:
            return Response(
                {"detail": "No Wagtail site is configured."},
                status=status.HTTP_404_NOT_FOUND,
            )
        settings_obj = CoreSiteSettings.for_site(site)
        serializer = CoreSiteSettingsSerializer(settings_obj, context={"request": request})
        return Response(serializer.data, status=status.HTTP_200_OK)


class ContactSubmissionView(APIView):
    """Public contact form endpoint that sends an email."""

    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = ContactSubmissionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        name = serializer.validated_data["name"]
        email = serializer.validated_data["email"]
        subject = serializer.validated_data["subject"]
        message = serializer.validated_data["message"]

        admin_recipients = [admin_email for _, admin_email in getattr(settings, "ADMINS", [])]
        to_emails = admin_recipients or [settings.DEFAULT_FROM_EMAIL]

        email_body = (
            f"New contact submission from {name}.\n\n"
            f"From: {name} <{email}>\n"
            f"Subject: {subject}\n\n"
            f"Message:\n{message}\n"
        )

        send_mail(
            subject=f"Contact Form: {subject}",
            message=email_body,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=to_emails,
            reply_to=[email],
        )

        return Response(
            {"detail": "Contact message sent successfully."},
            status=status.HTTP_200_OK,
        )
