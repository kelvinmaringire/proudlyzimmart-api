# Core Headless API

This document describes the headless endpoints exposed by the `core` app and
the data they return for frontend consumption.

Base path:
- `/api/core/`

## GET /api/core/settings/

Returns the site-wide settings content managed in Wagtail Settings.

Response shape (200):

```json
{
  "privacy_policy": "<p>...</p>",
  "terms_and_conditions": "<p>...</p>",
  "return_refund_policy": "<p>...</p>",
  "faqs": "<p>...</p>",
  "about_us": "<p>...</p>",
  "announcement_enabled": false,
  "announcement_bar_text": "<p>...</p>",
  "contact_email": "support@example.com",
  "contact_phone": "+263-...",
  "contact_address": "<p>...</p>",
  "facebook_url": "https://facebook.com/...",
  "instagram_url": "https://instagram.com/...",
  "x_url": "https://x.com/...",
  "linkedin_url": "https://linkedin.com/...",
  "tiktok_url": "https://tiktok.com/@...",
  "youtube_url": "https://youtube.com/@...",
  "whatsapp_url": "https://wa.me/..."
}
```

Notes:
- Rich text fields are returned as HTML (expanded from Wagtail rich text).
- Social URLs can be empty strings when not configured.

## POST /api/core/contact/

Public contact form endpoint. Sends an email; no authentication required.

Request body:

```json
{
  "name": "Jane Doe",
  "email": "jane@example.com",
  "subject": "Order question",
  "message": "Hello, I need help with..."
}
```

Response (200):

```json
{
  "detail": "Contact message sent successfully."
}
```

Error responses:
- 400: Validation errors for missing or invalid fields.
