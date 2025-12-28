# Accounts App - Authentication System

This app provides a comprehensive REST-based authentication system for Django, supporting both web and mobile clients.

## Table of Contents

- [Features](#features)
- [Overview](#overview)
- [Project Structure](#project-structure)
- [Models](#models)
- [Views](#views)
- [API Endpoints](#api-endpoints)
- [Configuration](#configuration)
- [Social Authentication](#social-authentication)
- [Notes](#notes)

## Features

- ✅ User registration with email verification
- ✅ Login with email or username + password
- ✅ JWT-based authentication
- ✅ Token refresh and blacklisting
- ✅ Password change (authenticated)
- ✅ Password reset (forgot password flow)
- ✅ Social authentication (Google & Facebook)
- ✅ User profile management
- ✅ Email verification

## Overview

The accounts app implements a complete authentication system using:
- **Django REST Framework** - REST API framework
- **django-allauth** - Authentication and social account management
- **Simple JWT** - JWT token generation and validation
- **dj-rest-auth** - REST API support for allauth

### Key Components

- **CustomUser Model** - Extended AbstractUser with email verification and additional fields
- **Custom Adapters** - Custom allauth adapters for email verification URLs and social account handling
- **API Views** - REST API endpoints for all authentication operations
- **Serializers** - Request/response validation and serialization
- **Services** - Business logic layer for token generation and email sending

## Project Structure

```
accounts/
├── __init__.py
├── admin.py          # CustomUser admin configuration
├── adapters.py       # Custom allauth adapters
├── apps.py           # App configuration with signals
├── models.py         # CustomUser model
├── serializers.py    # DRF serializers
├── services.py       # Business logic layer
├── signals.py        # Signal handlers
├── urls.py           # URL routing
├── views.py          # API views
├── README.md         # This file
└── USAGE.md          # Setup and usage guide
```

## Models

### CustomUser

Extended Django AbstractUser with additional fields:

- `email_verified` (BooleanField) - Email verification status
- `dob` (DateField, optional) - Date of birth
- `sex` (CharField, optional) - Gender
- `physical_address` (TextField, optional) - Physical address
- `phone_number` (CharField, optional) - Phone number

**Key Features:**
- Email verification is mandatory for regular accounts
- Social accounts are automatically verified
- Username and email are both supported for login

## Views

### Authentication Views

- `RegisterView` - User registration
- `LoginView` - User login (email/username + password)
- `LogoutView` - User logout with token blacklisting

### Email Verification Views

- `VerifyEmailView` - Verify email with confirmation key
- `ResendVerificationEmailView` - Resend verification email

### Password Management Views

- `ChangePasswordView` - Change password (authenticated)
- `PasswordResetView` - Request password reset email
- `PasswordResetConfirmView` - Confirm password reset with token
- `PasswordResetTokenValidateView` - Validate password reset token

### Profile Views

- `UserProfileView` - Get and update user profile

### Social Authentication Views

- `GoogleLoginView` - Google OAuth2 login
- `FacebookLoginView` - Facebook OAuth2 login

## API Endpoints

All endpoints are prefixed with `/api/accounts/`

### Authentication

#### 1. User Registration

**Endpoint:** `POST /api/accounts/register/`

**Description:** Register a new user account. Email verification will be sent automatically.

**Authentication:** Not required

**Request Body:**
```json
{
  "username": "johndoe",
  "email": "john.doe@example.com",
  "password1": "SecurePassword123!",
  "password2": "SecurePassword123!"
}
```

**Response (201 Created):**
```json
{
  "user": {
    "id": 1,
    "username": "johndoe",
    "email": "john.doe@example.com",
    "email_verified": false,
    ...
  },
  "access_token": "...",
  "refresh_token": "...",
  "message": "Registration successful."
}
```

#### 2. User Login

**Endpoint:** `POST /api/accounts/login/`

**Description:** Authenticate user with email or username and password. Returns JWT tokens.

**Authentication:** Not required

**Request Body:**
```json
{
  "login": "john.doe@example.com",
  "password": "SecurePassword123!"
}
```

**OR**

```json
{
  "login": "johndoe",
  "password": "SecurePassword123!"
}
```

**Response (200 OK):**
```json
{
  "user": {...},
  "access_token": "...",
  "refresh_token": "...",
  "message": "Login successful."
}
```

#### 3. User Logout

**Endpoint:** `POST /api/accounts/logout/`

**Description:** Logout user by blacklisting the refresh token.

**Authentication:** Required

**Request Body:**
```json
{
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

**Note:** Also accepts `refresh` or `refreshToken` as field names.

**Response (200 OK):**
```json
{
  "message": "Successfully logged out."
}
```

### Email Verification

#### 4. Verify Email

**Endpoint:** `POST /api/accounts/verify-email/`

**Description:** Verify user email using confirmation key from email.

**Authentication:** Not required

**Request Body:**
```json
{
  "key": "abc123def456..."
}
```

**Response (200 OK):**
```json
{
  "message": "Email verified successfully."
}
```

#### 5. Resend Verification Email

**Endpoint:** `POST /api/accounts/resend-verification/`

**Description:** Resend email verification to user.

**Authentication:** Not required

**Request Body:**
```json
{
  "email": "john.doe@example.com"
}
```

### Password Management

#### 6. Change Password

**Endpoint:** `PUT /api/accounts/change-password/` or `PATCH /api/accounts/change-password/`

**Description:** Change authenticated user's password. Requires old password verification.

**Authentication:** Required

**Request Body:**
```json
{
  "old_password": "OldPassword123!",
  "new_password1": "NewSecurePassword123!",
  "new_password2": "NewSecurePassword123!"
}
```

**Response (200 OK):**
```json
{
  "message": "Password changed successfully."
}
```

#### 7. Request Password Reset

**Endpoint:** `POST /api/accounts/password-reset/`

**Description:** Request password reset email. Email will be sent with reset link.

**Authentication:** Not required

**Request Body:**
```json
{
  "email": "john.doe@example.com"
}
```

**Response (200 OK):**
```json
{
  "message": "Password reset email has been sent."
}
```

**Note:** For security, the same message is returned even if the email doesn't exist.

#### 8. Validate Password Reset Token

**Endpoint:** `GET /api/accounts/password-reset/validate/<uidb64>-<token>/`

**Description:** Validate if a password reset token is valid without resetting the password. Useful for frontend to check token validity before showing reset form.

**Authentication:** Not required

**Response (200 OK):**
```json
{
  "valid": true,
  "message": "Token is valid."
}
```

**Response (400 Bad Request):**
```json
{
  "valid": false,
  "error": "Invalid or expired token."
}
```

#### 9. Confirm Password Reset

**Endpoint:** `POST /api/accounts/password-reset-confirm/<uidb64>-<token>/`  
**Endpoint:** `POST /api/accounts/password-reset-confirm/`

**Description:** Reset password using token from email. Supports multiple formats:

1. **Token in URL path (Recommended):**
   ```
   POST /api/accounts/password-reset-confirm/1-d1b4o1-9e4d96fb02b86b5edb66171e08d58dc4/
   ```

2. **Token in request body:**
   ```
   POST /api/accounts/password-reset-confirm/
   Body: { "token_key": "uidb64-token", "new_password1": "...", "new_password2": "..." }
   ```

3. **Separate uid and token (Legacy):**
   ```
   POST /api/accounts/password-reset-confirm/
   Body: { "uid": "...", "token": "...", "new_password1": "...", "new_password2": "..." }
   ```

**Request Body:**
```json
{
  "new_password1": "NewSecurePassword123!",
  "new_password2": "NewSecurePassword123!"
}
```

**Response (200 OK):**
```json
{
  "message": "Password has been reset successfully."
}
```

### User Profile

#### 10. Get/Update User Profile

**Endpoint:** `GET /api/accounts/profile/`  
**Endpoint:** `PUT /api/accounts/profile/`

**Description:** Retrieve or update authenticated user's profile.

**Authentication:** Required

**GET Response (200 OK):**
```json
{
  "id": 1,
  "username": "johndoe",
  "email": "john.doe@example.com",
  "first_name": "John",
  "last_name": "Doe",
  "email_verified": true,
  "dob": "1990-01-01",
  "sex": "M",
  "physical_address": "123 Main St",
  "phone_number": "+1234567890"
}
```

**PUT Request Body:**
```json
{
  "first_name": "John",
  "last_name": "Doe",
  "dob": "1990-01-01",
  "sex": "M",
  "physical_address": "123 Main St",
  "phone_number": "+1234567890"
}
```

### Social Authentication

#### 11. Google OAuth2 Login

**Endpoint:** `POST /api/accounts/google/`

**Description:** Authenticate user with Google OAuth2 token. Returns JWT tokens.

**Authentication:** Not required

**Request Body:**
```json
{
  "access_token": "ya29.a0AfH6SMB..."
}
```

**Response (200 OK):**
```json
{
  "user": {...},
  "access_token": "...",
  "refresh_token": "..."
}
```

#### 12. Facebook OAuth2 Login

**Endpoint:** `POST /api/accounts/facebook/`

**Description:** Authenticate user with Facebook OAuth2 token. Returns JWT tokens.

**Authentication:** Not required

**Request Body:**
```json
{
  "access_token": "EAABsbCS1iHgBA..."
}
```

### Token Refresh

**Endpoint:** `POST /api/token/refresh/`

**Description:** Refresh an expired access token.

**Request Body:**
```json
{
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

**Response (200 OK):**
```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

## Configuration

### Environment Variables

Required environment variables (add to `.env` file):

```env
# Django Secret Key
SECRET_KEY=your-secret-key-here

# Database (if not using docker-compose)
POSTGRES_DB=proudlyzimmart
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_HOST=db
POSTGRES_PORT=5432

# Email Configuration
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
DEFAULT_FROM_EMAIL=your-email@gmail.com

# Frontend URL (for email links)
FRONTEND_URL=http://localhost:9000

# Google OAuth2 (Optional - for social auth)
GOOGLE_CLIENT_ID=your-google-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-google-client-secret

# Facebook OAuth2 (Optional - for social auth)
FACEBOOK_CLIENT_ID=your-facebook-app-id
FACEBOOK_CLIENT_SECRET=your-facebook-app-secret
```

### Django Settings

Key settings required:

- `AUTH_USER_MODEL = 'accounts.CustomUser'`
- `ACCOUNT_ADAPTER = 'accounts.adapters.CustomAccountAdapter'`
- `SOCIALACCOUNT_ADAPTER = 'accounts.adapters.CustomSocialAccountAdapter'`
- JWT authentication configured in REST_FRAMEWORK settings
- Token blacklist enabled

### Site Configuration

Django-allauth requires a Site object. Create it via Django shell:

```python
from django.contrib.sites.models import Site
site = Site.objects.get(id=1)
site.domain = 'localhost:8000'  # Change for production
site.name = 'ProudlyZimMart'
site.save()
```

Or create it via admin panel at `/django-admin/sites/site/`

## Social Authentication

### Google OAuth2 Setup

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a project or select existing
3. Enable Google+ API
4. Configure OAuth consent screen
5. Create OAuth 2.0 credentials
6. Add redirect URIs:
   - `http://localhost:8000/accounts/google/login/callback/` (dev)
   - `https://yourdomain.com/accounts/google/login/callback/` (prod)
7. Add credentials to `.env` file

### Facebook OAuth2 Setup

1. Go to [Meta for Developers](https://developers.facebook.com/)
2. Create a new app
3. Add Facebook Login product
4. Configure OAuth redirect URIs:
   - `http://localhost:8000/accounts/facebook/login/callback/` (dev)
   - `https://yourdomain.com/accounts/facebook/login/callback/` (prod)
5. Get App ID and App Secret
6. Add credentials to `.env` file

## Notes

### JWT Token Lifetime

- Access tokens expire after 60 minutes
- Refresh tokens expire after 7 days
- Use refresh token to get new access token

### Email Verification

- Email verification is mandatory for regular accounts
- Social accounts are automatically verified
- Verification emails contain links pointing to frontend

### Password Requirements

- Must meet Django's password validation requirements
- Minimum length: 8 characters (configurable)
- Cannot be too similar to user information
- Cannot be a common password
- Cannot be entirely numeric

### Password Reset Flow

- Password reset tokens expire after use (one-time use)
- Tokens also expire after 3 days (Django default)
- Email links point to frontend: `{FRONTEND_URL}/password/reset/key/{uidb64}-{token}/`
- Token format: `{uidb64}-{token}` (token can contain dashes)

### Error Codes

- `400 Bad Request`: Invalid request data or validation errors
- `401 Unauthorized`: Missing or invalid authentication token
- `403 Forbidden`: User doesn't have permission to access resource
- `404 Not Found`: Resource not found
- `500 Internal Server Error`: Server error

### CORS Configuration

- Make sure to configure CORS settings for your frontend domains
- Add `django-cors-headers` to `INSTALLED_APPS` if needed

### Rate Limiting

- Consider implementing rate limiting for authentication endpoints
- Use `django-ratelimit` or similar package

---

For setup instructions, testing examples, and frontend integration guides, see [USAGE.md](./USAGE.md).
