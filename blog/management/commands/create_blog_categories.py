from django.core.management.base import BaseCommand
from blog.models import BlogCategory


class Command(BaseCommand):
    help = 'Create initial blog categories for PropertySpotter'

    def handle(self, *args, **options):
        categories = [
            {
                'name': 'Property Investment Tips',
                'description': 'Expert advice on property investment strategies and opportunities'
            },
            {
                'name': 'Market Trends',
                'description': 'Latest trends and insights in the South African property market'
            },
            {
                'name': 'First-Time Buyers',
                'description': 'Guides and tips for first-time property buyers'
            },
            {
                'name': 'Property Spotting',
                'description': 'Tips and tricks for effective property spotting'
            },
            {
                'name': 'Real Estate News',
                'description': 'Latest news and updates from the real estate industry'
            },
            {
                'name': 'Success Stories',
                'description': 'Inspiring success stories from our property spotters and agents'
            },
        ]

        created_count = 0
        for cat_data in categories:
            category, created = BlogCategory.objects.get_or_create(
                name=cat_data['name'],
                defaults={'description': cat_data['description']}
            )
            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'Created category: {category.name}')
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f'Category already exists: {category.name}')
                )

        self.stdout.write(
            self.style.SUCCESS(f'Successfully created {created_count} new categories')
        )