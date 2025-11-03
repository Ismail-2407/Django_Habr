from django.core.management.base import BaseCommand
from django.utils.text import slugify
from habr.models import Category


class Command(BaseCommand):
    help = 'Create predefined categories'

    def handle(self, *args, **options):
        categories = [
            'Backend',
            'Frontend',
            'AI',
            'Cyber Security',
            'Cyber Sport',
            'Game Development',
        ]
        
        created_count = 0
        for name in categories:
            slug = slugify(name)
            category, created = Category.objects.get_or_create(
                name=name,
                defaults={'slug': slug}
            )
            if created:
                created_count += 1
                self.stdout.write(self.style.SUCCESS(f'Created category: {name}'))
            else:
                self.stdout.write(self.style.WARNING(f'Category already exists: {name}'))
        
        self.stdout.write(self.style.SUCCESS(f'Successfully created {created_count} categories.'))

