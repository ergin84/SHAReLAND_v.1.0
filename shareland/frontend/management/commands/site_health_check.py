from django.core.management.base import BaseCommand
from django.core.mail import mail_admins
from django.db import connections
from django.conf import settings
import shutil

class Command(BaseCommand):
    help = 'Performs a basic site health check and notifies admins if issues are found.'

    def handle(self, *args, **options):
        errors = []

        # Check database connection
        try:
            for conn in connections.all():
                conn.cursor()
        except Exception as e:
            errors.append(f'Database connection failed: {str(e)}')

        # Check disk space (root filesystem)
        try:
            total, used, free = shutil.disk_usage("/")
            # Alert if less than 1GB free
            if free < 1 * 1024 * 1024 * 1024:
                errors.append(f'Low disk space: only {free // (1024*1024)} MB free on root filesystem.')
        except Exception as e:
            errors.append(f'Disk space check failed: {str(e)}')

        if errors:
            subject = 'SHAReLAND Site Health Alert'
            message = '\n'.join(errors)
            mail_admins(subject, message, fail_silently=False)
            self.stdout.write(self.style.ERROR('Health check failed. Admins notified.'))
        else:
            self.stdout.write(self.style.SUCCESS('Health check passed.'))
