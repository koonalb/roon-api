"""Model definitions for Topics"""
import logging
import uuid
from datetime import datetime

from django.db import models

from api.core.models import CoreModel
from api.core.utils import computed_model_keys

LOGGER = logging.getLogger("roon")


class QuestionTopic(CoreModel):
    """
    Topic of the Question
    """

    # Primary
    topic_id = models.UUIDField("Topic ID", primary_key=True, default=uuid.uuid4, editable=False)

    # Tag data
    title = models.CharField("Topic Title", max_length=256, blank=False, null=False)

    class Meta:
        db_table = "question_topic"
        verbose_name = "Question Topic"
        verbose_name_plural = "Question Topics"

    def __str__(self):
        return f"QuestionTopic: ID: {self.topic_id} and Title: {self.title}"

    def save(self, **kwargs):
        if not self.topic_id:
            self.topic_id = uuid.uuid4()
        self.title = self.cleanse(self.title)

        self.last_modified = datetime.utcnow()
        super().save(**kwargs)
        return self

    @classmethod
    def cleanse(cls, value):
        """
        Helper method that strips whitespace
        unless the provided value is whitespace
        """
        if not value.isspace():
            return value.strip()
        return value

    @classmethod
    def param_transform(cls):
        """
        Either model or serializer computed properties
        """

        return {}

    @classmethod
    def model_keys(cls):
        """
        List of attributes associated with this model class
        """
        exclude = [
            "topic_id",
        ]

        exclude.extend(CoreModel.model_keys())
        return computed_model_keys(cls, field_name_exclusions=exclude, field_type_exclusions=[])
