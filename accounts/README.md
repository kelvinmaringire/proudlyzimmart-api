# Accounts App - Authentication System

This app provides a comprehensive REST-based authentication system for Django, supporting both web and mobile clients.

## Features

- ✅ User registration with email verification
- ✅ Login with email or username + password
- ✅ JWT-based authentication
- ✅ Token refresh and blacklisting
- ✅ Password change
- ✅ Password reset (forgot password flow)
- ✅ Social authentication (Google & Facebook)
- ✅ User profile management

## Setup Instructions

### 1. Install Dependencies

Make sure all required packages are installed:

```bash
pip install -r requirements.txt
```

### 2. Database Migrations

Create and apply migrations for the accounts app:

```bash
python manage.py makemigrations accounts
python manage.py migrate
```

### 3. Create Superuser (Optional)

```bash
python manage.py createsuperuser
```

### 4. Environment Variables

Create a `.env` file in the project root with the following variables:

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
FRONTEND_URL=http://localhost:8080

# Google OAuth2 (Optional - for social auth)
GOOGLE_CLIENT_ID=your-google-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-google-client-secret

# Facebook OAuth2 (Optional - for social auth)
FACEBOOK_CLIENT_ID=your-facebook-app-id
FACEBOOK_CLIENT_SECRET=your-facebook-app-secret
```

### 5. Configure Site

Django-allauth requires a Site object. Create it via Django shell:

```bash
python manage.py shell
```

```python
from django.contrib.sites.models import Site
site = Site.objects.get(id=1)
site.domain = 'localhost:8000'  # Change for production
site.name = 'ProudlyZimMart'
site.save()
```

Or create it via admin panel at `/django-admin/sites/site/`

### 6. Run Server

```bash
python manage.py runserver
```

## API Endpoints

See [API_DOCUMENTATION.md](./API_DOCUMENTATION.md) for complete API documentation.

### Quick Reference

- `POST /api/accounts/register/` - Register new user
- `POST /api/accounts/login/` - Login user
- `POST /api/accounts/logout/` - Logout user
- `PUT /api/accounts/change-password/` - Change password
- `POST /api/accounts/password-reset/` - Request password reset
- `POST /api/accounts/password-reset-confirm/` - Confirm password reset
- `POST /api/accounts/verify-email/` - Verify email
- `POST /api/accounts/resend-verification/` - Resend verification email
- `GET /api/accounts/profile/` - Get user profile
- `PUT /api/accounts/profile/` - Update user profile
- `POST /api/accounts/google/` - Google OAuth2 login
- `POST /api/accounts/facebook/` - Facebook OAuth2 login
- `POST /api/token/refresh/` - Refresh access token

## Testing

Test the API using curl, Postman, or your frontend application.

### Example: Register User

```bash
curl -X POST http://localhost:8000/api/accounts/register/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "email": "test@example.com",
    "password1": "SecurePass123!",
    "password2": "SecurePass123!"
  }'
```

### Example: Login

```bash
curl -X POST http://localhost:8000/api/accounts/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "login": "test@example.com",
    "password": "SecurePass123!"
  }'
```

### Example: Get Profile (with token)

```bash
curl -X GET http://localhost:8000/api/accounts/profile/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

## Social Authentication Setup

### Google OAuth2

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a project or select existing
3. Enable Google+ API
4. Configure OAuth consent screen
5. Create OAuth 2.0 credentials
6. Add redirect URIs:
   - `http://localhost:8000/accounts/google/login/callback/` (dev)
   - `https://yourdomain.com/accounts/google/login/callback/` (prod)
7. Add credentials to `.env` file

### Facebook OAuth2

1. Go to [Meta for Developers](https://developers.facebook.com/)
2. Create a new app
3. Add Facebook Login product
4. Configure OAuth redirect URIs:
   - `http://localhost:8000/accounts/facebook/login/callback/` (dev)
   - `https://yourdomain.com/accounts/facebook/login/callback/` (prod)
5. Get App ID and App Secret
6. Add credentials to `.env` file

## Project Structure

```
accounts/
├── __init__.py
├── admin.py          # Admin configuration
├── adapters.py       # Custom allauth adapters
├── apps.py           # App configuration with signals
├── models.py         # CustomUser model
├── serializers.py    # DRF serializers
├── services.py       # Business logic layer
├── signals.py        # Signal handlers
├── urls.py           # URL routing
├── views.py          # API views
├── API_DOCUMENTATION.md  # Complete API docs
└── README.md         # This file
```

## Notes

- Email verification is mandatory for regular accounts
- Social accounts are automatically verified
- JWT tokens expire after 60 minutes (access) and 7 days (refresh)
- Password must meet Django's validation requirements
- All endpoints return JSON responses
- CORS should be configured for frontend domains

## Troubleshooting

### Email Not Sending

- Check `EMAIL_BACKEND` in settings
- For Gmail, use App Password (not regular password)
- Check `EMAIL_HOST`, `EMAIL_PORT`, `EMAIL_USE_TLS` settings
- In development, use `django.core.mail.backends.console.EmailBackend` to see emails in console

### Social Auth Not Working

- Verify OAuth credentials in `.env`
- Check redirect URIs match exactly
- Ensure Site ID is set correctly
- Check that social account providers are enabled in admin

### Token Issues

- Verify `SECRET_KEY` is set correctly
- Check token expiration times
- Ensure token blacklist app is installed and migrated

## Production Considerations

1. Set `DEBUG = False` in production settings
2. Use secure `SECRET_KEY` from environment
3. Configure proper email backend (SMTP)
4. Set `ALLOWED_HOSTS` correctly
5. Use HTTPS for all endpoints
6. Configure CORS properly
7. Set up proper logging
8. Use environment variables for all secrets
9. Configure proper database backups
10. Set up monitoring and error tracking

