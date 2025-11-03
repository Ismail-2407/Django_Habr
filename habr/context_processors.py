from .models import Category


def categories(request):
    """Add categories to all templates"""
    return {'categories': Category.objects.all()}

