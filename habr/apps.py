from django.apps import AppConfig


class HabrConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'habr'

    def ready(self):
        from . import signals

