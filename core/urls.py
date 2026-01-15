from django.urls import path

from .views import CoreSettingsView, ContactSubmissionView

app_name = "core"

urlpatterns = [
    path("settings/", CoreSettingsView.as_view(), name="core-settings"),
    path("contact/", ContactSubmissionView.as_view(), name="core-contact"),
]
