from django.apps import AppConfig


class SearchConfig(AppConfig):
    name = 'hikster.search'

    def ready(self):
        from . import signal_handlers
