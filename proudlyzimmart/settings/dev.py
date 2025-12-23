from .base import *
import os

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.getenv('DEBUG', 'True').lower() == 'true'

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv('SECRET_KEY', 'django-insecure-ngk20(q35(we!3c#)=+4ky=#(6s_la*2&&j3jbflw^cx%*#dg^')

# SECURITY WARNING: define the correct hosts in production!
ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', 'localhost,127.0.0.1,0.0.0.0').split(',')

# Email backend override for development (console backend shows emails in terminal)
EMAIL_BACKEND = os.getenv('EMAIL_BACKEND', 'django.core.mail.backends.console.EmailBackend')


try:
    from .local import *
except ImportError:
    pass
