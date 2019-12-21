from django.apps import AppConfig


class LocationConfig(AppConfig):
    name = "hikster.location"

    def ready(self):
        import hikster.location.signals  # noqa
