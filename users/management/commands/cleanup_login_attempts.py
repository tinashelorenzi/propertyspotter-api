from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from users.models import AdminLoginAttempt

class Command(BaseCommand):
    help = 'Clean up old admin login attempts older than 24 hours'

    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            default=1,
            help='Number of days to keep login attempts (default: 1)'
        )

    def handle(self, *args, **options):
        days = options['days']
        cutoff_date = timezone.now() - timedelta(days=days)
        
        # Delete old login attempts
        deleted_count, _ = AdminLoginAttempt.objects.filter(
            attempted_at__lt=cutoff_date
        ).delete()
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully deleted {deleted_count} login attempts older than {days} day(s)'
            )
        ) 