from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class TopicsConfig(AppConfig):
    name = "api.topics"
    verbose_name = _("Topics")

    def ready(self):
        try:
            import api.topics.signals  # noqa F401
        except ImportError:
            pass
