# Environment Setup Guide

This guide will help you set up the environment variables for the ProudlyZimMart API.

## Quick Start

1. **Copy the example file:**
   ```bash
   cp .env.example .env
   ```

2. **Edit `.env` file** with your actual values (see below)

3. **Generate a secure SECRET_KEY:**
   ```bash
   python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
   ```
   Copy the output and paste it as `SECRET_KEY` in your `.env` file.

## Environment Variables

### Required Variables

#### Django Configuration
```env
SECRET_KEY=your-secret-key-here-change-in-production
DEBUG=True
DJANGO_ENV=development
ALLOWED_HOSTS=localhost,127.0.0.1,0.0.0.0
```

#### Database Configuration
```env
POSTGRES_DB=proudlyzimmart
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_HOST=db
POSTGRES_PORT=5432
```

**Note:** If running locally (not in Docker), change `POSTGRES_HOST` to `localhost`.

### Email Configuration

For development (emails shown in console):
```env
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
```

For production (SMTP):
```env
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
DEFAULT_FROM_EMAIL=your-email@gmail.com
```

**Gmail Setup:**
1. Enable 2-Factor Authentication
2. Go to Google Account Settings > Security > App Passwords
3. Generate an app password for "Mail"
4. Use the generated password (not your regular password)

### Frontend Configuration
```env
FRONTEND_URL=http://localhost:8080
```
Change this to your frontend URL (Quasar app). In production, use your actual domain.

### Social Authentication (Optional)

#### Google OAuth2
```env
GOOGLE_CLIENT_ID=your-google-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-google-client-secret
```

#### Facebook OAuth2
```env
FACEBOOK_CLIENT_ID=your-facebook-app-id
FACEBOOK_CLIENT_SECRET=your-facebook-app-secret
```

### Site Configuration
```env
SITE_DOMAIN=localhost:8000
SITE_NAME=ProudlyZimMart
```

## Setup Steps

### 1. Create .env File

```bash
# Copy example file
cp .env.example .env

# Or create manually
touch .env
```

### 2. Configure Database

If using Docker (recommended):
- Keep `POSTGRES_HOST=db` (Docker service name)
- Values are already set in docker-compose.yml

If running locally:
- Change `POSTGRES_HOST=localhost`
- Ensure PostgreSQL is running
- Create database: `createdb proudlyzimmart`

### 3. Generate SECRET_KEY

```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

### 4. Configure Site Object

After running migrations, configure the Site object:

**Option 1: Django Shell**
```bash
python manage.py shell
```
```python
from django.contrib.sites.models import Site
site = Site.objects.get(id=1)
site.domain = 'localhost:8000'  # or your domain
site.name = 'ProudlyZimMart'
site.save()
```

**Option 2: Django Admin**
1. Run server: `python manage.py runserver`
2. Go to: http://localhost:8000/django-admin/sites/site/1/change/
3. Update domain and name
4. Save

### 5. Run Migrations

```bash
python manage.py migrate
```

## Production Setup

For production, ensure:

1. **SECRET_KEY** is a strong, random value
2. **DEBUG=False** (set in production.py)
3. **ALLOWED_HOSTS** includes your domain
4. **EMAIL_BACKEND** is configured for SMTP
5. **FRONTEND_URL** points to production frontend
6. **Social auth credentials** are production credentials

## Verification

Test your configuration:

```bash
# Check environment variables are loaded
python manage.py shell
>>> import os
>>> from django.conf import settings
>>> print(settings.SECRET_KEY[:10])  # Should show your SECRET_KEY
>>> print(settings.DATABASES['default']['HOST'])  # Should show your DB host
```

## Troubleshooting

### Database Connection Issues
- Check PostgreSQL is running
- Verify credentials in `.env`
- Check `POSTGRES_HOST` matches your setup (db for Docker, localhost for local)

### Email Not Sending
- Check `EMAIL_BACKEND` setting
- Verify SMTP credentials
- For Gmail, use App Password (not regular password)
- Check firewall/network settings

### Site Object Issues
- Ensure Site with id=1 exists
- Run: `python manage.py migrate`
- Check: `python manage.py shell` → `from django.contrib.sites.models import Site; Site.objects.all()`

### Environment Variables Not Loading
- Ensure `.env` file exists in project root
- Check `python-dotenv` is installed
- Verify `load_dotenv()` is called in settings/base.py

