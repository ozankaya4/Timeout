from django.apps import AppConfig


class TimeoutConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'timeout'

    def ready(self):
        import timeout.signals
