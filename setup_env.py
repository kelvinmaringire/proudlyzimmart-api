#!/usr/bin/env python
"""
Setup script to create .env file from template and configure Site object.
Run this script after cloning the repository.
"""
import os
from pathlib import Path

def create_env_file():
    """Create .env file from template if it doesn't exist."""
    env_file = Path('.env')
    env_example = Path('.env.example')
    
    if env_file.exists():
        print("✓ .env file already exists. Skipping creation.")
        return
    
    # Create .env.example if it doesn't exist
    if not env_example.exists():
        env_template = """# Django Configuration
SECRET_KEY=your-secret-key-here-change-in-production
DEBUG=True
DJANGO_ENV=development
ALLOWED_HOSTS=localhost,127.0.0.1,0.0.0.0

# Database Configuration
POSTGRES_DB=proudlyzimmart
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_HOST=db
POSTGRES_PORT=5432

# Email Configuration
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
DEFAULT_FROM_EMAIL=your-email@gmail.com

# Frontend URL (for email links and CORS)
FRONTEND_URL=http://localhost:8080

# Google OAuth2 (Optional - for social authentication)
GOOGLE_CLIENT_ID=
GOOGLE_CLIENT_SECRET=

# Facebook OAuth2 (Optional - for social authentication)
FACEBOOK_CLIENT_ID=
FACEBOOK_CLIENT_SECRET=

# Site Configuration
SITE_DOMAIN=localhost:8000
SITE_NAME=ProudlyZimMart
"""
        env_example.write_text(env_template)
        print("✓ Created .env.example file")
    
    # Copy .env.example to .env
    env_file.write_text(env_example.read_text())
    print("✓ Created .env file from .env.example")
    print("⚠ Please edit .env file and update the values, especially SECRET_KEY!")


def setup_site():
    """Configure Django Site object."""
    import django
    import sys
    
    # Setup Django
    sys.path.insert(0, str(Path.cwd()))
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'proudlyzimmart.settings.dev')
    django.setup()
    
    from django.contrib.sites.models import Site
    from dotenv import load_dotenv
    
    load_dotenv()
    
    site_domain = os.getenv('SITE_DOMAIN', 'localhost:8000')
    site_name = os.getenv('SITE_NAME', 'ProudlyZimMart')
    
    try:
        site = Site.objects.get(id=1)
        site.domain = site_domain
        site.name = site_name
        site.save()
        print(f"✓ Updated Site object: {site_name} ({site_domain})")
    except Site.DoesNotExist:
        site = Site.objects.create(
            id=1,
            domain=site_domain,
            name=site_name
        )
        print(f"✓ Created Site object: {site_name} ({site_domain})")


if __name__ == '__main__':
    print("Setting up environment...")
    create_env_file()
    print("\nTo configure Site object, run:")
    print("  python manage.py shell")
    print("  from django.contrib.sites.models import Site")
    print("  site = Site.objects.get(id=1)")
    print("  site.domain = 'localhost:8000'")
    print("  site.name = 'ProudlyZimMart'")
    print("  site.save()")
    print("\nOr run migrations first, then use Django admin at /django-admin/sites/site/")

