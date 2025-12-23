# Accounts API Documentation

This document provides comprehensive documentation for the authentication API endpoints.

## Base URL

All endpoints are prefixed with `/api/accounts/`

## Authentication

Most endpoints require JWT authentication. Include the access token in the Authorization header:

```
Authorization: Bearer <access_token>
```

---

## Endpoints

### 1. User Registration

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
    "first_name": "",
    "last_name": "",
    "email_verified": false,
    "dob": null,
    "sex": null,
    "physical_address": null,
    "phone_number": null
  },
  "tokens": {
    "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
    "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
  },
  "message": "Registration successful. Please check your email to verify your account."
}
```

**Error Response (400 Bad Request):**
```json
{
  "username": ["A user with that username already exists."],
  "email": ["A user is already registered with this email address."],
  "password2": ["The two password fields didn't match."]
}
```

---

### 2. User Login

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
  "user": {
    "id": 1,
    "username": "johndoe",
    "email": "john.doe@example.com",
    "first_name": "",
    "last_name": "",
    "email_verified": true,
    "dob": null,
    "sex": null,
    "physical_address": null,
    "phone_number": null
  },
  "tokens": {
    "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
    "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
  },
  "message": "Login successful."
}
```

**Error Response (400 Bad Request):**
```json
{
  "non_field_errors": ["Unable to log in with provided credentials."]
}
```

---

### 3. User Logout

**Endpoint:** `POST /api/accounts/logout/`

**Description:** Logout user by blacklisting the refresh token.

**Authentication:** Required

**Request Body:**
```json
{
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

**Response (200 OK):**
```json
{
  "message": "Successfully logged out."
}
```

**Error Response (400 Bad Request):**
```json
{
  "error": "Refresh token is required."
}
```

---

### 4. Change Password

**Endpoint:** `PUT /api/accounts/change-password/`

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

**Error Response (400 Bad Request):**
```json
{
  "old_password": ["Old password is incorrect."],
  "new_password2": ["The two password fields didn't match."]
}
```

---

### 5. Request Password Reset

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

---

### 6. Confirm Password Reset

**Endpoint:** `POST /api/accounts/password-reset-confirm/`

**Description:** Reset password using token from email.

**Authentication:** Not required

**Request Body:**
```json
{
  "uid": "MQ",
  "token": "abc123def456...",
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

**Error Response (400 Bad Request):**
```json
{
  "error": "Invalid or expired token."
}
```

---

### 7. Verify Email

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

**Error Response (400 Bad Request):**
```json
{
  "error": "Invalid or expired verification key."
}
```

---

### 8. Resend Verification Email

**Endpoint:** `POST /api/accounts/resend-verification/`

**Description:** Resend email verification to user.

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
  "message": "Verification email has been sent."
}
```

**Error Response (400 Bad Request):**
```json
{
  "error": "No user found with this email address."
}
```

---

### 9. Get/Update User Profile

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

**PUT Response (200 OK):**
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

---

## Social Authentication

### 10. Google OAuth2 Login

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
  "user": {
    "id": 1,
    "username": "johndoe",
    "email": "john.doe@gmail.com",
    "first_name": "John",
    "last_name": "Doe",
    "email_verified": true,
    "dob": null,
    "sex": null,
    "physical_address": null,
    "phone_number": null
  },
  "tokens": {
    "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
    "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
  }
}
```

---

### 11. Facebook OAuth2 Login

**Endpoint:** `POST /api/accounts/facebook/`

**Description:** Authenticate user with Facebook OAuth2 token. Returns JWT tokens.

**Authentication:** Not required

**Request Body:**
```json
{
  "access_token": "EAABsbCS1iHgBA..."
}
```

**Response (200 OK):**
```json
{
  "user": {
    "id": 1,
    "username": "johndoe",
    "email": "john.doe@facebook.com",
    "first_name": "John",
    "last_name": "Doe",
    "email_verified": true,
    "dob": null,
    "sex": null,
    "physical_address": null,
    "phone_number": null
  },
  "tokens": {
    "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
    "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
  }
}
```

---

## Token Refresh

