from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class QuestionsConfig(AppConfig):
    name = "api.questions"
    verbose_name = _("Questions")

    def ready(self):
        try:
            import api.questions.signals  # noqa F401
        except ImportError:
            pass
