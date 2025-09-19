from django.apps import AppConfig


class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'core'

    def ready(self) -> None:
        # Import signal handlers to keep media files tidy when models change
        from . import signals  # noqa: F401