To refresh an expired access token, use the SimpleJWT token refresh endpoint:

**Endpoint:** `POST /api/token/refresh/`

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

---

## API Key Setup Guide

### Google OAuth2 Setup

1. **Go to Google Cloud Console**
   - Visit: https://console.cloud.google.com/
   - Create a new project or select an existing one

2. **Enable Google+ API**
   - Navigate to "APIs & Services" > "Library"
   - Search for "Google+ API" and enable it

3. **Configure OAuth Consent Screen**
   - Go to "APIs & Services" > "OAuth consent screen"
   - Choose "External" user type
   - Fill in app information (name, support email, etc.)
   - Add scopes: `email`, `profile`
   - Add test users (for development)

4. **Create OAuth Credentials**
   - Go to "APIs & Services" > "Credentials"
   - Click "Create Credentials" > "OAuth client ID"
   - Choose "Web application" for web client
   - Add authorized redirect URIs:
     - `http://localhost:8000/accounts/google/login/callback/` (development)
     - `https://yourdomain.com/accounts/google/login/callback/` (production)
   - Choose "Android" for Android client
   - Add package name and SHA-1 certificate fingerprint

5. **Get Credentials**
   - Copy the Client ID and Client Secret
   - Add to your `.env` file:
     ```
     GOOGLE_CLIENT_ID=your_client_id.apps.googleusercontent.com
     GOOGLE_CLIENT_SECRET=your_client_secret
     ```

### Facebook OAuth2 Setup

1. **Go to Meta for Developers**
   - Visit: https://developers.facebook.com/
   - Click "My Apps" > "Create App"
   - Choose "Consumer" app type

2. **Configure App**
   - Fill in app display name and contact email
   - Add "Facebook Login" product

3. **Configure Facebook Login**
   - Go to "Facebook Login" > "Settings"
   - Add Valid OAuth Redirect URIs:
     - `http://localhost:8000/accounts/facebook/login/callback/` (development)
     - `https://proudlyzimmart.com/accounts/facebook/login/callback/` (production)
   - Save changes

4. **Get App Credentials**
   - Go to "Settings" > "Basic"
   - Copy App ID and App Secret
   - Add to your `.env` file:
     ```
     FACEBOOK_CLIENT_ID=your_app_id
     FACEBOOK_CLIENT_SECRET=your_app_secret
     ```

5. **Configure App Domains**
   - Add your domain to "App Domains"
   - Add platform (Website) with site URL

---

## Environment Variables

Add these to your `.env` file:

```env
# Django Secret Key
SECRET_KEY=your-secret-key-here

# Email Configuration
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
DEFAULT_FROM_EMAIL=your-email@gmail.com

# Frontend URL (for email links)
FRONTEND_URL=http://localhost:8080

# Google OAuth2
GOOGLE_CLIENT_ID=your-google-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-google-client-secret

# Facebook OAuth2
FACEBOOK_CLIENT_ID=your-facebook-app-id
FACEBOOK_CLIENT_SECRET=your-facebook-app-secret
```

---

## Error Codes

- `400 Bad Request`: Invalid request data or validation errors
- `401 Unauthorized`: Missing or invalid authentication token
- `403 Forbidden`: User doesn't have permission to access resource
- `404 Not Found`: Resource not found
- `500 Internal Server Error`: Server error

---

## Notes

1. **JWT Token Lifetime:**
   - Access tokens expire after 60 minutes
   - Refresh tokens expire after 7 days
   - Use refresh token to get new access token

2. **Email Verification:**
   - Email verification is mandatory for regular accounts
   - Social accounts are automatically verified

3. **Password Requirements:**
   - Must meet Django's password validation requirements
   - Minimum length: 8 characters (configurable)
   - Cannot be too similar to user information
   - Cannot be a common password
   - Cannot be entirely numeric

4. **CORS Configuration:**
   - Make sure to configure CORS settings for your frontend domains
   - Add `django-cors-headers` to `INSTALLED_APPS` if needed

5. **Rate Limiting:**
   - Consider implementing rate limiting for authentication endpoints
   - Use `django-ratelimit` or similar package

