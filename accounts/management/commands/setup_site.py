"""
Management command to configure Django Site object.
Run: python manage.py setup_site
"""
from django.core.management.base import BaseCommand
from django.contrib.sites.models import Site
import os
from dotenv import load_dotenv

load_dotenv()


class Command(BaseCommand):
    help = 'Configure Django Site object from environment variables'

    def add_arguments(self, parser):
        parser.add_argument(
            '--domain',
            type=str,
            help='Site domain (overrides SITE_DOMAIN env var)',
        )
        parser.add_argument(
            '--name',
            type=str,
            help='Site name (overrides SITE_NAME env var)',
        )

    def handle(self, *args, **options):
        site_domain = options.get('domain') or os.getenv('SITE_DOMAIN', 'localhost:8000')
        site_name = options.get('name') or os.getenv('SITE_NAME', 'ProudlyZimMart')

        try:
            site = Site.objects.get(id=1)
            site.domain = site_domain
            site.name = site_name
            site.save()
            self.stdout.write(
                self.style.SUCCESS(
                    f'✓ Updated Site object: {site_name} ({site_domain})'
                )
            )
        except Site.DoesNotExist:
            site = Site.objects.create(
                id=1,
                domain=site_domain,
                name=site_name
            )
            self.stdout.write(
                self.style.SUCCESS(
                    f'✓ Created Site object: {site_name} ({site_domain})'
                )
            )

