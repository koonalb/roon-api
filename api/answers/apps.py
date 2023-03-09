from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class AnswersConfig(AppConfig):
    name = "api.answers"
    verbose_name = _("Answers")

    def ready(self):
        try:
            import api.answers.signals  # noqa F401
        except ImportError:
            pass
